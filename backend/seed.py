"""Explicitly synthetic portfolio, events and profiles. Historical research is separate."""
import math
from datetime import timedelta

from .config import IST
from .domain import utcnow

PORTFOLIO = [
    ("TCS", "Tata Consultancy Services", "Technology", "large", 4020),
    ("INFY", "Infosys", "Technology", "large", 1870),
    ("RELIANCE", "Reliance Industries", "Energy", "large", 1290),
    ("HDFCBANK", "HDFC Bank", "Banking", "large", 1755),
    ("ICICIBANK", "ICICI Bank", "Banking", "large", 1260),
    ("ASIANPAINT", "Asian Paints", "Consumer", "large", 2430),
    ("PIDILITIND", "Pidilite Industries", "Consumer", "large", 2940),
    ("PIIND", "PI Industries", "Chemicals", "mid", 3650),
    ("DEEPAKNTR", "Deepak Nitrite", "Chemicals", "mid", 2320),
    ("SRF", "SRF", "Chemicals", "mid", 2350),
    ("LT", "Larsen & Toubro", "Industrials", "large", 3610),
    ("SIEMENS", "Siemens", "Industrials", "large", 6200),
    ("SUNPHARMA", "Sun Pharmaceutical", "Healthcare", "large", 1820),
    ("DIVISLAB", "Divi’s Laboratories", "Healthcare", "large", 5960),
    ("DIXON", "Dixon Technologies", "Electronics", "mid", 14350),
    ("KAYNES", "Kaynes Technology", "Electronics", "mid", 4860),
    ("APLAPOLLO", "APL Apollo Tubes", "Materials", "mid", 1540),
    ("CERA", "Cera Sanitaryware", "Consumer", "small", 6780),
]
COMPANIES = {x[0]: dict(zip(("symbol", "name", "sector", "size"), x[:4])) for x in PORTFOLIO}


def role(company, title, start, end=None):
    return {"company": company, "title": title, "start": start, "end": end}


def contacts():
    today = utcnow().astimezone(IST).date()
    def person(id, name, title, sector, days, roles, education, themes, knows=None):
        return {"id": id, "name": name, "title": title, "sector": sector, "roles": roles,
                "education": education, "themes": themes, "last_contact": (today - timedelta(days=days)).isoformat(),
                "knows": knows or {}, "provenance": "Synthetic profile; invented for this demo", "consent": "demo"}
    return [
        person("meera", "Meera Shah", "Former strategy lead · PI Industries", "Chemicals", 143,
               [role("PIIND", "Strategy lead", 2018, 2023), role("Bharat Chemicals", "Analyst", 2014, 2018)],
               "IIT Delhi · 2014", ["specialty chemicals", "capex", "agrochemicals"],
               {"rohan-desai": "Worked directly together at Bharat Chemicals, 2015–2018 (synthetic attestation)"}),
        person("arjun", "Arjun Rao", "Independent enterprise technology advisor", "Technology", 34,
               [role("TCS", "Delivery director", 2012, 2021)], "IIT Delhi · 2008",
               ["IT services", "AI", "deal conversion", "cloud"]),
        person("neha", "Neha Menon", "Former finance manager · Infosys", "Technology", 82,
               [role("INFY", "Finance manager", 2015, 2022)], "IIM Bangalore · 2015",
               ["cash conversion", "IT services", "margins"]),
        person("vikram", "Vikram Sethi", "Building materials distributor", "Consumer", 192,
               [role("ASIANPAINT", "Regional sales manager", 2010, 2019), role("Independent distribution", "Founder", 2019)],
               "Delhi University · 2009", ["distribution", "paints", "rural demand", "pricing"]),
        person("sana", "Sana Iyer", "Electronics manufacturing consultant", "Electronics", 61,
               [role("DIXON", "Operations lead", 2016, 2022), role("KAYNES", "External advisor", 2023, 2025)],
               "BITS Pilani · 2012", ["semiconductors", "electronics", "working capital", "capex"]),
        person("kabir", "Kabir Kapoor", "Former credit officer · HDFC Bank", "Banking", 104,
               [role("HDFCBANK", "Credit officer", 2013, 2020)], "IIM Ahmedabad · 2013",
               ["rural lending", "credit quality", "banking"]),
        person("leela", "Leela Nair", "Pharma supply-chain advisor", "Healthcare", 25,
               [role("SUNPHARMA", "Procurement head", 2014, 2021)], "ICT Mumbai · 2010",
               ["pharma", "supply chain", "regulation"]),
        person("dev", "Dev Mehta", "Former project director · L&T", "Industrials", 211,
               [role("LT", "Project director", 2011, 2023)], "IIT Bombay · 2006",
               ["infrastructure", "execution", "capex", "working capital"]),
    ]


INCOMING = {"id": "rohan-desai", "name": "Rohan Desai", "title": "Incoming CFO (fictional scenario)",
            "roles": [role("Bharat Chemicals", "Finance controller", 2015, 2019),
                      role("Industrial Ventures", "CFO", 2019, 2025)],
            "education": "IIM Ahmedabad · 2012", "provenance": "Entirely synthetic; not a real appointment"}


def demo_bars(index, now=None):
    now = (now or utcnow()).astimezone(IST)
    day = now.date()
    if now.hour < 16:
        day -= timedelta(days=1)
    days = []
    while len(days) < 25:
        if day.weekday() < 5:
            days.append(day)
        day -= timedelta(days=1)
    days.reverse()
    base = PORTFOLIO[index][4]
    bars = [{"date": day.isoformat(), "close": round(base * (1 + .008 * math.sin(i * .7 + index)), 2),
             "volume": 1000000 + index * 41000 + (i % 4) * 14000} for i, day in enumerate(days)]
    move = {0: 1.2, 5: -4.1, 7: 2.4, 14: 5.2}.get(index, round(math.sin(index + 1) * 1.8, 2))
    bars[-1]["close"] = round(bars[-2]["close"] * (1 + move / 100), 2)
    baseline = sum(b["volume"] for b in bars[-21:-1]) / 20
    bars[-1]["volume"] = round(baseline * {5: 2.6, 7: 2.3, 14: 3.1}.get(index, .85 + (index % 4) * .15))
    return bars


def demo_events(anchor):
    entries = [
        ("pi-cfo", "PIIND", "management_change", 34, "A leadership change worth a conversation", "Fictional scenario: PI Industries appoints Rohan Desai as CFO.", "The incoming executive has a direct path to someone in your network. Understand their approach to capital allocation.", {"incoming_person": INCOMING}),
        ("asian-results", "ASIANPAINT", "results", 94, "When volume grows, but value doesn’t", "Demo results: pricing pressure offsets higher volumes.", "Separate demand from price and product mix. A former regional sales manager can help frame the right questions.", {"results": {"periods": ["Scenario quarter", "Previous quarter", "Year-ago quarter"], "unit": "₹ crore · synthetic consolidated figures", "rows": [{"metric": "Revenue", "values": [8350, 8540, 8870]}, {"metric": "EBITDA", "values": [1590, 1740, 1880]}, {"metric": "PBT", "values": [1380, 1530, 1690]}, {"metric": "PAT", "values": [1020, 1140, 1260]}]}}),
        ("dixon-capex", "DIXON", "capex", 185, "Capacity is a promise. Cash is the test.", "Fictional scenario: a new electronics assembly facility receives board approval.", "Look at utilisation, customer commitments and the working-capital ramp before treating capacity as earnings.", {}),
        ("tcs-results", "TCS", "results", 310, "A strong order book needs to become revenue", "Fictional scenario: quarterly results show steady margins and a healthy pipeline.", "Ask how quickly signed deals turn into billable work. Your network includes a former delivery director.", {}),
        ("srf-rating", "SRF", "credit_rating", 420, "Credit rating reaffirmed", "Fictional scenario: the company’s credit rating is reaffirmed.", "No change in rating. Keep the filing for the record.", {}),
        ("hdfc-dividend", "HDFCBANK", "dividend", 520, "Dividend record date announced", "Fictional scenario: record date for a dividend is announced.", "Administrative update; no change to the investment case.", {}),
        ("infy-meeting", "INFY", "investor_meetings", 610, "Investor meeting schedule", "Fictional scenario: schedule of institutional investor meetings.", "Routine disclosure with no financial guidance.", {}),
        ("cera-compliance", "CERA", "unclassified", 740, "Compliance certificate filed", "Fictional scenario: quarterly compliance confirmation.", "Routine paperwork. Collapsed to keep the signal clear.", {}),
        ("deepak-deal", "DEEPAKNTR", "M&A", 1800, "A transaction to revisit", "Fictional scenario: a small specialty-chemicals acquisition.", "Check integration assumptions and return on incremental capital.", {}),
    ]
    events = []
    for id, symbol, category, minutes, title, summary, why, extra in entries:
        events.append({"id": "demo-" + id, "symbol": symbol, "category": category, "title": title,
                       "summary": summary, "why": why, "published_at": (anchor - timedelta(minutes=minutes)).isoformat(),
                       "source": "Synthetic scenario", "source_url": None, "demo": True, **extra})
    return events
