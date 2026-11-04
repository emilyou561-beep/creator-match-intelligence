-- Change this one value to test another campaign (1 to 5).
WITH parameters AS (
    SELECT 1 AS campaign_id, 50.0 AS minimum_score
),
selected_campaign AS (
    SELECT c.*
    FROM campaigns AS c
    JOIN parameters AS p ON c.campaign_id = p.campaign_id
),
tag_features AS (
    SELECT
        c.creator_id,
        sc.campaign_id,
        (SELECT COUNT(*)
         FROM campaign_tags AS cpt
         WHERE cpt.campaign_id = sc.campaign_id) AS requested_tag_count,
        (SELECT COUNT(*)
         FROM campaign_tags AS cpt
         JOIN creator_tags AS crt
           ON crt.tag_id = cpt.tag_id
          AND crt.creator_id = c.creator_id
         WHERE cpt.campaign_id = sc.campaign_id) AS matched_tag_count
    FROM creators AS c
    CROSS JOIN selected_campaign AS sc
),
brand_features AS (
    SELECT
        c.creator_id,
        sc.campaign_id,
        COUNT(bc.collaboration_id) AS relevant_verified_brand_count
    FROM creators AS c
    CROSS JOIN selected_campaign AS sc
    LEFT JOIN brand_collaborations AS bc
      ON bc.creator_id = c.creator_id
     AND bc.verified = 1
     AND (
          (sc.target_category = 'Beauty'    AND bc.brand_industry IN ('Beauty','Skincare'))
       OR (sc.target_category = 'Fashion'   AND bc.brand_industry = 'Fashion')
       OR (sc.target_category = 'Fitness'   AND bc.brand_industry IN ('Fitness','Wellness'))
       OR (sc.target_category = 'Lifestyle' AND bc.brand_industry IN ('Lifestyle','Wellness','Home'))
       OR (sc.target_category = 'Tech'      AND bc.brand_industry IN ('Tech','Technology'))
     )
    GROUP BY c.creator_id, sc.campaign_id
),
risk_features AS (
    SELECT
        c.creator_id,
        COALESCE(MAX(
            CASE
                WHEN rr.verification_status = 'Verified'
                 AND rr.record_status = 'Active'
                 AND rr.severity = 'High'   THEN 30
                WHEN rr.verification_status = 'Verified'
                 AND rr.record_status = 'Active'
                 AND rr.severity = 'Medium' THEN 15
                WHEN rr.verification_status = 'Verified'
                 AND rr.record_status = 'Active'
                 AND rr.severity = 'Low'    THEN 5
                ELSE 0
            END
        ), 0) AS risk_penalty,
        COALESCE(MAX(
            CASE
                WHEN rr.verification_status = 'Verified'
                 AND rr.record_status = 'Active'
                 AND rr.severity = 'High' THEN 1
                ELSE 0
            END
        ), 0) AS has_major_verified_active_risk
    FROM creators AS c
    LEFT JOIN risk_records AS rr ON c.creator_id = rr.creator_id
    GROUP BY c.creator_id
),
creator_features AS (
    SELECT
        c.creator_id,
        c.creator_code,
        c.creator_name,
        c.primary_category,
        c.data_completeness_score,
        sc.campaign_id,
        sc.target_category,
        sc.brand_experience_preference,
        sc.risk_tolerance,
        tf.requested_tag_count,
        tf.matched_tag_count,
        bf.relevant_verified_brand_count,
        rf.risk_penalty,
        rf.has_major_verified_active_risk
    FROM creators AS c
    CROSS JOIN selected_campaign AS sc
    JOIN tag_features AS tf
      ON tf.creator_id = c.creator_id
     AND tf.campaign_id = sc.campaign_id
    JOIN brand_features AS bf
      ON bf.creator_id = c.creator_id
     AND bf.campaign_id = sc.campaign_id
    JOIN risk_features AS rf
      ON rf.creator_id = c.creator_id
    WHERE c.profile_status = 'Active'
      AND NOT (
          sc.risk_tolerance = 'Low'
          AND rf.has_major_verified_active_risk = 1
      )
      AND (
          sc.brand_experience_preference <> 'Required'
          OR bf.relevant_verified_brand_count > 0
      )
),
score_components AS (
    SELECT
        *,
        CASE WHEN primary_category = target_category THEN 30.0 ELSE 0.0 END
            AS industry_points,
        CASE
            WHEN requested_tag_count = 0 THEN 25.0
            ELSE 25.0 * matched_tag_count / requested_tag_count
        END AS tag_points,
        CASE
            WHEN brand_experience_preference = 'Not Important' THEN 25.0
            WHEN relevant_verified_brand_count > 0 THEN 25.0
            ELSE 0.0
        END AS brand_points,
        20.0 * data_completeness_score / 100.0 AS completeness_points
    FROM creator_features
),
scored AS (
    SELECT
        *,
        ROUND(MAX(
            0.0,
            industry_points
            + tag_points
            + brand_points
            + completeness_points
            - risk_penalty
        ), 1) AS match_score
    FROM score_components
),
qualified AS (
    SELECT s.*
    FROM scored AS s
    CROSS JOIN parameters AS p
    WHERE s.match_score >= p.minimum_score
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            ORDER BY
                match_score DESC,
                relevant_verified_brand_count DESC,
                data_completeness_score DESC,
                creator_id
        ) AS recommendation_rank
    FROM qualified
)
SELECT
    recommendation_rank,
    creator_code,
    creator_name,
    match_score,
    industry_points,
    ROUND(tag_points, 1) AS tag_points,
    brand_points,
    ROUND(completeness_points, 1) AS completeness_points,
    risk_penalty,
    matched_tag_count || '/' || requested_tag_count AS tag_match,
    relevant_verified_brand_count,
    CASE
        WHEN risk_penalty = 0 THEN 'No active verified risk penalty'
        ELSE 'Active verified risk penalty applied'
    END AS risk_flag
FROM ranked
WHERE recommendation_rank <= 5
ORDER BY recommendation_rank;
