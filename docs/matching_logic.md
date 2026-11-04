# Matching logic

The MVP ranks active creators using fixed, auditable components. It does not use machine learning or an LLM.

## Score components

| Component | Maximum | Rule |
|---|---:|---|
| Industry match | 30 | Exact match between creator primary category and campaign target category |
| Tag match | 25 | Matched campaign tags divided by requested campaign tags |
| Relevant brand experience | 25 | At least one verified collaboration in a related brand industry |
| Data completeness | 20 | Creator completeness percentage multiplied by 20% |
| Verified active risk | -30 | Highest applicable active, verified risk penalty |

If a campaign marks brand experience as `Not Important`, every eligible creator
receives the neutral 25 brand points, so that criterion does not change ranking.
Likewise, a campaign with no requested tags receives neutral tag points rather
than being penalized for missing requirements that do not exist.

The displayed score is bounded at a minimum of zero.
Only creators scoring at least 50 are displayed. The tool returns up to five
qualified recommendations rather than filling empty positions with clearly
irrelevant creators.

```text
Match Score = Industry Points
            + Tag Points
            + Brand Points
            + Completeness Points
            - Risk Penalty
```

## Eligibility filters

1. Only creators with `profile_status = Active` are eligible.
2. A Low-risk campaign excludes creators with an active, verified, High-severity risk.
3. A campaign with Required brand experience excludes creators without a verified, relevant collaboration.
4. Category and tags are ranking signals, not hard filters, so the system can return alternatives when coverage is limited.
5. Candidates below the 50-point minimum quality threshold are not displayed.

## Brand-industry mapping

The sample collaboration industries are mapped transparently:

- Beauty: Beauty, Skincare
- Fashion: Fashion
- Fitness: Fitness, Wellness
- Lifestyle: Lifestyle, Wellness, Home
- Tech: Tech, Technology

This mapping is intentionally small and explicit for the MVP. A future version can move it into a reference table.

## Risk policy

- Verified + Active + High: 30-point penalty
- Verified + Active + Medium: 15-point penalty
- Verified + Active + Low: 5-point penalty
- Resolved, Unverified, or Disputed: no automatic score penalty; still available for human review

When several risk records exist, the MVP uses the highest applicable penalty rather than adding every record together. This avoids double-punishing a creator while keeping the most important warning visible.

## Important interpretation

“No active verified risk penalty” means only that the current synthetic database produced no automatic penalty. It does not mean the creator has no real-world risk.
