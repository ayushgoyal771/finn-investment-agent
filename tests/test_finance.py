import math

import pytest
from pydantic import ValidationError

from backend.domain import Preferences, ResearchRequest, classify, market_summary, percent, ticker


def bars(last_volume=300, last_close=106):
    return [{"date": f"2025-01-{i+1:02}", "close": last_close if i == 20 else 100,
             "volume": last_volume if i == 20 else 100} for i in range(21)]


def test_volume_baseline_excludes_current_session():
    result = market_summary(bars())
    assert result["average_volume"] == 100
    assert result["volume_ratio"] == 3
    assert result["change"] == 6
    assert result["volume_alert"] and result["price_alert"]


def test_threshold_is_strictly_beyond_not_equal():
    result = market_summary(bars(last_volume=200, last_close=103), price_threshold=3, volume_threshold=2)
    assert not result["volume_alert"] and not result["price_alert"]


def test_negative_price_move_triggers():
    result = market_summary(bars(last_close=94))
    assert result["change"] == -6
    assert result["price_alert"]


def test_zero_volume_baseline_does_not_divide_by_zero():
    series = bars()
    for bar in series[:-1]:
        bar["volume"] = 0
    result = market_summary(series)
    assert result["volume_ratio"] is None and not result["volume_alert"]


def test_insufficient_and_bad_bars_are_rejected():
    with pytest.raises(ValueError):
        market_summary(bars()[:-1])
    series = bars()
    series[5]["close"] = math.nan
    with pytest.raises(ValueError):
        market_summary(series)


def test_duplicate_session_not_counted_twice():
    with pytest.raises(ValueError):
        market_summary(bars()[:-1] + [bars()[0]])


@pytest.mark.parametrize("current,prior,expected", [(120,100,20),(90,100,-10),(1,0,None),(1,-1,None),(None,10,None)])
def test_percentage_comparisons(current, prior, expected):
    assert percent(current, prior) == expected


@pytest.mark.parametrize("source,expected", [(" m&m.ns ","M&M"),("TCS","TCS"),("BAJAJ-AUTO","BAJAJ-AUTO")])
def test_ticker_normalization(source, expected):
    assert ticker(source) == expected


@pytest.mark.parametrize("source", ["../TCS","https://localhost","TCS?x=1","TCS.BO","A"*31,"<script>"])
def test_ticker_rejects_paths_and_non_nse_symbols(source):
    with pytest.raises(ValueError):
        ticker(source)


@pytest.mark.parametrize("text,category", [
    ("Board Meeting to consider financial results", "unclassified"),
    ("Audited Financial Results for quarter ended", "results"),
    ("Transcript of earnings conference call", "earnings_call"),
    ("Appointment of Chief Financial Officer", "management_change"),
    ("Acquisition of a subsidiary", "M&A"), ("Capacity expansion at new plant", "capex"),
    ("Investor meeting schedule", "investor_meetings"), ("Compliance certificate", "unclassified")])
def test_classification_distinguishes_results_from_notices(text, category):
    assert classify(text) == category


def test_preferences_validate_finite_bounds_and_categories():
    for payload in ({"price_threshold":float('nan')}, {"volume_threshold":0}, {"categories":["bogus"]}, {"arbitrary":True}):
        with pytest.raises(ValidationError):
            Preferences(**payload)
    assert Preferences(categories=["results","results"]).categories == ["results"]


def test_research_question_has_size_bound():
    with pytest.raises(ValidationError):
        ResearchRequest(symbol="TCS", question="a"*601)
