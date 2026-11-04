-- Creator category distribution
SELECT
    primary_category,
    COUNT(*) AS creator_count
FROM creators
GROUP BY primary_category
ORDER BY creator_count DESC, primary_category;

-- Top tags by unique creator coverage
SELECT
    t.tag_name,
    COUNT(DISTINCT ct.creator_id) AS creator_count
FROM creator_tags AS ct
JOIN tags AS t ON ct.tag_id = t.tag_id
GROUP BY t.tag_id, t.tag_name
ORDER BY creator_count DESC, t.tag_name
LIMIT 10;

-- Verified collaboration coverage by creator category
WITH verified_creators AS (
    SELECT DISTINCT creator_id
    FROM brand_collaborations
    WHERE verified = 1
)
SELECT
    c.primary_category,
    COUNT(*) AS creator_count,
    SUM(CASE WHEN vc.creator_id IS NOT NULL THEN 1 ELSE 0 END)
        AS creators_with_verified_collaboration,
    ROUND(
        100.0 * SUM(CASE WHEN vc.creator_id IS NOT NULL THEN 1 ELSE 0 END)
        / COUNT(*),
        1
    ) AS coverage_rate
FROM creators AS c
LEFT JOIN verified_creators AS vc ON c.creator_id = vc.creator_id
GROUP BY c.primary_category
ORDER BY coverage_rate DESC, c.primary_category;

-- Missing-data rates in the creator profile table
SELECT
    ROUND(100.0 * SUM(CASE WHEN market IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1)
        AS market_missing_rate,
    ROUND(100.0 * SUM(CASE WHEN profile_summary IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1)
        AS profile_summary_missing_rate,
    ROUND(100.0 * SUM(CASE WHEN primary_category IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1)
        AS category_missing_rate,
    ROUND(100.0 * SUM(CASE WHEN data_completeness_score IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1)
        AS completeness_missing_rate
FROM creators;

-- Risk-record distribution
SELECT
    severity,
    COUNT(*) AS risk_record_count
FROM risk_records
GROUP BY severity
ORDER BY CASE severity WHEN 'Low' THEN 1 WHEN 'Medium' THEN 2 WHEN 'High' THEN 3 END;
