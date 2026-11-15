"""Opt-in source checks. Availability failures never use synthetic data."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.config import ROOT
from backend.db import Store
from backend.domain import market_summary
from backend.evidence import ISSUER_DOCUMENTS
from backend.providers import Providers, SourceError


async def main():
    store = Store(ROOT / "artifacts" / "provider-probe.db")
    store.init()
    providers, results = Providers(store), {}
    async def probe(label, action):
        try:
            results[label] = {"status":"ok", **await asyncio.wait_for(action(), 65)}
        except (SourceError, asyncio.TimeoutError, ValueError) as exc:
            results[label] = {"status":"unavailable", "detail":str(exc) or "timeout"}
    async def market():
        data = await providers.market("TCS")
        summary = market_summary(data["bars"])
        return {"symbol":"TCS", "date":summary["date"], "sessions":len(data["bars"])}
    async def filings():
        data = await providers.announcements({"TCS", "INFY", "ASIANPAINT"})
        return {"count":len(data), "all_primary":all(x["source"]=="NSE corporate disclosure" for x in data)}
    async def discovery():
        data = await providers.discover("HCLTECH")
        return {"symbol":"HCLTECH", "documents":len(data["documents"]), "kinds":sorted({x["kind"] for x in data["documents"]})}
    async def document(kind):
        doc = next(d for d in ISSUER_DOCUMENTS["ASIANPAINT"] if d["kind"] == kind)
        data = await providers.document(doc)
        return {"kind":kind, "readable_pages":len(data["pages"]), "sha256":data["sha256"]}
    try:
        await asyncio.gather(probe("market",market), probe("exchange_filings",filings),
                             probe("unseen_ticker_discovery",discovery),
                             probe("annual_report",lambda:document("annual_report")),
                             probe("call_transcript",lambda:document("transcript")))
    finally:
        await providers.close()
    print(json.dumps(results,indent=2))
    (ROOT / "artifacts" / "live-probe.json").write_text(json.dumps(results,indent=2),encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
