PRAGMA foreign_keys = ON;

CREATE TABLE creators (
    creator_id              INTEGER PRIMARY KEY,
    creator_code            TEXT NOT NULL UNIQUE,
    creator_name            TEXT NOT NULL,
    primary_category        TEXT NOT NULL
                            CHECK (primary_category IN ('Beauty','Fashion','Fitness','Lifestyle','Tech')),
    market                  TEXT,
    profile_summary         TEXT,
    data_completeness_score REAL NOT NULL
                            CHECK (data_completeness_score BETWEEN 0 AND 100),
    profile_status          TEXT NOT NULL
                            CHECK (profile_status IN ('Active','Inactive','Review')),
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL
);

CREATE TABLE tags (
    tag_id      INTEGER PRIMARY KEY,
    tag_name    TEXT NOT NULL UNIQUE,
    tag_group   TEXT NOT NULL,
    is_active   INTEGER NOT NULL CHECK (is_active IN (0, 1))
);

CREATE TABLE creator_tags (
    creator_id    INTEGER NOT NULL,
    tag_id        INTEGER NOT NULL,
    tag_relevance TEXT NOT NULL CHECK (tag_relevance IN ('Primary','Secondary')),
    verified      INTEGER CHECK (verified IN (0, 1)),
    PRIMARY KEY (creator_id, tag_id),
    FOREIGN KEY (creator_id) REFERENCES creators (creator_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags (tag_id) ON DELETE RESTRICT
);

CREATE TABLE brand_collaborations (
    collaboration_id   INTEGER PRIMARY KEY,
    creator_id          INTEGER NOT NULL,
    brand_name          TEXT NOT NULL,
    brand_industry      TEXT NOT NULL,
    collaboration_type  TEXT NOT NULL,
    collaboration_date  TEXT,
    verified             INTEGER CHECK (verified IN (0, 1)),
    evidence_source      TEXT,
    notes                TEXT,
    FOREIGN KEY (creator_id) REFERENCES creators (creator_id) ON DELETE CASCADE
);

CREATE TABLE risk_records (
    risk_id              INTEGER PRIMARY KEY,
    creator_id           INTEGER NOT NULL,
    risk_type            TEXT NOT NULL,
    risk_description     TEXT NOT NULL,
    severity             TEXT NOT NULL CHECK (severity IN ('Low','Medium','High')),
    verification_status  TEXT NOT NULL
                         CHECK (verification_status IN ('Verified','Unverified','Disputed')),
    record_status        TEXT NOT NULL CHECK (record_status IN ('Active','Resolved','Monitoring')),
    record_date          TEXT,
    evidence_source      TEXT,
    reviewed_at          TEXT,
    FOREIGN KEY (creator_id) REFERENCES creators (creator_id) ON DELETE CASCADE
);

CREATE TABLE campaigns (
    campaign_id                 INTEGER PRIMARY KEY,
    campaign_name               TEXT NOT NULL,
    product_description         TEXT,
    target_category             TEXT NOT NULL
                                CHECK (target_category IN ('Beauty','Fashion','Fitness','Lifestyle','Tech')),
    brand_experience_preference TEXT NOT NULL
                                CHECK (brand_experience_preference IN ('Required','Preferred','Not Important')),
    risk_tolerance              TEXT NOT NULL CHECK (risk_tolerance IN ('Low','Medium','High')),
    created_at                  TEXT NOT NULL
);

CREATE TABLE campaign_tags (
    campaign_id INTEGER NOT NULL,
    tag_id      INTEGER NOT NULL,
    importance  TEXT NOT NULL CHECK (importance IN ('Required','Preferred')),
    PRIMARY KEY (campaign_id, tag_id),
    FOREIGN KEY (campaign_id) REFERENCES campaigns (campaign_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags (tag_id) ON DELETE RESTRICT
);

CREATE INDEX idx_creators_category
    ON creators (primary_category);

CREATE INDEX idx_creator_tags_tag
    ON creator_tags (tag_id);

CREATE INDEX idx_collaborations_creator_industry
    ON brand_collaborations (creator_id, brand_industry);

CREATE INDEX idx_risks_creator_status
    ON risk_records (creator_id, verification_status, severity, record_status);

CREATE INDEX idx_campaign_tags_tag
    ON campaign_tags (tag_id);
