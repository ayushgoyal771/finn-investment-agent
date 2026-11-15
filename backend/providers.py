"""Bounded public-source adapters. Access denial is a source error, never a reason to bypass it."""
import asyncio
import hashlib
import io
import re
import socket
import ipaddress
import ssl
from datetime import datetime, time, timedelta, timezone
from urllib.parse import quote, urljoin, urlparse

import httpx
import truststore
from bs4 import BeautifulSoup
from pypdf import PdfReader

from .config import IST
from .domain import classify, utcnow

HEADERS = {"User-Agent": "FINN-Research-Prototype/1.0 (personal research; public company disclosures)",
           "Accept": "application/json,text/html,application/pdf"}
MAX_BYTES = 25 * 1024 * 1024
EXCHANGE_HOSTS = {"www.nseindia.com", "www.nseindia.in", "nsearchives.nseindia.com", "archives.nseindia.com"}


class SourceError(Exception):
    pass


def public_url(url, allowed_hosts):
    try:
        parsed = urlparse(url)
        allowed = (parsed.scheme == "https" and not parsed.username and not parsed.password
                   and parsed.port in (None, 443) and parsed.hostname in allowed_hosts)
    except (ValueError, TypeError, AttributeError):
        allowed = False
    if not allowed:
        raise SourceError("Document URL is outside the approved primary-source hosts.")
    return url


async def check_dns(url):
    host = urlparse(url).hostname
    try:
        results = await asyncio.get_running_loop().getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise SourceError("Source hostname could not be resolved.") from exc
    if not results or any(not ipaddress.ip_address(r[4][0]).is_global for r in results):
        raise SourceError("Private network destinations are not permitted.")


class Providers:
    def __init__(self, store, transport=None):
        self.store = store
        self.client = httpx.AsyncClient(headers=HEADERS, timeout=httpx.Timeout(18, connect=8),
                                        verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
                                        follow_redirects=False, transport=transport)
        self.semaphore = asyncio.Semaphore(3)

    async def close(self):
        await self.client.aclose()

    async def fetch(self, url, allowed_hosts, limit=MAX_BYTES):
        """Validate each redirect; no user-supplied fetch URL is accepted by the API."""
        for _ in range(4):
            public_url(url, allowed_hosts)
            await check_dns(url)
            try:
                async with self.client.stream("GET", url) as response:
                    if response.status_code in (301, 302, 303, 307, 308):
                        url = urljoin(url, response.headers.get("location", ""))
                        continue
                    response.raise_for_status()
                    chunks, size = [], 0
                    async for chunk in response.aiter_bytes():
                        size += len(chunk)
                        if size > limit:
                            raise SourceError("Source document exceeds the 25 MB limit.")
                        chunks.append(chunk)
                    return b"".join(chunks)
            except httpx.HTTPError as exc:
                code = getattr(getattr(exc, "response", None), "status_code", None)
                raise SourceError(f"Source unavailable{f' (HTTP {code})' if code else ' (network/timeout)'}. Try again later.") from exc
        raise SourceError("Too many source redirects.")

    async def market(self, symbol):
        key = "market-v1:" + symbol
        cached = self.store.cached(key, 900)
        if cached is not None:
            return {**cached, "cached": True}
        async with self.semaphore:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol + '.NS', safe='')}?range=3mo&interval=1d"
            import json
            try:
                body = json.loads(await self.fetch(url, {"query1.finance.yahoo.com"}, 2 * 1024 * 1024))
                chart = body["chart"]["result"][0]
                quotes = chart["indicators"]["quote"][0]
                now = utcnow().astimezone(IST)
                bars = []
                for i, timestamp in enumerate(chart.get("timestamp", [])):
                    day = datetime.fromtimestamp(timestamp, timezone.utc).astimezone(IST).date()
                    if day > now.date() or (day == now.date() and now.time() < time(15, 35)):
                        continue
                    bars.append({"date": day.isoformat(), "close": quotes["close"][i], "volume": quotes["volume"][i]})
                data = {"symbol": symbol, "name": chart["meta"].get("longName", symbol), "bars": bars,
                        "source": "Yahoo Finance · daily close", "fetched_at": utcnow().isoformat(), "cached": False}
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                raise SourceError("No usable market data was returned for this NSE ticker.") from exc
            self.store.cache(key, data)
            return data

    async def announcements(self, symbols, days=7):
        key = f"nse-v2:{days}"
        cached = self.store.cached(key, 300)
        if cached is None:
            now = utcnow().astimezone(IST)
            start = (now - timedelta(days=days)).strftime("%d-%m-%Y")
            end = now.strftime("%d-%m-%Y")
            url = f"https://www.nseindia.in/api/corporate-announcements?index=equities&from_date={start}&to_date={end}"
            import json
            try:
                rows = json.loads(await self.fetch(url, EXCHANGE_HOSTS, 12 * 1024 * 1024))
                if not isinstance(rows, list):
                    raise ValueError()
                cached = []
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    symbol = str(row.get("symbol", ""))
                    title = str(row.get("desc", "Exchange disclosure"))
                    summary = str(row.get("attchmntText", "") or title)
                    stamp = row.get("an_dt") or row.get("sort_date") or row.get("exchdisstime")
                    parsed = None
                    for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d-%b-%Y %H:%M"):
                        try:
                            parsed = datetime.strptime(str(stamp), fmt).replace(tzinfo=IST)
                            break
                        except ValueError:
                            pass
                    if parsed is None:
                        continue  # Unknown timestamps must not be passed off as fresh.
                    attachment = row.get("attchmntFile")
                    try:
                        attachment = public_url(attachment, EXCHANGE_HOSTS) if attachment else None
                    except (SourceError, ValueError):
                        attachment = None
                    id = hashlib.sha256(f"{symbol}|{stamp}|{title}|{attachment}".encode()).hexdigest()[:24]
                    cached.append({"id": "nse-" + id, "symbol": symbol, "title": title, "summary": summary[:1800],
                                   "category": classify(title + " " + summary), "published_at": parsed.astimezone(timezone.utc).isoformat(),
                                   "why": "Review the primary filing before drawing conclusions. Classification uses the exchange description.",
                                   "source": "NSE corporate disclosure", "source_url": attachment, "demo": False})
            except (ValueError, TypeError, KeyError) as exc:
                raise SourceError("Exchange returned an unsupported response.") from exc
            self.store.cache(key, cached)
        return [r for r in cached if r["symbol"] in symbols]

    async def discover(self, symbol):
        key = "discovery-v3:" + symbol
        cached = self.store.cached(key, 86400)
        if cached is not None:
            return cached
        url = f"https://www.screener.in/company/{quote(symbol, safe='')}/consolidated/"
        html = await self.fetch(url, {"www.screener.in"}, 3 * 1024 * 1024)
        soup = BeautifulSoup(html, "html.parser")
        heading = soup.find("h1")
        name = heading.get_text(" ", strip=True) if heading else symbol
        documents = []
        # Screener is a link directory only. Its ratios, summaries and tables never enter research.
        for header in soup.find_all(["h2", "h3"]):
            label = header.get_text(" ", strip=True).lower()
            kind = "annual_report" if "annual reports" in label else "transcript" if "concalls" in label else None
            if not kind:
                continue
            # The concall heading may be nested inside a toolbar while its list is a sibling.
            # Walk to the next heading, rather than assuming one particular parent structure.
            for link in header.next_elements:
                if getattr(link, "name", None) in {"h2", "h3"}:
                    break
                if getattr(link, "name", None) != "a" or not link.get("href"):
                    continue
                text = link.get_text(" ", strip=True)
                if kind == "transcript" and text.lower() != "transcript":
                    continue
                href = urljoin(url, link["href"])
                host = urlparse(href).hostname or ""
                # Only exchange-filed originals for unknown tickers. A shared CDN alone isn't provenance.
                if host not in {"www.bseindia.com", *EXCHANGE_HOSTS}:
                    continue
                if not (".pdf" in href.lower() or "annpdfopen" in href.lower()):
                    continue
                item = link.find_parent("li")
                title = item.get_text(" ", strip=True).split("AI Summary")[0][:120] if item else text
                if href not in {d["url"] for d in documents}:
                    documents.append({"kind": kind, "title": title, "url": href})
                if sum(d["kind"] == kind for d in documents) >= (1 if kind == "annual_report" else 4):
                    break
        if not documents:
            raise SourceError("No accessible primary annual-report or transcript links found for this ticker.")
        data = {"symbol": symbol, "name": name, "documents": documents,
                "discovered_at": utcnow().isoformat(), "directory_url": url}
        self.store.cache(key, data)
        return data

    async def document(self, document):
        key = "document-v2:" + hashlib.sha256(document["url"].encode()).hexdigest()
        cached = self.store.cached(key, 30 * 86400)
        if cached is not None:
            return cached
        async with self.semaphore:
            host = urlparse(document["url"]).hostname
            content = await self.fetch(document["url"], {host})
            if not content.startswith(b"%PDF"):
                raise SourceError("Source did not return a PDF; no content was used.")
            pages = await asyncio.to_thread(extract_pages, content)
            data = {**document, "pages": pages, "sha256": hashlib.sha256(content).hexdigest(),
                    "fetched_at": utcnow().isoformat()}
            self.store.cache(key, data)
            return data


def extract_pages(content):
    try:
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted:
            raise SourceError("Encrypted PDFs are not supported.")
        if len(reader.pages) > 650:
            raise SourceError("PDF exceeds the 650-page processing limit.")
        pages, total = [], 0
        for i, page in enumerate(reader.pages):
            text = re.sub(r"\s+", " ", page.extract_text() or "").strip()
            text = text[:30000]
            total += len(text)
            if total > 3_000_000:
                break
            if len(text) > 70:
                pages.append({"page": i + 1, "text": text})
        if not pages:
            raise SourceError("No readable text. This PDF may require OCR, which the prototype does not perform.")
        return pages
    except SourceError:
        raise
    except Exception as exc:
        raise SourceError("Could not extract text from this PDF.") from exc
