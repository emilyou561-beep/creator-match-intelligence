"""Use an LLM only to extract structured campaign requirements."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from matcher import DEFAULT_DATABASE, match_creators, print_recommendations


Category = Literal["Beauty", "Fashion", "Fitness", "Lifestyle", "Tech"]
BrandPreference = Literal["Required", "Preferred", "Not Important"]
RiskTolerance = Literal["Low", "Medium", "High"]


class CampaignRequirements(BaseModel):
    """The only fields the deterministic matcher is allowed to receive."""

    model_config = ConfigDict(extra="forbid")

    target_category: Category
    preferred_tags: list[str] = Field(max_length=5)
    brand_experience_preference: BrandPreference
    risk_tolerance: RiskTolerance
    interpretation_notes: list[str] = Field(default_factory=list, max_length=5)


def available_tags(database_path: Path = DEFAULT_DATABASE) -> list[str]:
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            "SELECT tag_name FROM tags WHERE is_active = 1 ORDER BY tag_name"
        ).fetchall()
    return [row[0] for row in rows]


def parse_campaign_description(
    description: str,
    database_path: Path = DEFAULT_DATABASE,
    model: str | None = None,
) -> CampaignRequirements:
    """Parse free text with Structured Outputs, then normalize tags to the database."""
    if not description.strip():
        raise ValueError("Campaign description cannot be empty")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not configured")

    try:
        from openai import OpenAI
    except ImportError as error:
        raise RuntimeError("Install dependencies with: pip install -r requirements.txt") from error

    allowed_tags = available_tags(database_path)
    system_prompt = f"""
Extract campaign requirements for a creator-matching system.

Allowed categories: Beauty, Fashion, Fitness, Lifestyle, Tech.
Allowed tags: {', '.join(allowed_tags)}.

Rules:
- Choose exactly one closest category.
- Return at most five tags and only use tags from the allowed list.
- Brand experience is Required only when the text makes it mandatory;
  Preferred when it is desired; otherwise Not Important.
- Risk tolerance is Low for strict brand-safety or no-controversy requirements,
  Medium when unspecified, and High only when the text explicitly allows risk.
- Do not invent campaign requirements. Record ambiguity in interpretation_notes.
""".strip()

    client = OpenAI()
    response = client.responses.parse(
        model=model or os.getenv("OPENAI_MODEL", "gpt-5.6"),
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": description},
        ],
        text_format=CampaignRequirements,
    )
    parsed = response.output_parsed
    if parsed is None:
        raise RuntimeError("The model did not return parsed campaign requirements")

    canonical_tags = {tag.casefold(): tag for tag in allowed_tags}
    normalized_tags = [
        canonical_tags[tag.casefold()]
        for tag in parsed.preferred_tags
        if tag.casefold() in canonical_tags
    ]
    return parsed.model_copy(update={"preferred_tags": list(dict.fromkeys(normalized_tags))})


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse campaign text and rank creators")
    parser.add_argument("--description", required=True)
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    requirements = parse_campaign_description(args.description, model=args.model)
    print("Structured requirements:")
    print(json.dumps(requirements.model_dump(), indent=2, ensure_ascii=False))
    print("\nRecommendations:\n")
    results = match_creators(requirements=requirements.model_dump())
    print_recommendations(results)


if __name__ == "__main__":
    main()
