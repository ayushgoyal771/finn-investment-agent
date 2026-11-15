import asyncio
import hmac
import re
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager, suppress
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import Config, ROOT
from .db import Store
from .domain import CATEGORIES, ContactUpdate, ItemState, Preferences, ResearchRequest, ticker
from .network import ranked_contacts
from .providers import Providers, SourceError
from .research import research
from .service import Intelligence


def create_app(config=None, providers_factory=Providers):
    config = config or Config()
    store = Store(config.db_path)
    limits = defaultdict(deque)

    @asynccontextmanager
    async def lifespan(app):
        store.init()
        providers = providers_factory(store)
        intelligence = Intelligence(store, providers)
        app.state.store, app.state.providers, app.state.intelligence = store, providers, intelligence
        app.state.research_slots = asyncio.Semaphore(2)
        async def poll():
            while True:
                await asyncio.sleep(config.poll_seconds)
                with suppress(SourceError, asyncio.TimeoutError):
                    async with intelligence.refresh_lock:
                        await asyncio.wait_for(intelligence.brief("live", 168), 65)
        task = asyncio.create_task(poll()) if config.background_live else None
        try:
            yield
        finally:
            if task:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
            await providers.close()

    app = FastAPI(title="FINN", version="1.0.0", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(config.allowed_hosts))

    @app.middleware("http")
    async def guard(request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/") and path != "/api/health":
            if config.access_token and not config.public_demo:
                supplied = request.headers.get("authorization", "")
                if not hmac.compare_digest(supplied.encode(), ("Bearer " + config.access_token).encode()):
                    return JSONResponse({"detail": "Enter the server access token to unlock FINN."}, status_code=401)
            elif not config.public_demo and request.client and request.client.host not in {"127.0.0.1", "::1", "testclient"}:
                return JSONResponse({"detail": "Remote access requires FINN_ACCESS_TOKEN."}, status_code=403)
            if request.method not in {"GET", "HEAD", "OPTIONS"}:
                origin = request.headers.get("origin")
                if origin and urlparse(origin).netloc != request.headers.get("host"):
                    return JSONResponse({"detail": "Cross-origin writes are not permitted."}, status_code=403)
                try:
                    if int(request.headers.get("content-length", "0")) > 16384:
                        return JSONResponse({"detail": "Request is too large."}, status_code=413)
                except ValueError:
                    return JSONResponse({"detail": "Invalid Content-Length."}, status_code=400)
            if path == "/api/research" or request.method not in {"GET", "HEAD", "OPTIONS"}:
                key = (request.client.host if request.client else "local", "research" if path == "/api/research" else "writes")
                now = time.monotonic()
                bucket = limits[key]
                while bucket and bucket[0] <= now - 60:
                    bucket.popleft()
                if len(bucket) >= (8 if path == "/api/research" else 90):
                    return JSONResponse({"detail": "Please wait a minute before trying again."}, status_code=429, headers={"Retry-After": "60"})
                bucket.append(now)
        response = await call_next(request)
        response.headers.update({
            "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer", "X-Frame-Options": "DENY",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        })
        if path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(SourceError)
    async def source_error(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=503)

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "auth_required": bool(config.access_token) and not config.public_demo,
                "public_demo": config.public_demo, "model_available": bool(config.openai_key) and not config.public_demo,
                "version": "1.0.0"}

    @app.get("/api/brief")
    async def brief(mode: str = Query("demo", pattern="^(demo|live)$"), hours: int = Query(24, ge=1, le=168), saved: bool = False):
        async def locked_brief():
            async with app.state.intelligence.refresh_lock:
                return await app.state.intelligence.brief(mode, hours, saved)
        try:
            return await asyncio.wait_for(locked_brief(), timeout=70)
        except asyncio.TimeoutError:
            raise HTTPException(504, "Sources took too long to respond. Try again or use the demo.")

    @app.get("/api/settings")
    async def settings():
        return {"preferences": app.state.intelligence.preferences().model_dump(),
                "categories": [{"id": key, "label": value[1]} for key, value in CATEGORIES.items() if key != "market"]}

    @app.put("/api/settings")
    async def update_settings(preferences: Preferences):
        store.set("preferences", preferences.model_dump())
        return preferences.model_dump()

    @app.patch("/api/items/{item_id}")
    async def item_state(item_id: str, value: ItemState):
        if not re.fullmatch(r"[a-zA-Z0-9&_-]{1,100}", item_id):
            raise HTTPException(422, "Invalid item identifier")
        store.state(item_id, value.saved, value.seen)
        return {"ok": True}

    @app.post("/api/research")
    async def run_research(value: ResearchRequest):
        if config.public_demo and value.use_model:
            raise HTTPException(403, "Model synthesis is disabled in the public demo. Primary-source research remains available.")
        async def limited_research():
            async with app.state.research_slots:
                return await research(value, app.state.providers, config, app.state.intelligence.contacts())
        try:
            return await asyncio.wait_for(limited_research(), timeout=125)
        except asyncio.TimeoutError:
            raise HTTPException(504, "Research timed out. Try a narrower question or the bundled demo.")

    @app.get("/api/network")
    async def network(q: str = Query("", max_length=300), symbol: str | None = None):
        if symbol:
            try:
                symbol = ticker(symbol)
            except ValueError as exc:
                raise HTTPException(422, str(exc))
        people = app.state.intelligence.contacts()
        matches = ranked_contacts(people, symbol, q) if q or symbol else ranked_contacts(people, query="capex cash IT paints rural pharma")
        return {"contacts": people, "matches": matches, "synthetic": True,
                "notice": "All people, roles and relationships are invented. No professional-profile scraping is used."}

    @app.get("/api/network/export")
    async def network_export():
        return JSONResponse({"synthetic": True, "contacts": app.state.intelligence.contacts()},
                            headers={"Content-Disposition": 'attachment; filename="finn-network.json"'})

    @app.post("/api/network/{contact_id}/contacted")
    async def contacted(contact_id: str, value: ContactUpdate):
        if contact_id not in {p["id"] for p in app.state.intelligence.contacts()}:
            raise HTTPException(404, "Contact not found")
        dates = store.get("contact_dates", {})
        dates[contact_id] = value.last_contact
        store.set("contact_dates", dates)
        return {"ok": True}

    @app.get("/")
    async def index():
        return FileResponse(ROOT / "frontend" / "index.html")

    app.mount("/assets", StaticFiles(directory=ROOT / "frontend"), name="assets")
    return app


app = create_app()
