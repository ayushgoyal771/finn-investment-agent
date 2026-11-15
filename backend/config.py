import os
from dataclasses import dataclass
from datetime import timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def resolve_allowed_hosts(environ=None):
    environ = os.environ if environ is None else environ
    explicit = environ.get("FINN_ALLOWED_HOSTS")
    if explicit is not None:
        return tuple(host.strip() for host in explicit.split(",") if host.strip())
    hosts = ["localhost", "127.0.0.1", "[::1]", "testserver"]
    # Render supplies this trusted process environment value, not the HTTP client.
    # Never allow every onrender.com tenant or infer trust from the request's Host.
    external = environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip().lower()
    import re
    if re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", external):
        hosts.append(external)
    return tuple(dict.fromkeys(hosts))


@dataclass(frozen=True)
class Config:
    db_path: Path = Path(os.getenv("FINN_DB_PATH", str(ROOT / "data" / "finn.db")))
    access_token: str = os.getenv("FINN_ACCESS_TOKEN", "")
    openai_key: str = os.getenv("OPENAI_API_KEY", "")
    model: str = os.getenv("FINN_MODEL", "gpt-4.1-mini")
    poll_seconds: int = max(300, int(os.getenv("FINN_POLL_SECONDS", "900")))
    background_live: bool = os.getenv("FINN_BACKGROUND_LIVE", "false").lower() == "true"
    allowed_hosts: tuple = resolve_allowed_hosts()


IST = timezone(timedelta(hours=5, minutes=30))
