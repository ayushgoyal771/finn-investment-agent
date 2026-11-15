import asyncio
from datetime import datetime, timedelta

from .config import IST
from .domain import CATEGORIES, Preferences, market_summary, utcnow
from .network import ranked_contacts
from .providers import SourceError
from .seed import COMPANIES, PORTFOLIO, demo_bars, demo_events


class Intelligence:
    def __init__(self, store, providers):
        self.store, self.providers = store, providers
        self.anchor = utcnow()
        self.refresh_lock = asyncio.Lock()

    def preferences(self):
        return Preferences.model_validate(self.store.get("preferences", {}))

    def contacts(self):
        from .seed import contacts
        people = contacts()
        updates = self.store.get("contact_dates", {})
        return [{**p, "last_contact": updates.get(p["id"], p["last_contact"])} for p in people]

    async def market(self, mode):
        settings = self.preferences()
        async def one(index, company):
            try:
                if mode == "demo":
                    raw = {"bars": demo_bars(index), "source": "Synthetic EOD scenario", "fetched_at": self.anchor.isoformat(), "cached": False}
                else:
                    raw = await self.providers.market(company[0])
                summary = market_summary(raw["bars"], settings.price_threshold, settings.volume_threshold)
                return {**COMPANIES[company[0]], **summary,
                        "source": raw["source"], "fetched_at": raw["fetched_at"], "cached": raw["cached"], "demo": mode == "demo",
                        "stale": (utcnow().astimezone(IST).date() - datetime.fromisoformat(summary["date"]).date()).days > 4}
            except (SourceError, ValueError, IndexError, KeyError, TypeError) as exc:
                return {**COMPANIES[company[0]], "error": str(exc), "demo": mode == "demo"}
        tasks = [asyncio.create_task(one(i, c)) for i, c in enumerate(PORTFOLIO)]
        try:
            done, pending = await asyncio.wait(tasks, timeout=40)
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
            return [task.result() if task in done else {**COMPANIES[PORTFOLIO[i][0]], "error": "Market refresh time budget exceeded.", "demo": mode == "demo"}
                    for i, task in enumerate(tasks)]
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    async def brief(self, mode="demo", hours=24, saved=False):
        settings, warnings = self.preferences(), []
        if mode == "demo":
            events = demo_events(self.anchor)
        else:
            try:
                events = await self.providers.announcements(set(COMPANIES), max(1, (hours + 23) // 24))
                self.store.add_filings(events)
            except SourceError as exc:
                warnings.append(str(exc))
                events = []
            # Persisted filings retain their true timestamps. They never become fresh on a refresh.
            events = self.store.filings()
        markets = await self.market(mode)
        for market in markets:
            if market.get("error"):
                continue
            if not (market["price_alert"] or market["volume_alert"]):
                continue
            parts = []
            if market["price_alert"]:
                parts.append(f'{market["change"]:+.2f}% close-to-close')
            if market["volume_alert"]:
                parts.append(f'{market["volume_ratio"]:.1f}× prior 20-session volume')
            stamp = (self.anchor - timedelta(minutes=12)).isoformat() if mode == "demo" else datetime.fromisoformat(market["date"] + "T15:30:00").replace(tzinfo=IST).isoformat()
            events.append({"id": f'{mode}-market-{market["symbol"]}-{market["date"]}', "symbol": market["symbol"],
                           "category": "market", "title": " · ".join(parts), "summary": "An end-of-day move crossed your alert rules.",
                           "why": "Volume is compared with the 20 completed sessions before this one. This is an attention signal, not a forecast. Check corporate actions before interpreting a price move.",
                           "published_at": stamp, "source": market["source"], "demo": mode == "demo",
                           "source_url": None if mode == "demo" else f'https://finance.yahoo.com/quote/{market["symbol"]}.NS/history/',
                           "market": market})
        self.store.archive(mode, events)
        if saved:
            events = self.store.archived(mode)
        states, people, now = self.store.states(), self.contacts(), utcnow()
        selected = []
        for event in events:
            state = states.get(event["id"], {"saved": False, "seen": False})
            age = now - datetime.fromisoformat(event["published_at"])
            if saved:
                if not state["saved"]:
                    continue
            elif not timedelta(0) <= age <= timedelta(hours=hours):
                continue
            links = ranked_contacts(people, event["symbol"], person=event.get("incoming_person"))[:2]
            boost = 8 if any(link["path"] for link in links) else 3 if links else 0
            score = min(100, CATEGORIES[event["category"]][0] + boost)
            selected.append({**event, **state, "company": COMPANIES[event["symbol"]]["name"],
                             "sector": COMPANIES[event["symbol"]]["sector"], "score": score,
                             "alert": event["category"] == "market" or event["category"] in settings.categories,
                             "network": links, "category_label": CATEGORIES[event["category"]][1]})
        selected.sort(key=lambda event: (-event["score"], -datetime.fromisoformat(event["published_at"]).timestamp()))
        priority = [e for e in selected if e["score"] >= 60]
        routine = [e for e in selected if e["score"] < 60]
        errors = sum(bool(m.get("error")) for m in markets)
        if errors:
            warnings.append(f"{errors} of {len(markets)} market sources unavailable. Failed sources are shown without prices.")
        return {"mode": mode, "generated_at": now.isoformat(), "scenario_anchor": self.anchor.isoformat() if mode == "demo" else None,
                "hours": hours, "priority": priority, "routine": routine, "market": markets, "warnings": warnings,
                "stats": {"companies": len(PORTFOLIO), "filings": sum(e["category"] != "market" for e in selected),
                          "signals": len(priority), "network_paths": sum(bool(e["network"]) for e in priority),
                          "unread": sum(not e["seen"] for e in priority)},
                "preferences": settings.model_dump()}
