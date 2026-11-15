from backend.config import Config, resolve_allowed_hosts
from backend.main import create_app
from fastapi.testclient import TestClient
from tests.conftest import OfflineProviders
import pytest


def test_local_hosts_remain_default():
    assert resolve_allowed_hosts({}) == ("localhost", "127.0.0.1", "[::1]", "testserver")


def test_render_hostname_is_allowed_without_a_tenant_wildcard():
    result = resolve_allowed_hosts({"RENDER_EXTERNAL_HOSTNAME": "finn-demo.onrender.com"})
    assert "finn-demo.onrender.com" in result
    assert "*.onrender.com" not in result


def test_explicit_hosts_override_render_default_and_trim_whitespace():
    assert resolve_allowed_hosts({"FINN_ALLOWED_HOSTS": " localhost, finn.example.com, ",
                                  "RENDER_EXTERNAL_HOSTNAME": "finn.onrender.com"}) == ("localhost", "finn.example.com")


def test_url_and_wildcard_are_not_treated_as_render_hostname():
    for value in ["https://finn.onrender.com", "*.onrender.com", "finn.onrender.com:443", "finn.onrender.com/path"]:
        assert resolve_allowed_hosts({"RENDER_EXTERNAL_HOSTNAME": value}) == resolve_allowed_hosts({})


def test_render_health_check_and_api_auth_with_external_host(tmp_path):
    hosts = resolve_allowed_hosts({"RENDER_EXTERNAL_HOSTNAME": "finn-demo.onrender.com"})
    app = create_app(Config(db_path=tmp_path/"deployed.db", access_token="test-token", allowed_hosts=hosts), OfflineProviders)
    with TestClient(app, base_url="https://finn-demo.onrender.com") as client:
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/settings").status_code == 401
        assert client.get("/api/settings", headers={"Authorization":"Bearer test-token"}).status_code == 200
        assert client.get("/api/health", headers={"Host":"someone-else.onrender.com"}).status_code == 400


@pytest.mark.parametrize("token", ["", "previous-private-token"])
def test_public_demo_opens_all_workflows_without_credentials(tmp_path, token):
    config = Config(db_path=tmp_path/"public.db", public_demo=True, access_token=token,
                    allowed_hosts=("finn-demo.onrender.com",))
    with TestClient(create_app(config, OfflineProviders), base_url="https://finn-demo.onrender.com",
                    client=("203.0.113.5", 5000)) as client:
        health = client.get("/api/health").json()
        assert health["public_demo"] is True and health["auth_required"] is False
        assert client.get("/api/brief").status_code == 200
        assert client.get("/api/network").json()["synthetic"] is True
        assert client.post("/api/research", json={"symbol":"ASIANPAINT"}).status_code == 200
        assert client.patch("/api/items/demo-pi-cfo", json={"saved":True}).status_code == 200
        assert client.put("/api/settings", json={}, headers={"Origin":"https://attacker.example"}).status_code == 403
        assert client.get("/api/brief", headers={"Host":"someone-else.onrender.com"}).status_code == 400


def test_private_mode_still_denies_remote_access_without_a_token(tmp_path):
    config = Config(db_path=tmp_path/"private.db", public_demo=False, access_token="")
    with TestClient(create_app(config, OfflineProviders), client=("203.0.113.5", 5000)) as client:
        assert client.get("/api/network").status_code == 403


def test_public_demo_cannot_spend_a_configured_model_key(tmp_path):
    config = Config(db_path=tmp_path/"no-model.db", public_demo=True, openai_key="test-not-a-real-key")
    with TestClient(create_app(config, OfflineProviders)) as client:
        assert client.get("/api/health").json()["model_available"] is False
        response = client.post("/api/research", json={"symbol":"TCS", "use_model":True})
        assert response.status_code == 403
        assert "disabled in the public demo" in response.json()["detail"]
