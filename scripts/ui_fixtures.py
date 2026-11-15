"""Generate UI test data from the real API in-process. No network or browser is used."""
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fastapi.testclient import TestClient
from backend.config import Config, ROOT
from backend.main import create_app


class NoNetwork:
    def __init__(self, store):
        pass

    async def close(self):
        pass


def main():
    scratch = ROOT / "artifacts"
    scratch.mkdir(exist_ok=True)
    config = Config(db_path=scratch / ("ui-" + uuid.uuid4().hex[:10] + ".db"), openai_key="")
    with TestClient(create_app(config, NoNetwork)) as client:
        fixtures = {"brief":client.get("/api/brief").json(), "settings":client.get("/api/settings").json(),
                    "network":client.get("/api/network").json(), "research":client.post("/api/research",json={"symbol":"ASIANPAINT"}).json()}
    (scratch/"ui-fixtures.json").write_text(json.dumps(fixtures),encoding="utf-8")


if __name__ == "__main__":
    main()
