from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "python"))

from campaign_parser import CampaignRequirements  # noqa: E402
from analytics import build_analytics  # noqa: E402
from matcher import DEFAULT_DATABASE, match_creators  # noqa: E402


@pytest.mark.parametrize(
    ("campaign_id", "expected"),
    [
        (1, [("CR001", 99.0), ("CR004", 89.9)]),
        (2, [("CR002", 96.4), ("CR006", 68.4)]),
        (3, [("CR003", 82.6)]),
        (4, [("CR007", 98.6)]),
        (5, [("CR009", 86.5), ("CR005", 80.5)]),
    ],
)
def test_five_campaign_rankings(campaign_id: int, expected: list[tuple[str, float]]) -> None:
    results = match_creators(campaign_id)
    actual = list(zip(results["creator_code"], results["match_score"]))
    assert actual == expected


def test_low_risk_campaign_excludes_major_verified_active_risk() -> None:
    requirements = {
        "target_category": "Fashion",
        "preferred_tags": ["Styling"],
        "brand_experience_preference": "Preferred",
        "risk_tolerance": "Low",
    }
    results = match_creators(requirements=requirements)
    assert "CR008" not in set(results["creator_code"])


def test_medium_risk_campaign_keeps_creator_and_applies_penalty() -> None:
    requirements = {
        "target_category": "Fashion",
        "preferred_tags": ["Styling"],
        "brand_experience_preference": "Preferred",
        "risk_tolerance": "Medium",
    }
    results = match_creators(requirements=requirements)
    risky_creator = results.loc[results["creator_code"].eq("CR008")].iloc[0]
    assert risky_creator["risk_penalty"] == 30
    assert risky_creator["match_score"] == 65.8


def test_required_brand_experience_excludes_unverified_collaboration() -> None:
    requirements = {
        "target_category": "Beauty",
        "preferred_tags": [],
        "brand_experience_preference": "Required",
        "risk_tolerance": "Medium",
    }
    results = match_creators(requirements=requirements)
    assert set(results["creator_code"]) == {"CR001", "CR004"}
    assert results["relevant_brands"].ne("").all()


def test_missing_market_does_not_break_scoring() -> None:
    with sqlite3.connect(DEFAULT_DATABASE) as connection:
        market = connection.execute(
            "SELECT market FROM creators WHERE creator_code = 'CR010'"
        ).fetchone()[0]
    assert market is None

    requirements = {
        "target_category": "Beauty",
        "preferred_tags": ["Makeup"],
        "brand_experience_preference": "Not Important",
        "risk_tolerance": "Medium",
    }
    results = match_creators(requirements=requirements)
    incomplete_creator = results.loc[results["creator_code"].eq("CR010")].iloc[0]
    assert incomplete_creator["data_completeness_score"] == 58
    assert pd.notna(incomplete_creator["match_score"])


def test_score_breakdown_reconciles_to_total() -> None:
    creator = match_creators(1).iloc[0]
    calculated = (
        creator["industry_points"]
        + creator["tag_points"]
        + creator["brand_points"]
        + creator["completeness_points"]
        - creator["risk_penalty"]
    )
    assert round(calculated, 1) == creator["match_score"] == 99.0


def test_minimum_score_and_top_n_are_enforced() -> None:
    results = match_creators(1, top_n=1, minimum_score=50)
    assert len(results) == 1
    assert results["match_score"].ge(50).all()


def test_sql_and_python_results_match_for_all_campaigns() -> None:
    query_template = (PROJECT_DIR / "sql" / "04_matching_query.sql").read_text()
    with sqlite3.connect(DEFAULT_DATABASE) as connection:
        for campaign_id in range(1, 6):
            python_results = match_creators(campaign_id)
            query = query_template.replace(
                "SELECT 1 AS campaign_id",
                f"SELECT {campaign_id} AS campaign_id",
                1,
            )
            sql_results = pd.read_sql_query(query, connection)
            assert list(zip(python_results.creator_code, python_results.match_score)) == list(
                zip(sql_results.creator_code, sql_results.match_score)
            )


def test_ai_schema_rejects_invalid_category_and_too_many_tags() -> None:
    with pytest.raises(ValidationError):
        CampaignRequirements(
            target_category="Gaming",
            preferred_tags=["One", "Two", "Three", "Four", "Five", "Six"],
            brand_experience_preference="Preferred",
            risk_tolerance="Low",
        )


def test_unknown_campaign_id_has_clear_error() -> None:
    with pytest.raises(ValueError, match="Campaign 999 does not exist"):
        match_creators(999)


def test_analytics_summary_matches_sample_database() -> None:
    analytics = build_analytics()
    assert analytics["summary"] == {
        "creator_count": 10,
        "average_completeness": 81.3,
        "verified_collaboration_coverage": 80.0,
        "major_active_risk_count": 1,
    }


def test_analytics_distributions_and_missingness() -> None:
    analytics = build_analytics()
    categories = analytics["category_distribution"].set_index("primary_category")
    assert categories.loc["Beauty", "creator_count"] == 3

    missing = analytics["missing_data"].set_index("field")
    assert missing.loc["Market", "missing_rate"] == 10.0

    risks = analytics["risk_distribution"].set_index("severity")
    assert risks["risk_record_count"].to_dict() == {"Low": 2, "Medium": 1, "High": 1}
