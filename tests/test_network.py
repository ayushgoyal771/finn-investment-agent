from copy import deepcopy

from backend.network import ranked_contacts
from backend.seed import INCOMING, contacts


def test_attested_second_degree_path_is_explained():
    matches = ranked_contacts(contacts(), "PIIND", person=INCOMING)
    assert matches[0]["id"] == "meera"
    assert matches[0]["path"] == ["You", "Meera Shah", "Rohan Desai"]
    assert "synthetic attestation" in matches[0]["reasons"][0]


def test_shared_employer_does_not_create_attested_relationship():
    people = deepcopy(contacts())
    people[0]["knows"] = {}
    match = ranked_contacts(people, person=INCOMING)[0]
    assert match["path"] == []
    assert any("acquaintance unverified" in r for r in match["reasons"])


def test_non_overlapping_tenure_is_not_professional_overlap():
    people = deepcopy(contacts())
    people[0]["knows"] = {}
    people[0]["roles"][1]["start"] = 2000
    people[0]["roles"][1]["end"] = 2004
    assert ranked_contacts(people, person=INCOMING) == []


def test_arbitrary_ticker_can_match_explicit_employer():
    people = deepcopy(contacts())
    people[0]["roles"].append({"company":"UNSEENCO","title":"Engineer","start":2020,"end":2023})
    assert ranked_contacts(people, symbol="UNSEENCO")[0]["id"] == "meera"


def test_expertise_search_and_no_match():
    assert ranked_contacts(contacts(), query="semiconductors")[0]["id"] == "sana"
    assert ranked_contacts(contacts(), query="astronomy") == []


def test_employer_peer_link_is_labelled():
    match = next(c for c in ranked_contacts(contacts(), "INFY") if c["id"] == "arjun")
    assert any("peer TCS" in reason for reason in match["reasons"])
