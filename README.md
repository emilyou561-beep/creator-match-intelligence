# Creator Match Intelligence

Give it a campaign brief (category, tags, how much brand experience matters, how much risk is OK) and it returns up to five creators that fit, with the score broken down so you can see why each one is on the list. It narrows the list and flags risks; the final call is still a person's.

![Python](https://img.shields.io/badge/Python-3.12-00274C?style=flat-square) ![SQLite](https://img.shields.io/badge/SQLite-7%20tables-00274C?style=flat-square) ![Streamlit](https://img.shields.io/badge/Streamlit-app-00274C?style=flat-square) ![tests](https://img.shields.io/badge/tests-pytest-00274C?style=flat-square)

## How the score works

| Part | Points |
|---|---:|
| Category match | 30 |
| Tag overlap | 25 |
| Verified brand experience in a related industry | 25 |
| Profile completeness | 20 |
| Active, verified risk record | up to -30 |

A few rules run before scoring: inactive creators are dropped, low-risk campaigns drop anyone with a verified high-severity issue, and "brand experience required" drops anyone without a verified collab. Anything under 50 points isn't shown, so a weak campaign can return fewer than five names instead of padding the list.

Full rules are in [docs/matching_logic.md](docs/matching_logic.md).

The same logic is written twice, once in SQL ([sql/04_matching_query.sql](sql/04_matching_query.sql)) and once in pandas ([python/matcher.py](python/matcher.py)), and the tests check that both give the same rankings.

## Run it

```bash
pip install -r requirements.txt
python3 scripts/setup_database.py
streamlit run app/app.py
```

There's also an optional mode that turns a free-text brief into the structured fields using the OpenAI API. It only fills in the four campaign fields and never sees creator data. It's off unless `OPENAI_API_KEY` is set. See [docs/ai_requirement_extraction.md](docs/ai_requirement_extraction.md).

## Tests

```bash
python3 -m pytest -q
```

Covers the expected ranking for each sample campaign, the edge cases (risk exclusion vs. penalty, unverified collabs, missing fields), and SQL/pandas parity. Details in [docs/test_plan.md](docs/test_plan.md).

## What's where

```text
sample_data/   7 CSVs, one per table
sql/           schema, basic queries, data-quality checks, matching query, analytics
scripts/       builds the SQLite database from the CSVs
python/        matcher, analytics, optional brief parser
app/           Streamlit app
tests/         pytest
docs/          scoring rules, data dictionary, test plan, findings
```

## About the data

Every creator, brand, campaign and risk record here is made up. The point is the workflow, not the numbers. More in [docs/data_privacy.md](docs/data_privacy.md) and [docs/data_dictionary.md](docs/data_dictionary.md).
