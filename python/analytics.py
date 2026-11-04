"""Reusable creator-database analytics for the public demonstration dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from matcher import DEFAULT_DATABASE, load_tables


def build_analytics(database_path: Path = DEFAULT_DATABASE) -> dict[str, object]:
    data = load_tables(database_path)
    creators = data["creators"]
    creator_tags = data["creator_tags"]
    tags = data["tags"]
    collaborations = data["brand_collaborations"]
    risks = data["risk_records"]

    verified_creator_ids = set(collaborations.loc[collaborations["verified"].eq(1), "creator_id"])
    major_active_risks = risks.loc[
        risks["severity"].eq("High")
        & risks["verification_status"].eq("Verified")
        & risks["record_status"].eq("Active")
    ]

    summary = {
        "creator_count": len(creators),
        "average_completeness": round(creators["data_completeness_score"].mean(), 1),
        "verified_collaboration_coverage": round(
            creators["creator_id"].isin(verified_creator_ids).mean() * 100, 1
        ),
        "major_active_risk_count": major_active_risks["creator_id"].nunique(),
    }

    category_distribution = (
        creators.groupby("primary_category", as_index=False)
        .agg(creator_count=("creator_id", "nunique"))
        .sort_values(["creator_count", "primary_category"], ascending=[False, True])
    )

    tag_distribution = (
        creator_tags.merge(tags, on="tag_id")
        .groupby("tag_name", as_index=False)
        .agg(creator_count=("creator_id", "nunique"))
        .sort_values(["creator_count", "tag_name"], ascending=[False, True])
        .head(10)
    )

    creator_coverage = creators[["creator_id", "primary_category"]].copy()
    creator_coverage["has_verified_collaboration"] = creator_coverage["creator_id"].isin(
        verified_creator_ids
    )
    collaboration_coverage = (
        creator_coverage.groupby("primary_category", as_index=False)
        .agg(
            creator_count=("creator_id", "nunique"),
            creators_with_verified_collaboration=("has_verified_collaboration", "sum"),
        )
    )
    collaboration_coverage["coverage_rate"] = (
        collaboration_coverage["creators_with_verified_collaboration"]
        / collaboration_coverage["creator_count"]
        * 100
    ).round(1)

    missing_data = pd.DataFrame(
        {
            "field": ["Market", "Profile summary", "Primary category", "Completeness score"],
            "missing_rate": [
                creators["market"].isna().mean() * 100,
                creators["profile_summary"].isna().mean() * 100,
                creators["primary_category"].isna().mean() * 100,
                creators["data_completeness_score"].isna().mean() * 100,
            ],
        }
    )
    missing_data["missing_rate"] = missing_data["missing_rate"].round(1)

    severity_order = pd.DataFrame({"severity": ["Low", "Medium", "High"]})
    risk_distribution = severity_order.merge(
        risks.groupby("severity", as_index=False).agg(risk_record_count=("risk_id", "count")),
        on="severity",
        how="left",
    ).fillna({"risk_record_count": 0})
    risk_distribution["risk_record_count"] = risk_distribution["risk_record_count"].astype(int)

    return {
        "summary": summary,
        "category_distribution": category_distribution,
        "tag_distribution": tag_distribution,
        "collaboration_coverage": collaboration_coverage,
        "missing_data": missing_data,
        "risk_distribution": risk_distribution,
    }
