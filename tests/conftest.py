import pytest
from fastapi.testclient import TestClient

from backend.config import Config
from backend.main import create_app
from backend.providers import SourceError


class OfflineProviders:
    def __init__(self, store):
        self.store = store

    async def close(self):
        pass

    async def announcements(self, symbols, days):
        raise SourceError("Exchange is offline in this test")

    async def market(self, symbol):
        raise SourceError("Market provider is offline in this test")

    async def discover(self, symbol):
        raise SourceError("Discovery is offline in this test")

    async def document(self, document):
        raise SourceError("Documents are offline in this test")


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(Config(db_path=tmp_path / "test.db"), OfflineProviders)) as client:
        yield client
