-- Query 1: JOIN creators to their tags.
SELECT
    c.creator_code,
    c.creator_name,
    c.primary_category,
    GROUP_CONCAT(t.tag_name, ', ') AS tags
FROM creators AS c
LEFT JOIN creator_tags AS ct
    ON c.creator_id = ct.creator_id
LEFT JOIN tags AS t
    ON ct.tag_id = t.tag_id
GROUP BY c.creator_id, c.creator_code, c.creator_name, c.primary_category
ORDER BY c.creator_code;

-- Query 2: Count total and verified collaborations by creator.
SELECT
    c.creator_code,
    c.creator_name,
    COUNT(bc.collaboration_id) AS collaboration_count,
    SUM(CASE WHEN bc.verified = 1 THEN 1 ELSE 0 END) AS verified_collaboration_count
FROM creators AS c
LEFT JOIN brand_collaborations AS bc
    ON c.creator_id = bc.creator_id
GROUP BY c.creator_id, c.creator_code, c.creator_name
ORDER BY verified_collaboration_count DESC, c.creator_code;

-- Query 3: Filter active, verified high-severity risk records.
SELECT
    c.creator_code,
    c.creator_name,
    rr.risk_type,
    rr.severity,
    rr.record_status
FROM risk_records AS rr
JOIN creators AS c
    ON rr.creator_id = c.creator_id
WHERE rr.verification_status = 'Verified'
  AND rr.severity = 'High'
  AND rr.record_status = 'Active';

-- Query 4: Category-level creator coverage and average completeness.
SELECT
    primary_category,
    COUNT(*) AS creator_count,
    ROUND(AVG(data_completeness_score), 1) AS average_completeness
FROM creators
GROUP BY primary_category
ORDER BY creator_count DESC, primary_category;

-- Query 5: Window function ranking creators within each category.
WITH category_ranking AS (
    SELECT
        creator_code,
        creator_name,
        primary_category,
        data_completeness_score,
        RANK() OVER (
            PARTITION BY primary_category
            ORDER BY data_completeness_score DESC
        ) AS completeness_rank
    FROM creators
)
SELECT *
FROM category_ranking
ORDER BY primary_category, completeness_rank, creator_code;
