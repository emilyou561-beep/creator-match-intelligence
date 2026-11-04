# Optional: parsing a campaign description

The LLM has one bounded responsibility: convert campaign text into four validated fields.

```text
Campaign description
        ↓
OpenAI Structured Outputs
        ↓
Pydantic validation
        ↓
target_category, preferred_tags,
brand_experience_preference, risk_tolerance
        ↓
Existing deterministic pandas matcher
```

The model never receives creator profiles and never chooses or ranks creators.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="your-key"
```

Do not save an API key in source code or commit it to Git.

## Run

```bash
python3 python/campaign_parser.py \
  --description "We need US skincare creators for a sensitive-skin serum. Previous beauty partnerships are preferred and there must be no major controversies."
```

The model defaults to `gpt-5.6`. Override it without changing code by setting
`OPENAI_MODEL` or passing `--model`.

## Guardrails

- Category, brand preference, and risk tolerance are restricted enums.
- Tags are normalized against the active tags stored in SQLite.
- Unknown tags are discarded before matching.
- The output may contain at most five tags and five interpretation notes.
- Extra fields are rejected by Pydantic.
- Empty campaign descriptions fail before an API request.
- Missing API configuration produces a clear error.
