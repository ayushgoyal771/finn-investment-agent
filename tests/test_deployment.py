from backend.config import Config, resolve_allowed_hosts
from backend.main import create_app
from fastapi.testclient import TestClient
from tests.conftest import OfflineProviders


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
