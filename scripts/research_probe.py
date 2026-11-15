"""Opt-in full research check for a ticker outside the bundled evidence packs."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.config import Config, ROOT
from backend.db import Store
from backend.domain import ResearchRequest
from backend.providers import Providers, SourceError
from backend.research import research
from backend.seed import contacts


async def main():
    config = Config(db_path=ROOT/"artifacts"/"provider-probe.db")
    store = Store(config.db_path)
    store.init()
    providers = Providers(store)
    try:
        data = await research(ResearchRequest(symbol="HCLTECH",mode="live",question="How did revenue, operating margins and cash flow change?"),providers,config,contacts())
        output = {"status":"ok", "symbol":data["symbol"], "facts":len(data["facts"]),"coverage":data["coverage"],
                  "sources":[{"title":f["title"],"url":f["url"],"locator":f["locator"]} for f in data["facts"]], "warnings":data["warnings"]}
    except SourceError as exc:
        output = {"status":"unavailable", "detail":str(exc)}
    finally:
        await providers.close()
    print(json.dumps(output,indent=2))
    (ROOT/"artifacts"/"research-probe.json").write_text(json.dumps(output,indent=2),encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
