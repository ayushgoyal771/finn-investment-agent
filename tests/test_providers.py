import hashlib
import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from backend.config import IST
from backend.db import Store
from backend.providers import Providers, SourceError, extract_pages, public_url


@pytest.fixture
def store(tmp_path):
    db = Store(tmp_path/"sources.db")
    db.init()
    return db


@pytest.fixture(autouse=True)
def no_network_dns(monkeypatch):
    async def check(url):
        pass
    monkeypatch.setattr("backend.providers.check_dns",check)


@pytest.mark.parametrize("url", [None, {"bad":"url"}, "https://www.bseindia.com:bad/x", "http://www.bseindia.com/report.pdf","https://localhost/report.pdf", "https://www.bseindia.com@127.0.0.1/x", "https://www.bseindia.com:8443/x", "https://evil.example/x"])
def test_source_url_gate_rejects_unapproved_destinations(url):
    with pytest.raises(SourceError):
        public_url(url,{"www.bseindia.com"})


async def test_redirect_is_revalidated_before_fetch(store):
    calls=[]
    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(302,headers={"location":"https://127.0.0.1/private"})
    p=Providers(store,httpx.MockTransport(handler))
    try:
        with pytest.raises(SourceError):
            await p.fetch("https://www.bseindia.com/report.pdf",{"www.bseindia.com"})
        assert len(calls)==1
    finally:
        await p.close()


async def test_size_limit_and_access_denial_are_explicit(store):
    p=Providers(store,httpx.MockTransport(lambda r:httpx.Response(200,content=b'x'*1024)))
    try:
        with pytest.raises(SourceError,match="limit"):
            await p.fetch("https://www.bseindia.com/report.pdf",{"www.bseindia.com"},limit=100)
    finally:
        await p.close()
    p=Providers(store,httpx.MockTransport(lambda r:httpx.Response(403)))
    try:
        with pytest.raises(SourceError,match="403"):
            await p.fetch("https://www.bseindia.com/report.pdf",{"www.bseindia.com"})
    finally:
        await p.close()


async def test_market_excludes_current_unfinished_session(store,monkeypatch):
    now=datetime(2026,11,16,12,tzinfo=IST)
    monkeypatch.setattr("backend.providers.utcnow",lambda:now)
    stamps=[int((now-timedelta(days=24-i)).timestamp()) for i in range(25)]
    payload={"chart":{"result":[{"meta":{"longName":"Unseen Company"},"timestamp":stamps,
                "indicators":{"quote":[{"close":[100]*25,"volume":[1000]*25}]}}]}}
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(200,json=payload)
    p=Providers(store,httpx.MockTransport(handler))
    try:
        result=await p.market("UNSEENCO")
        assert len(result["bars"])==24 and result["symbol"]=="UNSEENCO"
        assert result["bars"][-1]["date"]=="2026-11-15"
        assert (await p.market("UNSEENCO"))["cached"] and len(calls)==1
    finally:
        await p.close()


async def test_exchange_filters_portfolio_preserves_date_and_deduplicates(store):
    rows=[{"symbol":"TCS","desc":"Financial results","an_dt":"13-Nov-2026 16:31:00","attchmntText":"Consolidated quarterly financial results","attchmntFile":"https://nsearchives.nseindia.com/corporate/a.pdf"},
          {"symbol":"OTHER","desc":"Financial results","an_dt":"13-Nov-2026 17:00:00"},
          {"symbol":"TCS","desc":"Unknown date","an_dt":"unrecognised"}]
    p=Providers(store,httpx.MockTransport(lambda r:httpx.Response(200,json=rows)))
    try:
        result=await p.announcements({"TCS"})
        assert len(result)==1 and result[0]["category"]=="results"
        assert result[0]["published_at"]=="2026-11-13T11:01:00+00:00"
        store.add_filings(result+result)
        assert len(store.filings())==1
    finally:
        await p.close()


async def test_discovery_for_unseen_ticker_does_not_ingest_secondary_analysis(store):
    html='''<h1>Unseen Company</h1><p>Broker says BUY with 200% upside</p>
    <div><h3>Annual reports</h3><ul><li><a href="https://www.bseindia.com/annual.pdf">Annual Report 2026</a></li></ul></div>
    <div><h3>Concalls</h3><ul><li>Oct 2026 <a href="https://www.bseindia.com/call.pdf">Transcript</a><a href="https://broker.example/research.pdf">PPT</a></li></ul></div>'''
    p=Providers(store,httpx.MockTransport(lambda r:httpx.Response(200,text=html)))
    try:
        result=await p.discover("UNSEENCO")
        assert len(result["documents"])==2
        assert {d["kind"] for d in result["documents"]}=={"annual_report","transcript"}
        assert "Broker" not in json.dumps(result)
    finally:
        await p.close()


def test_unreadable_pdf_does_not_produce_text():
    with pytest.raises(SourceError):
        extract_pages(b"Not a PDF")


def test_cache_ttl_expiration(store,monkeypatch):
    store.cache("x",{"data":1})
    assert store.cached("x",10)=={"data":1}
    with store.connection() as db:
        db.execute("UPDATE cache SET at=at-20")
    assert store.cached("x",10) is None
