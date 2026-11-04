"""Explainable pandas implementation of the creator matching MVP."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = PROJECT_DIR / "database" / "creator_matching.db"

WEIGHTS = {
    "industry": 30.0,
    "tags": 25.0,
    "brand": 25.0,
    "completeness": 20.0,
}

RISK_PENALTIES = {"Low": 5.0, "Medium": 15.0, "High": 30.0}

RELEVANT_BRAND_INDUSTRIES = {
    "Beauty": {"Beauty", "Skincare"},
    "Fashion": {"Fashion"},
    "Fitness": {"Fitness", "Wellness"},
    "Lifestyle": {"Lifestyle", "Wellness", "Home"},
    "Tech": {"Tech", "Technology"},
}

TABLES = [
    "creators",
    "tags",
    "creator_tags",
    "brand_collaborations",
    "risk_records",
    "campaigns",
    "campaign_tags",
]


def load_tables(database_path: Path) -> dict[str, pd.DataFrame]:
    """Load the seven normalized SQLite tables into pandas DataFrames."""
    with sqlite3.connect(database_path) as connection:
        return {
            table: pd.read_sql_query(f"SELECT * FROM {table}", connection)
            for table in TABLES
        }


def build_explanation(row: pd.Series) -> list[str]:
    """Turn score components into human-readable recommendation reasons."""
    reasons: list[str] = []

    if row["industry_points"] > 0:
        reasons.append(f"Category match: {row['primary_category']}")
    if row["matched_tag_count"] > 0:
        reasons.append(f"Matched tags: {row['matched_tags']}")
    if row["relevant_verified_brand_count"] > 0:
        reasons.append(
            f"{int(row['relevant_verified_brand_count'])} relevant verified brand collaboration(s)"
        )
    reasons.append(f"Data completeness: {row['data_completeness_score']:.0f}/100")

    if row["risk_penalty"] > 0:
        reasons.append(f"Active verified risk penalty: -{row['risk_penalty']:.0f}")
    else:
        reasons.append("No active verified risk penalty in the sample data")

    return reasons


def match_creators(
    campaign_id: int | None = None,
    database_path: Path = DEFAULT_DATABASE,
    top_n: int = 5,
    minimum_score: float = 50.0,
    requirements: dict | None = None,
) -> pd.DataFrame:
    """Return recommendations for a stored campaign or structured requirements."""
    data = load_tables(database_path)

    if requirements is None:
        if campaign_id is None:
            raise ValueError("Provide campaign_id or requirements")
        campaign_rows = data["campaigns"].query("campaign_id == @campaign_id")
        if campaign_rows.empty:
            raise ValueError(f"Campaign {campaign_id} does not exist")
        campaign = campaign_rows.iloc[0]
        requested_tag_ids = set(
            data["campaign_tags"]
            .query("campaign_id == @campaign_id")["tag_id"]
            .tolist()
        )
    else:
        campaign = pd.Series(requirements)
        requested_names = set(requirements.get("preferred_tags", []))
        requested_tag_ids = set(
            data["tags"].loc[data["tags"]["tag_name"].isin(requested_names), "tag_id"]
        )

    creators = data["creators"].query("profile_status == 'Active'").copy()

    # 1. Category points
    creators["industry_points"] = creators["primary_category"].eq(
        campaign["target_category"]
    ) * WEIGHTS["industry"]

    # 2. Tag overlap points
    creator_tag_sets = (
        data["creator_tags"].groupby("creator_id")["tag_id"].agg(set).to_dict()
    )
    tag_names = data["tags"].set_index("tag_id")["tag_name"].to_dict()

    creators["matched_tag_ids"] = creators["creator_id"].map(
        lambda creator_id: creator_tag_sets.get(creator_id, set()) & requested_tag_ids
    )
    creators["matched_tag_count"] = creators["matched_tag_ids"].map(len)
    creators["requested_tag_count"] = len(requested_tag_ids)
    creators["matched_tags"] = creators["matched_tag_ids"].map(
        lambda ids: ", ".join(tag_names[tag_id] for tag_id in sorted(ids))
    )
    if requested_tag_ids:
        creators["tag_points"] = (
            WEIGHTS["tags"]
            * creators["matched_tag_count"]
            / len(requested_tag_ids)
        )
    else:
        creators["tag_points"] = WEIGHTS["tags"]

    # 3. Verified, category-relevant brand experience
    relevant_industries = RELEVANT_BRAND_INDUSTRIES[campaign["target_category"]]
    relevant_collaborations = data["brand_collaborations"].loc[
        data["brand_collaborations"]["verified"].eq(1)
        & data["brand_collaborations"]["brand_industry"].isin(relevant_industries)
    ]
    brand_counts = relevant_collaborations.groupby("creator_id").size()
    brand_names = relevant_collaborations.groupby("creator_id")["brand_name"].agg(
        lambda values: ", ".join(sorted(values))
    )
    creators["relevant_verified_brand_count"] = (
        creators["creator_id"].map(brand_counts).fillna(0).astype(int)
    )
    creators["relevant_brands"] = creators["creator_id"].map(brand_names).fillna("")
    creators["brand_points"] = creators["relevant_verified_brand_count"].gt(0).map(
        {True: WEIGHTS["brand"], False: 0.0}
    )
    if campaign["brand_experience_preference"] == "Not Important":
        creators["brand_points"] = WEIGHTS["brand"]

    # 4. Data completeness points
    creators["completeness_points"] = (
        creators["data_completeness_score"] / 100 * WEIGHTS["completeness"]
    )

    # 5. Highest active, verified risk penalty
    active_verified_risks = data["risk_records"].loc[
        data["risk_records"]["verification_status"].eq("Verified")
        & data["risk_records"]["record_status"].eq("Active")
    ].copy()
    active_verified_risks["risk_penalty"] = active_verified_risks["severity"].map(
        RISK_PENALTIES
    )
    risk_penalties = active_verified_risks.groupby("creator_id")["risk_penalty"].max()
    major_risk_ids = set(
        active_verified_risks.query("severity == 'High'")["creator_id"]
    )
    creators["risk_penalty"] = creators["creator_id"].map(risk_penalties).fillna(0)

    # Hard business filters
    if campaign["risk_tolerance"] == "Low":
        creators = creators.loc[~creators["creator_id"].isin(major_risk_ids)].copy()
    if campaign["brand_experience_preference"] == "Required":
        creators = creators.loc[
            creators["relevant_verified_brand_count"].gt(0)
        ].copy()

    component_columns = [
        "industry_points",
        "tag_points",
        "brand_points",
        "completeness_points",
    ]
    creators["match_score"] = (
        creators[component_columns].sum(axis=1) - creators["risk_penalty"]
    ).clip(lower=0).round(1)

    creators = creators.loc[creators["match_score"].ge(minimum_score)].copy()
    creators = creators.sort_values(
        [
            "match_score",
            "relevant_verified_brand_count",
            "data_completeness_score",
            "creator_id",
        ],
        ascending=[False, False, False, True],
    ).head(top_n)
    creators.insert(0, "recommendation_rank", range(1, len(creators) + 1))
    creators["risk_flag"] = creators["risk_penalty"].map(
        lambda penalty: "Risk penalty applied" if penalty else "No active verified risk penalty"
    )
    creators["why_recommended"] = creators.apply(build_explanation, axis=1)

    display_columns = [
        "recommendation_rank",
        "creator_code",
        "creator_name",
        "primary_category",
        "match_score",
        "industry_points",
        "tag_points",
        "brand_points",
        "data_completeness_score",
        "completeness_points",
        "risk_penalty",
        "matched_tags",
        "relevant_brands",
        "risk_flag",
        "why_recommended",
    ]
    return creators[display_columns].reset_index(drop=True)


def print_recommendations(recommendations: pd.DataFrame) -> None:
    if recommendations.empty:
        print("No creators met the minimum score and eligibility rules.")
        return

    for row in recommendations.itertuples(index=False):
        print(f"#{row.recommendation_rank} {row.creator_name} ({row.creator_code})")
        print(f"Match Score: {row.match_score:.1f}/100")
        for reason in row.why_recommended:
            print(f"  - {reason}")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rank creators for one campaign")
    parser.add_argument("--campaign-id", type=int, default=1)
    parser.add_argument("--top-n", type=int, default=5)
    parser.add_argument("--minimum-score", type=float, default=50.0)
    args = parser.parse_args()

    result = match_creators(
        campaign_id=args.campaign_id,
        top_n=args.top_n,
        minimum_score=args.minimum_score,
    )
    print_recommendations(result)
