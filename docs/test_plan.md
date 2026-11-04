# Test plan

The MVP is tested at three levels: expected campaign rankings, business-rule edge cases, and SQL vs. pandas parity.

| Test area | Scenario | Expected behavior |
|---|---|---|
| Beauty | Sensitive-skin serum | CR001 then CR004 |
| Lifestyle | Home wellness routine | CR002 then CR006 |
| Fashion | Sustainable collection | CR003; risk penalty remains visible |
| Tech | Smart-home device | CR007 only because brand experience is required |
| Fitness | Outdoor running | CR009 then CR005 |
| Major risk | Low-risk Fashion campaign | CR008 is excluded |
| Risk penalty | Medium-risk Fashion campaign | CR008 remains with a 30-point penalty |
| Brand verification | Required Beauty experience | CR010's unverified collaboration does not qualify |
| Missing data | CR010 has no market | Scoring completes without null scores or errors |
| Quality threshold | Minimum score 50 | Every displayed result scores at least 50 |
| Explainability | Score reconciliation | Components reproduce the displayed total |
| Consistency | SQL versus pandas | All five stored Campaign rankings and scores match |
| AI guardrail | Invalid schema values | Pydantic rejects them before matching |

Run from the project directory:

```bash
python3 -m pytest -q
```

These tests use synthetic local data and do not call an external API.
