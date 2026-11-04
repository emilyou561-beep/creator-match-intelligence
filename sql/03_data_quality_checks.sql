-- Every query should return zero rows or zero problems.

PRAGMA foreign_key_check;

SELECT creator_code, COUNT(*) AS duplicate_count
FROM creators
GROUP BY creator_code
HAVING COUNT(*) > 1;

SELECT tag_name, COUNT(*) AS duplicate_count
FROM tags
GROUP BY LOWER(TRIM(tag_name))
HAVING COUNT(*) > 1;

SELECT creator_id, creator_code, data_completeness_score
FROM creators
WHERE data_completeness_score NOT BETWEEN 0 AND 100;

SELECT creator_id, creator_code
FROM creators
WHERE TRIM(creator_name) = ''
   OR TRIM(primary_category) = '';

SELECT 'creator_tags.creator_id' AS check_name, COUNT(*) AS problem_count
FROM creator_tags AS ct
LEFT JOIN creators AS c ON ct.creator_id = c.creator_id
WHERE c.creator_id IS NULL
UNION ALL
SELECT 'creator_tags.tag_id', COUNT(*)
FROM creator_tags AS ct
LEFT JOIN tags AS t ON ct.tag_id = t.tag_id
WHERE t.tag_id IS NULL
UNION ALL
SELECT 'brand_collaborations.creator_id', COUNT(*)
FROM brand_collaborations AS bc
LEFT JOIN creators AS c ON bc.creator_id = c.creator_id
WHERE c.creator_id IS NULL
UNION ALL
SELECT 'risk_records.creator_id', COUNT(*)
FROM risk_records AS rr
LEFT JOIN creators AS c ON rr.creator_id = c.creator_id
WHERE c.creator_id IS NULL
UNION ALL
SELECT 'campaign_tags.campaign_id', COUNT(*)
FROM campaign_tags AS ct
LEFT JOIN campaigns AS c ON ct.campaign_id = c.campaign_id
WHERE c.campaign_id IS NULL
UNION ALL
SELECT 'campaign_tags.tag_id', COUNT(*)
FROM campaign_tags AS ct
LEFT JOIN tags AS t ON ct.tag_id = t.tag_id
WHERE t.tag_id IS NULL;
