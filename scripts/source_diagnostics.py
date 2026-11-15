"""Minimal connectivity diagnostics; never print credentials or document content."""
import asyncio
import ssl
import sys
from pathlib import Path

import httpx
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.evidence import ASIAN_AR, ASIAN_CALL, TCS_CALL, INFY_CALL
from backend.providers import HEADERS


async def main():
    async with httpx.AsyncClient(headers=HEADERS, timeout=18, follow_redirects=False) as client:
        for url in ["https://www.nseindia.com/api/corporate-announcements?index=equities", ASIAN_AR, ASIAN_CALL, TCS_CALL, INFY_CALL]:
            try:
                async with client.stream("GET", url) as response:
                    print(response.status_code, url, "redirect:", response.headers.get("location", "none"))
            except httpx.HTTPError as exc:
                print(type(exc).__name__, str(exc), url)


asyncio.run(main())
