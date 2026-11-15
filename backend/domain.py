import math
import re
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator

CATEGORIES = {
    "results": (92, "Results"), "M&A": (96, "Mergers & acquisitions"),
    "management_change": (90, "Leadership"), "litigation": (88, "Litigation"),
    "capex": (82, "Capital expenditure"), "fund_raise": (80, "Fund raising"),
    "pledging": (78, "Promoter pledging"), "credit_rating": (68, "Credit rating"),
    "insider_trading": (58, "Insider trading"), "dividend": (40, "Dividend"),
    "bonus_split": (42, "Bonus / split"), "earnings_call": (35, "Earnings call"),
    "press_release": (50, "Company update"), "postal_ballot": (20, "Postal ballot"),
    "agm_egm": (18, "Shareholder meeting"), "investor_meetings": (12, "Investor meeting"),
    "unclassified": (10, "Routine filing"), "market": (75, "Market signal"),
}


def ticker(value: str) -> str:
    symbol = value.strip().upper()
    if symbol.endswith(".NS"):
        symbol = symbol[:-3]
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9&-]{0,29}", symbol):
        raise ValueError("Use an NSE symbol, for example TCS, INFY or M&M.")
    return symbol


def classify(text: str) -> str:
    text = text.lower()
    # Notices are separated from actual results: a meeting to consider results is not a result.
    rules = [
        ("management_change", r"resign|appoint.*(?:chief|cfo|ceo|director|managing)|management change"),
        ("M&A", r"acquisition|acquire|merger|demerger|joint venture|sale of.*stake"),
        ("litigation", r"litigation|penalty|fine imposed|insolvency|regulatory order|show cause"),
        ("pledging", r"pledg"),
        ("earnings_call", r"transcript|concall|conference call|earnings call"),
        ("investor_meetings", r"analyst.*meet|investor.*meet|investor conference"),
        ("unclassified", r"board meeting.*(?:consider|approv)|newspaper|advertisement|esop|compliance certificate|auditor appointment"),
        ("results", r"financial results|quarterly results|annual results|audited results"),
        ("fund_raise", r"qip|rights issue|preferential allotment|buyback|commercial paper|fund rais"),
        ("capex", r"capex|capacity expansion|new plant|new facility"),
        ("credit_rating", r"credit rating|rating.*(?:upgrade|downgrade|reaffirm)"),
        ("insider_trading", r"insider trading|disclosure.*(?:pit|sast)"),
        ("dividend", r"dividend"), ("bonus_split", r"bonus issue|stock split|sub.division"),
        ("postal_ballot", r"postal ballot"), ("agm_egm", r"annual general meeting|extraordinary general|agm|egm"),
        ("press_release", r"press release|order win|partnership|product launch"),
    ]
    return next((category for category, pattern in rules if re.search(pattern, text)), "unclassified")


def percent(current, previous):
    if previous is None or current is None or previous == 0:
        return None
    # Negative comparatives are ambiguous; don't call a loss-to-profit change a growth rate.
    if previous < 0:
        return None
    return round((current / previous - 1) * 100, 2)


def market_summary(bars, price_threshold=3, volume_threshold=2):
    valid = [b for b in bars if b.get("close") is not None and b["close"] > 0
             and b.get("volume") is not None and b["volume"] >= 0
             and math.isfinite(b["close"]) and math.isfinite(b["volume"])]
    valid = sorted({b["date"]: b for b in valid}.values(), key=lambda b: b["date"])
    if len(valid) < 21:
        raise ValueError("Need 21 completed sessions for a prior-20-session volume baseline.")
    latest, previous = valid[-1], valid[-2]
    average = sum(b["volume"] for b in valid[-21:-1]) / 20
    change = percent(latest["close"], previous["close"])
    ratio = round(latest["volume"] / average, 2) if average > 0 else None
    return {"date": latest["date"], "close": latest["close"], "change": change,
            "volume": latest["volume"], "average_volume": round(average), "volume_ratio": ratio,
            "price_alert": abs(change) > price_threshold,
            "volume_alert": ratio is not None and ratio > volume_threshold,
            "history": [b["close"] for b in valid[-21:]]}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Preferences(StrictModel):
    price_threshold: float = Field(default=3, ge=0.5, le=15, allow_inf_nan=False)
    volume_threshold: float = Field(default=2, ge=1.1, le=6, allow_inf_nan=False)
    categories: list[str] = Field(default=["results", "M&A", "management_change", "litigation", "capex"], max_length=17)

    @field_validator("categories")
    @classmethod
    def known(cls, values):
        if any(v not in CATEGORIES or v == "market" for v in values):
            raise ValueError("Unknown announcement category")
        return list(dict.fromkeys(values))


class ItemState(StrictModel):
    saved: bool | None = None
    seen: bool | None = None


class ResearchRequest(StrictModel):
    symbol: str
    question: str = Field(default="What should I understand before investing?", min_length=3, max_length=600)
    mode: str = Field(default="demo", pattern="^(demo|live)$")
    use_model: bool = False

    @field_validator("symbol")
    @classmethod
    def valid_symbol(cls, value):
        return ticker(value)


class ContactUpdate(StrictModel):
    last_contact: str

    @field_validator("last_contact")
    @classmethod
    def valid_date(cls, value):
        from datetime import date
        from .config import IST
        result = date.fromisoformat(value)
        if result > utcnow().astimezone(IST).date():
            raise ValueError("Last contact cannot be in the future")
        return result.isoformat()


def utcnow():
    return datetime.now(timezone.utc)
