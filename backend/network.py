"""Explainable matching. Co-employment is a possible overlap, never proof of acquaintance."""
import re
from datetime import date

from .config import IST
from .domain import utcnow
from .seed import COMPANIES

COMPETITORS = {"INFY": ["TCS"], "TCS": ["INFY"], "PIDILITIND": ["ASIANPAINT"],
               "ASIANPAINT": ["PIDILITIND"], "DEEPAKNTR": ["PIIND"], "SRF": ["PIIND"],
               "ICICIBANK": ["HDFCBANK"], "DIVISLAB": ["SUNPHARMA"]}


def ranked_contacts(contacts, symbol=None, query="", person=None):
    query_words = set(re.findall(r"[a-z0-9&]+", query.lower())) - {"who", "can", "help", "with", "the", "and", "for", "know", "about", "should", "call", "does", "my"}
    company = COMPANIES.get(symbol, {})
    matches = []
    for contact in contacts:
        score, reasons, path = 0, [], []
        direct = next((r for r in contact["roles"] if r["company"] == symbol), None) if symbol else None
        if direct:
            score += 70
            end = direct["end"] or "present"
            reasons.append(f'{direct["title"]} at {symbol}, {direct["start"]}–{end}')
        competitor = next((r for r in contact["roles"] if r["company"] in COMPETITORS.get(symbol, [])), None)
        if competitor:
            score += 35
            reasons.append(f'Worked at peer {competitor["company"]}; sector context, not inside knowledge')
        if company.get("sector") == contact["sector"]:
            score += 15
            reasons.append(f'{contact["sector"]} experience')
        corpus = " ".join([contact["name"], contact["title"], contact["sector"], *contact["themes"],
                           *(r["company"] for r in contact["roles"])]).lower()
        matched = sorted(w for w in query_words if re.search(r"\b" + re.escape(w) + r"\b", corpus))
        if matched:
            score += min(40, len(matched) * 12)
            reasons.append("Relevant to: " + ", ".join(matched))
        if person:
            attestation = contact["knows"].get(person["id"])
            if attestation:
                score += 100
                reasons.insert(0, attestation)
                path = ["You", contact["name"], person["name"]]
            else:
                for own in contact["roles"]:
                    for target in person["roles"]:
                        start = max(own["start"], target["start"])
                        end = min(own["end"] or 9999, target["end"] or 9999)
                        if own["company"] == target["company"] and start < end:
                            score += 30
                            reasons.append(f'Possible overlap at {own["company"]}, {start}–{end}; acquaintance unverified')
        if score:
            days = max(0, (utcnow().astimezone(IST).date() - date.fromisoformat(contact["last_contact"])).days)
            matches.append({**contact, "score": score, "reasons": reasons, "path": path,
                            "days_since_contact": days, "reconnect": days >= 90,
                            "suggested_question": question_for(company.get("sector"), person)})
    return sorted(matches, key=lambda c: (-c["score"], c["id"]))[:6]


def question_for(sector, person=None):
    if person:
        return f'What was {person["name"]}’s approach to capital allocation when you worked together?'
    return {
        "Technology": "What tends to delay the conversion of signed deals into revenue?",
        "Chemicals": "Which assumptions on utilisation and customer qualification deserve the closest scrutiny?",
        "Consumer": "How would you separate a demand recovery from changes in price and product mix?",
        "Electronics": "What usually happens to working capital as a new assembly line ramps up?",
        "Banking": "What public indicators would reveal early stress in this loan book?",
        "Healthcare": "Which public milestones best indicate supply-chain and regulatory execution?",
    }.get(sector, "Which public operating indicators would you examine to test management’s assumptions?")
