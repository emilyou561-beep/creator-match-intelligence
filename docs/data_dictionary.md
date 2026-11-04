# Data Dictionary

The sample dataset is stored in seven normalized files under `sample_data/`.

| File | Grain | Primary key |
|---|---|---|
| `creators.csv` | One row per creator | `creator_id` |
| `tags.csv` | One row per standard tag | `tag_id` |
| `creator_tags.csv` | One row per creator-tag relationship | `creator_id + tag_id` |
| `brand_collaborations.csv` | One row per collaboration | `collaboration_id` |
| `risk_records.csv` | One row per risk record | `risk_id` |
| `campaigns.csv` | One row per test campaign | `campaign_id` |
| `campaign_tags.csv` | One row per campaign-tag requirement | `campaign_id + tag_id` |

Controlled values:

- Category: `Beauty`, `Fashion`, `Fitness`, `Lifestyle`, `Tech`
- Risk severity: `Low`, `Medium`, `High`
- Verification: `Verified`, `Unverified`, `Disputed`
- Risk status: `Active`, `Resolved`, `Monitoring`
- Campaign brand preference: `Required`, `Preferred`, `Not Important`
- Tag importance: `Required`, `Preferred`

Blank values represent unknown or unavailable information.
