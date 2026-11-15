import pytest

from backend.evidence import PACKS
from backend.research import rank_facts, retrieve, validate_synthesis


def test_question_selects_cash_evidence():
    result = rank_facts(PACKS["INFY"]["facts"], "How well does profit convert to cash?")
    assert result[0]["id"] == "infy-cash"


def test_unanswerable_question_does_not_generate_evidence():
    assert rank_facts(PACKS["TCS"]["facts"], "Who won Wimbledon?") == []


def test_synthesis_rejects_nonexistent_citation():
    with pytest.raises(ValueError):
        validate_synthesis({"claims":[{"text":"Revenue increased", "source_ids":["invented"]}], "unanswered":[]},PACKS["TCS"]["facts"])


def test_synthesis_requires_citations_and_forbids_extra_fields():
    for payload in [{"claims":[{"text":"Revenue increased", "source_ids":[]}], "unanswered":[]},
                    {"claims":[{"text":"Revenue increased", "source_ids":["tcs-growth"]}], "unanswered":[], "action":"buy"}]:
        with pytest.raises(ValueError):
            validate_synthesis(payload, PACKS["TCS"]["facts"])


def test_valid_synthesis_retains_exact_evidence_identifiers():
    payload={"claims":[{"text":"The annual report shows reported revenue growth.", "source_ids":["tcs-growth"]}], "unanswered":["Future growth is not established."]}
    assert validate_synthesis(payload, PACKS["TCS"]["facts"]) == payload


def test_live_retrieval_uses_new_ticker_document_and_pdf_page():
    docs=[{"sha256":"1234", "url":"https://www.bseindia.com/example.pdf", "title":"Unseen Company AR",
           "kind":"annual_report", "pages":[{"page":42,"text":"Operating cash flow increased during the year. "*8}]}]
    result=retrieve(docs,"cash flow")
    assert result and result[0]["url"].endswith("#page=42")
    assert result[0]["locator"] == "PDF page 42" and not result[0]["paraphrase"]
