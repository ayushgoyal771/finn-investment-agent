from datetime import timedelta

from fastapi.testclient import TestClient

from backend.config import Config
from backend.domain import utcnow
from backend.main import create_app
from tests.conftest import OfflineProviders


def test_app_serves_page_and_demo_end_to_end(client):
    response = client.get("/")
    assert response.status_code == 200 and "investment fieldnotes" in response.text
    assert client.get("/assets/app.js").status_code == 200
    data = client.get("/api/brief").json()
    assert len(data["market"]) == data["stats"]["companies"] == 18
    assert data["priority"] and data["routine"]
    lead = data["priority"][0]
    assert lead["category"] == "management_change" and lead["network"][0]["path"]
    assert all(item["demo"] for item in data["priority"])
    assert not data["warnings"]


def test_window_expands_and_all_announcements_survive(client):
    daily = client.get("/api/brief?hours=24").json()
    weekly = client.get("/api/brief?hours=168").json()
    assert weekly["stats"]["filings"] > daily["stats"]["filings"]
    assert daily["stats"]["filings"] == len(daily["priority"]) + len(daily["routine"]) - sum(i["category"]=="market" for i in daily["priority"])


def test_saved_seen_and_threshold_preferences_are_durable(client):
    item = client.get("/api/brief").json()["priority"][0]
    assert client.patch(f'/api/items/{item["id"]}',json={"saved":True,"seen":True}).status_code == 200
    saved = client.get("/api/brief?saved=true").json()
    assert len(saved["priority"]) == 1 and saved["priority"][0]["seen"]
    assert client.put("/api/settings", json={"price_threshold":15,"volume_threshold":6,"categories":[]}).status_code == 200
    updated = client.get("/api/brief").json()
    assert not any(e["category"] == "market" for e in updated["priority"])
    assert not any(e["alert"] for e in updated["priority"])
    assert client.get("/api/settings").json()["preferences"]["price_threshold"] == 15


def test_live_outages_do_not_fall_back_to_synthetic_data(client):
    data = client.get("/api/brief?mode=live").json()
    assert data["warnings"] and not data["priority"] and not data["routine"]
    assert all(m.get("error") and not m["demo"] for m in data["market"])


def test_research_all_three_packs_have_primary_citations_and_network(client):
    for symbol in ("TCS","INFY","ASIANPAINT"):
        response = client.post("/api/research",json={"symbol":symbol,"question":"What should I understand before investing?"})
        assert response.status_code == 200
        result = response.json()
        assert result["facts"] and result["metrics"] and result["network"]
        assert all(f["kind"] in ("annual_report","transcript") and f["url"].startswith("https://") for f in result["facts"])
        assert result["mode"] == "demo" and "FY2025" in result["period"]


def test_unknown_demo_ticker_and_unavailable_live_research_are_explicit(client):
    response = client.post("/api/research",json={"symbol":"UNSEENCO"})
    assert response.status_code == 503 and "Live sources" in response.json()["detail"]
    response = client.post("/api/research",json={"symbol":"UNSEENCO","mode":"live"})
    assert response.status_code == 503 and "No company facts" in response.json()["detail"]


def test_settings_and_queries_are_validated(client):
    assert client.put("/api/settings",json={"price_threshold":-1}).status_code == 422
    assert client.get("/api/brief?mode=unknown").status_code == 422
    assert client.get("/api/brief?hours=0").status_code == 422
    assert client.post("/api/research",json={"symbol":"../TCS"}).status_code == 422
    assert client.get("/api/network?symbol=https://127.0.0.1").status_code == 422


def test_contact_dates_export_and_invalid_dates(client):
    assert client.get("/api/network?q=semiconductors").json()["matches"][0]["id"] == "sana"
    today = utcnow().date().isoformat()
    assert client.post("/api/network/sana/contacted",json={"last_contact":today}).status_code == 200
    exported = client.get("/api/network/export")
    assert exported.json()["synthetic"]
    assert next(c for c in exported.json()["contacts"] if c["id"]=="sana")["last_contact"] == today
    future = (utcnow().date()+timedelta(days=30)).isoformat()
    assert client.post("/api/network/sana/contacted",json={"last_contact":future}).status_code == 422
    assert client.post("/api/network/no-one/contacted",json={"last_contact":today}).status_code == 404


def test_security_headers_and_cross_origin_writes(client):
    response = client.get("/")
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert client.get("/api/network").headers["cache-control"] == "no-store"
    assert client.put("/api/settings",json={},headers={"Origin":"https://attacker.example"}).status_code == 403
    assert client.get("/api/brief",headers={"Host":"attacker.example"}).status_code == 400


def test_token_required_when_configured(tmp_path):
    with TestClient(create_app(Config(db_path=tmp_path/"auth.db",access_token="a-test-token"),OfflineProviders)) as c:
        assert c.get("/api/health").status_code == 200
        assert c.get("/api/network").status_code == 401
        assert c.get("/api/network",headers={"Authorization":"Bearer wrong"}).status_code == 401
        assert c.get("/api/network",headers={"Authorization":"Bearer a-test-token"}).status_code == 200


def test_research_rate_limit(client):
    for _ in range(8):
        assert client.post("/api/research",json={"symbol":"TCS"}).status_code == 200
    assert client.post("/api/research",json={"symbol":"TCS"}).status_code == 429


def test_saved_market_signal_survives_next_session_and_threshold_change(client,monkeypatch):
    from backend.seed import demo_bars
    from datetime import date
    first = client.get("/api/brief").json()
    item = next(e for e in first["priority"] if e["category"]=="market")
    client.patch(f'/api/items/{item["id"]}',json={"saved":True})
    def next_day(index):
        bars = demo_bars(index)
        for bar in bars:
            bar["date"] = (date.fromisoformat(bar["date"])+timedelta(days=1)).isoformat()
        return bars
    monkeypatch.setattr("backend.service.demo_bars",next_day)
    client.put("/api/settings",json={"price_threshold":15,"volume_threshold":6,"categories":[]})
    saved = client.get("/api/brief?saved=true").json()
    assert any(e["id"]==item["id"] and e["saved"] for e in saved["priority"])
