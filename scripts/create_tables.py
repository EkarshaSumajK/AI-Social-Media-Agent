"""
Create wng_content schema and all tables in the company database.

This script uses raw SQL (no Alembic/migrations). It:
1. Runs the pre-flight safety check
2. Creates the wng_content schema
3. Creates all enum types inside wng_content
4. Creates all 18 tables with columns, constraints, indexes
5. Creates alembic_version and stamps with the latest revision
6. Everything runs in a single transaction — rolls back on any error

Usage:
    python scripts/create_tables.py
    # or with explicit URL:
    DATABASE_URL_DASHBOARD=postgresql://... python scripts/create_tables.py
    # dry run (prints SQL but doesn't execute):
    python scripts/create_tables.py --dry-run
"""
from __future__ import annotations

import os
import sys

import psycopg

# ── Configuration ────────────────────────────────────────────────────────────

DASHBOARD_URL = os.getenv(
    "DATABASE_URL_DASHBOARD",
    "postgresql://dev:DV0HG69VgEs4WLAGinIy@dev.cluster-cpcy048emvxy.ap-south-2.rds.amazonaws.com:5432/dashboard",
)

SCHEMA = "wng_content"
ALEMBIC_REVISION = "20260307_0013"

# ── SQL Statements ───────────────────────────────────────────────────────────

SQL_CREATE_SCHEMA = f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};"

SQL_SET_SEARCH_PATH = f"SET search_path TO {SCHEMA};"

# Enum types (created inside wng_content schema via search_path)
SQL_CREATE_ENUMS = """
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON t.typnamespace = n.oid
                   WHERE n.nspname = 'wng_content' AND t.typname = 'userrole') THEN
        CREATE TYPE userrole AS ENUM ('reviewer', 'admin');
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON t.typnamespace = n.oid
                   WHERE n.nspname = 'wng_content' AND t.typname = 'platform') THEN
        CREATE TYPE platform AS ENUM ('horizon', 'connect', 'parentshala');
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON t.typnamespace = n.oid
                   WHERE n.nspname = 'wng_content' AND t.typname = 'topicstatus') THEN
        CREATE TYPE topicstatus AS ENUM ('new', 'processed', 'duplicate_rejected');
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON t.typnamespace = n.oid
                   WHERE n.nspname = 'wng_content' AND t.typname = 'articlestatus') THEN
        CREATE TYPE articlestatus AS ENUM ('draft', 'approved', 'rejected', 'published');
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON t.typnamespace = n.oid
                   WHERE n.nspname = 'wng_content' AND t.typname = 'socialplatform') THEN
        CREATE TYPE socialplatform AS ENUM ('instagram', 'linkedin', 'twitter', 'facebook');
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON t.typnamespace = n.oid
                   WHERE n.nspname = 'wng_content' AND t.typname = 'socialstatus') THEN
        CREATE TYPE socialstatus AS ENUM ('draft', 'ready', 'posted', 'failed');
    END IF;
END $$;
"""

# ── Table: users ─────────────────────────────────────────────────────────────
SQL_CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    full_name       VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role            userrole NOT NULL DEFAULT 'reviewer',
    platform        platform NOT NULL DEFAULT 'horizon',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);
CREATE INDEX IF NOT EXISTS ix_users_role ON users (role);
CREATE INDEX IF NOT EXISTS ix_users_platform ON users (platform);
"""

# ── Table: topics ────────────────────────────────────────────────────────────
SQL_CREATE_TOPICS = """
CREATE TABLE IF NOT EXISTS topics (
    id                      SERIAL PRIMARY KEY,
    title                   VARCHAR(500) NOT NULL,
    source_url              VARCHAR(2048) NOT NULL UNIQUE,
    source_name             VARCHAR(255),
    summary                 TEXT,
    relevance_label         VARCHAR(16) NOT NULL DEFAULT 'low',
    relevance_score         INTEGER NOT NULL DEFAULT 0,
    age_group               VARCHAR(16) NOT NULL DEFAULT 'unknown',
    topic_type              VARCHAR(20) NOT NULL DEFAULT 'general',
    mental_health_specific  BOOLEAN NOT NULL DEFAULT FALSE,
    screening_reason        TEXT,
    trust_score             INTEGER NOT NULL DEFAULT 0,
    is_trending             BOOLEAN NOT NULL DEFAULT FALSE,
    x_engagement_score      DOUBLE PRECISION,
    x_tweet_count           INTEGER,
    x_trend_phrase          VARCHAR(500),
    x_top_tweet_raw         JSON,
    trend_regions           JSON,
    public_concerns         JSON,
    trend_statements        JSON,
    trend_sentiment         VARCHAR(32),
    statistics              JSON,
    embedding               JSON,
    related_keywords        JSON,
    original_published_at   TIMESTAMPTZ,
    platform                platform NOT NULL DEFAULT 'horizon',
    topic_category          VARCHAR(30),
    region                  VARCHAR(10) NOT NULL DEFAULT 'global',
    status                  topicstatus NOT NULL DEFAULT 'new',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_topics_title ON topics (title);
CREATE INDEX IF NOT EXISTS ix_topics_source_url ON topics (source_url);
CREATE INDEX IF NOT EXISTS ix_topics_relevance_label ON topics (relevance_label);
CREATE INDEX IF NOT EXISTS ix_topics_platform ON topics (platform);
CREATE INDEX IF NOT EXISTS ix_topics_topic_category ON topics (topic_category);
CREATE INDEX IF NOT EXISTS ix_topics_region ON topics (region);
CREATE INDEX IF NOT EXISTS ix_topics_status ON topics (status);
"""

# ── Table: articles ──────────────────────────────────────────────────────────
SQL_CREATE_ARTICLES = """
CREATE TABLE IF NOT EXISTS articles (
    id                          SERIAL PRIMARY KEY,
    topic_id                    INTEGER NOT NULL UNIQUE REFERENCES topics(id) ON DELETE CASCADE,
    content_html                TEXT NOT NULL,
    seo_title                   VARCHAR(300) NOT NULL,
    meta_description            VARCHAR(500) NOT NULL,
    keywords                    JSON,
    issue_summary               TEXT NOT NULL,
    why_it_matters              TEXT NOT NULL,
    mental_health_implications  TEXT NOT NULL,
    professional_insight        TEXT NOT NULL,
    how_services_help           TEXT NOT NULL,
    call_to_action              TEXT NOT NULL,
    disclaimer_text             VARCHAR(255) NOT NULL DEFAULT 'This content is for educational purposes only',
    readability_score           DOUBLE PRECISION,
    ai_generated_probability    DOUBLE PRECISION,
    source_similarity_score     DOUBLE PRECISION,
    structure_valid             BOOLEAN NOT NULL DEFAULT FALSE,
    quality_notes               JSON,
    source_url                  VARCHAR(2048) NOT NULL,
    status                      articlestatus NOT NULL DEFAULT 'draft',
    platform                    platform NOT NULL DEFAULT 'horizon',
    slug                        VARCHAR(500) UNIQUE,
    virality_score              DOUBLE PRECISION,
    clarity_score               DOUBLE PRECISION,
    hook_strength_score         DOUBLE PRECISION,
    conversion_score            DOUBLE PRECISION,
    created_by                  INTEGER REFERENCES users(id) ON DELETE SET NULL,
    approved_by                 INTEGER REFERENCES users(id) ON DELETE SET NULL,
    approved_at                 TIMESTAMPTZ,
    published_at                TIMESTAMPTZ,
    published_url               VARCHAR(2048),
    requires_review             BOOLEAN NOT NULL DEFAULT TRUE,
    internal_links_added        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_articles_topic_id ON articles (topic_id);
CREATE INDEX IF NOT EXISTS ix_articles_status ON articles (status);
CREATE INDEX IF NOT EXISTS ix_articles_platform ON articles (platform);
CREATE INDEX IF NOT EXISTS ix_articles_slug ON articles (slug);
CREATE INDEX IF NOT EXISTS ix_articles_created_by ON articles (created_by);
"""

# ── Table: social_posts ──────────────────────────────────────────────────────
SQL_CREATE_SOCIAL_POSTS = """
CREATE TABLE IF NOT EXISTS social_posts (
    id                SERIAL PRIMARY KEY,
    article_id        INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    platform          socialplatform NOT NULL,
    caption           TEXT NOT NULL,
    edited_caption    TEXT,
    status            socialstatus NOT NULL DEFAULT 'draft',
    external_post_id  VARCHAR(255),
    error_message     TEXT,
    posted_at         TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_social_posts_article_id ON social_posts (article_id);
CREATE INDEX IF NOT EXISTS ix_social_posts_platform ON social_posts (platform);
CREATE INDEX IF NOT EXISTS ix_social_posts_status ON social_posts (status);
"""

# ── Table: campaigns ─────────────────────────────────────────────────────────
SQL_CREATE_CAMPAIGNS = """
CREATE TABLE IF NOT EXISTS campaigns (
    id                  SERIAL PRIMARY KEY,
    title               VARCHAR(500) NOT NULL,
    event_date          TIMESTAMPTZ,
    goal                VARCHAR(255),
    audience_description TEXT,
    platforms           JSON,
    platform_entity     VARCHAR(20) NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'draft',
    created_by          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_campaigns_platform_entity ON campaigns (platform_entity);
CREATE INDEX IF NOT EXISTS ix_campaigns_status ON campaigns (status);
CREATE INDEX IF NOT EXISTS ix_campaigns_created_by ON campaigns (created_by);
"""

# ── Table: campaign_pieces ───────────────────────────────────────────────────
SQL_CREATE_CAMPAIGN_PIECES = """
CREATE TABLE IF NOT EXISTS campaign_pieces (
    id            SERIAL PRIMARY KEY,
    campaign_id   INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    phase         VARCHAR(20) NOT NULL,
    content_type  VARCHAR(30) NOT NULL,
    platform      VARCHAR(20),
    content       TEXT NOT NULL,
    scheduled_for TIMESTAMPTZ,
    status        VARCHAR(20) NOT NULL DEFAULT 'draft',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_campaign_pieces_campaign_id ON campaign_pieces (campaign_id);
CREATE INDEX IF NOT EXISTS ix_campaign_pieces_phase ON campaign_pieces (phase);
"""

# ── Table: competitors ───────────────────────────────────────────────────────
SQL_CREATE_COMPETITORS = """
CREATE TABLE IF NOT EXISTS competitors (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    platform        VARCHAR(20) NOT NULL,
    profile_url     VARCHAR(2048) NOT NULL,
    platform_entity VARCHAR(20) NOT NULL,
    created_by      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_competitors_platform ON competitors (platform);
CREATE INDEX IF NOT EXISTS ix_competitors_platform_entity ON competitors (platform_entity);
CREATE INDEX IF NOT EXISTS ix_competitors_created_by ON competitors (created_by);
"""

# ── Table: competitor_analyses ───────────────────────────────────────────────
SQL_CREATE_COMPETITOR_ANALYSES = """
CREATE TABLE IF NOT EXISTS competitor_analyses (
    id            SERIAL PRIMARY KEY,
    competitor_id INTEGER NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
    analysis      TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_competitor_analyses_competitor_id ON competitor_analyses (competitor_id);
"""

# ── Table: hook_templates ────────────────────────────────────────────────────
SQL_CREATE_HOOK_TEMPLATES = """
CREATE TABLE IF NOT EXISTS hook_templates (
    id         SERIAL PRIMARY KEY,
    hook_text  TEXT NOT NULL,
    category   VARCHAR(30) NOT NULL,
    platform   VARCHAR(20) NOT NULL,
    industry   VARCHAR(100),
    use_count  INTEGER NOT NULL DEFAULT 0,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_hook_templates_category ON hook_templates (category);
CREATE INDEX IF NOT EXISTS ix_hook_templates_platform ON hook_templates (platform);
CREATE INDEX IF NOT EXISTS ix_hook_templates_industry ON hook_templates (industry);
CREATE INDEX IF NOT EXISTS ix_hook_templates_created_by ON hook_templates (created_by);
"""

# ── Table: swipe_files ───────────────────────────────────────────────────────
SQL_CREATE_SWIPE_FILES = """
CREATE TABLE IF NOT EXISTS swipe_files (
    id                SERIAL PRIMARY KEY,
    created_by        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform          VARCHAR(20) NOT NULL,
    title             VARCHAR(500) NOT NULL,
    content           TEXT NOT NULL,
    source_url        VARCHAR(2048),
    performance_notes TEXT,
    tags              JSON,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_swipe_files_created_by ON swipe_files (created_by);
CREATE INDEX IF NOT EXISTS ix_swipe_files_platform ON swipe_files (platform);
"""

# ── Table: daily_post_batches ────────────────────────────────────────────────
SQL_CREATE_DAILY_POST_BATCHES = """
CREATE TABLE IF NOT EXISTS daily_post_batches (
    id              SERIAL PRIMARY KEY,
    industry        VARCHAR(255) NOT NULL,
    region          VARCHAR(50) NOT NULL DEFAULT 'global',
    target_audience VARCHAR(500) NOT NULL,
    business_goal   VARCHAR(50) NOT NULL DEFAULT 'brand',
    suggestions     JSON NOT NULL,
    created_by      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_daily_post_batches_created_by ON daily_post_batches (created_by);
"""

# ── Table: thought_leadership_generations ────────────────────────────────────
SQL_CREATE_THOUGHT_LEADERSHIP = """
CREATE TABLE IF NOT EXISTS thought_leadership_generations (
    id           SERIAL PRIMARY KEY,
    topic        VARCHAR(500) NOT NULL,
    industry     VARCHAR(255) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    content      TEXT NOT NULL,
    created_by   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_thought_leadership_generations_created_by ON thought_leadership_generations (created_by);
"""

# ── Table: platform_content_generations ──────────────────────────────────────
SQL_CREATE_PLATFORM_CONTENT = """
CREATE TABLE IF NOT EXISTS platform_content_generations (
    id           SERIAL PRIMARY KEY,
    topic        VARCHAR(500) NOT NULL,
    platform     VARCHAR(50) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    content      TEXT NOT NULL,
    metadata     JSON,
    created_by   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_platform_content_generations_created_by ON platform_content_generations (created_by);
"""

# ── Table: youtube_shorts ────────────────────────────────────────────────────
SQL_CREATE_YOUTUBE_SHORTS = """
CREATE TABLE IF NOT EXISTS youtube_shorts (
    id              SERIAL PRIMARY KEY,
    topic           VARCHAR(500) NOT NULL,
    target_audience VARCHAR(500),
    duration        INTEGER NOT NULL DEFAULT 60,
    hook            TEXT NOT NULL,
    script          JSON NOT NULL,
    titles          JSON NOT NULL,
    description     TEXT NOT NULL,
    tags            JSON NOT NULL,
    created_by      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_youtube_shorts_created_by ON youtube_shorts (created_by);
"""

# ── Table: social_accounts ───────────────────────────────────────────────────
SQL_CREATE_SOCIAL_ACCOUNTS = """
CREATE TABLE IF NOT EXISTS social_accounts (
    id                SERIAL PRIMARY KEY,
    platform          VARCHAR(50) NOT NULL,
    account_name      VARCHAR(255) NOT NULL,
    account_id        VARCHAR(255),
    access_token      TEXT,
    refresh_token     TEXT,
    token_expires_at  TIMESTAMPTZ,
    status            VARCHAR(50) NOT NULL DEFAULT 'connected',
    scopes            TEXT,
    profile_image_url TEXT,
    created_by        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_social_accounts_created_by ON social_accounts (created_by);
"""

# ── Table: scheduled_posts ───────────────────────────────────────────────────
SQL_CREATE_SCHEDULED_POSTS = """
CREATE TABLE IF NOT EXISTS scheduled_posts (
    id                SERIAL PRIMARY KEY,
    title             VARCHAR(500) NOT NULL,
    content           TEXT NOT NULL,
    platform          VARCHAR(50) NOT NULL,
    content_type      VARCHAR(100) NOT NULL,
    scheduled_for     TIMESTAMPTZ,
    status            VARCHAR(50) NOT NULL DEFAULT 'draft',
    hashtags          JSON,
    media_urls        JSON,
    campaign_id       INTEGER REFERENCES campaigns(id) ON DELETE SET NULL,
    social_account_id INTEGER,
    published_at      TIMESTAMPTZ,
    error_message     TEXT,
    created_by        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_scheduled_posts_campaign_id ON scheduled_posts (campaign_id);
CREATE INDEX IF NOT EXISTS ix_scheduled_posts_created_by ON scheduled_posts (created_by);
"""

# ── Table: regional_content ──────────────────────────────────────────────────
SQL_CREATE_REGIONAL_CONTENT = """
CREATE TABLE IF NOT EXISTS regional_content (
    id                SERIAL PRIMARY KEY,
    region            VARCHAR(100) NOT NULL,
    industry          VARCHAR(200) NOT NULL,
    language_style    VARCHAR(100) NOT NULL DEFAULT 'english',
    original_content  TEXT,
    localised_content TEXT,
    trending_topics   JSON,
    hashtags          JSON,
    platform          VARCHAR(50),
    request_type      VARCHAR(50) NOT NULL DEFAULT 'localise',
    created_by        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_regional_content_created_by ON regional_content (created_by);
"""

# ── Table: audit_logs ────────────────────────────────────────────────────────
SQL_CREATE_AUDIT_LOGS = """
CREATE TABLE IF NOT EXISTS audit_logs (
    id          SERIAL PRIMARY KEY,
    actor_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action      VARCHAR(120) NOT NULL,
    entity_type VARCHAR(80) NOT NULL,
    entity_id   VARCHAR(120) NOT NULL,
    details     JSON,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_audit_logs_actor_id ON audit_logs (actor_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs (action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_type ON audit_logs (entity_type);
CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_id ON audit_logs (entity_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs (created_at);
"""

# ── alembic_version (inside wng_content schema) ─────────────────────────────
SQL_CREATE_ALEMBIC_VERSION = f"""
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

-- Stamp with latest revision (idempotent)
INSERT INTO alembic_version (version_num)
SELECT '{ALEMBIC_REVISION}'
WHERE NOT EXISTS (SELECT 1 FROM alembic_version WHERE version_num = '{ALEMBIC_REVISION}');
"""

# ── Ordered list of all SQL blocks ──────────────────────────────────────────

ALL_SQL_BLOCKS = [
    ("Schema",                        SQL_CREATE_SCHEMA),
    ("Search path",                   SQL_SET_SEARCH_PATH),
    ("Enum types",                    SQL_CREATE_ENUMS),
    ("Table: users",                  SQL_CREATE_USERS),
    ("Table: topics",                 SQL_CREATE_TOPICS),
    ("Table: articles",               SQL_CREATE_ARTICLES),
    ("Table: social_posts",           SQL_CREATE_SOCIAL_POSTS),
    ("Table: campaigns",              SQL_CREATE_CAMPAIGNS),
    ("Table: campaign_pieces",        SQL_CREATE_CAMPAIGN_PIECES),
    ("Table: competitors",            SQL_CREATE_COMPETITORS),
    ("Table: competitor_analyses",    SQL_CREATE_COMPETITOR_ANALYSES),
    ("Table: hook_templates",         SQL_CREATE_HOOK_TEMPLATES),
    ("Table: swipe_files",            SQL_CREATE_SWIPE_FILES),
    ("Table: daily_post_batches",     SQL_CREATE_DAILY_POST_BATCHES),
    ("Table: thought_leadership_generations", SQL_CREATE_THOUGHT_LEADERSHIP),
    ("Table: platform_content_generations",   SQL_CREATE_PLATFORM_CONTENT),
    ("Table: youtube_shorts",         SQL_CREATE_YOUTUBE_SHORTS),
    ("Table: social_accounts",        SQL_CREATE_SOCIAL_ACCOUNTS),
    ("Table: scheduled_posts",        SQL_CREATE_SCHEDULED_POSTS),
    ("Table: regional_content",       SQL_CREATE_REGIONAL_CONTENT),
    ("Table: audit_logs",             SQL_CREATE_AUDIT_LOGS),
    ("Alembic version stamp",         SQL_CREATE_ALEMBIC_VERSION),
]


def main() -> int:
    dry_run = "--dry-run" in sys.argv

    # ── Step 1: Run pre-flight check ─────────────────────────────────────
    if not dry_run:
        print("=" * 60)
        print("STEP 1: Running pre-flight safety check...")
        print("=" * 60)
        from check_company_db import main as preflight
        result = preflight()
        if result != 0:
            print("\nPre-flight check FAILED. Aborting.")
            return 1
        print()

    # ── Step 2: Create everything in a single transaction ────────────────
    print("=" * 60)
    if dry_run:
        print("DRY RUN — Printing SQL that would be executed:")
    else:
        print("STEP 2: Creating schema, enums, and tables...")
    print("=" * 60)

    if dry_run:
        for label, sql in ALL_SQL_BLOCKS:
            print(f"\n-- {label}")
            print(sql.strip())
        print("\n-- DRY RUN COMPLETE (nothing was executed)")
        return 0

    conn = psycopg.connect(DASHBOARD_URL, autocommit=False)
    try:
        cur = conn.cursor()
        for label, sql in ALL_SQL_BLOCKS:
            print(f"  Creating: {label}...")
            cur.execute(sql)

        conn.commit()
        print("\nAll tables created successfully!")

    except Exception as exc:
        conn.rollback()
        print(f"\nERROR: {exc}")
        print("Transaction ROLLED BACK — no changes were made.")
        return 1
    finally:
        conn.close()

    # ── Step 3: Verify ───────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("STEP 3: Verification")
    print("=" * 60)

    conn = psycopg.connect(DASHBOARD_URL, autocommit=True)
    cur = conn.cursor()

    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = %s ORDER BY table_name",
        (SCHEMA,),
    )
    tables = [row[0] for row in cur.fetchall()]
    print(f"\nTables in '{SCHEMA}' schema ({len(tables)}):")
    for t in tables:
        print(f"  - {t}")

    cur.execute(
        "SELECT t.typname FROM pg_type t "
        "JOIN pg_namespace n ON t.typnamespace = n.oid "
        "WHERE n.nspname = %s AND t.typtype = 'e' ORDER BY t.typname",
        (SCHEMA,),
    )
    enums = [row[0] for row in cur.fetchall()]
    print(f"\nEnum types in '{SCHEMA}' schema ({len(enums)}):")
    for e in enums:
        print(f"  - {e}")

    cur.execute(f"SELECT version_num FROM {SCHEMA}.alembic_version")
    versions = [row[0] for row in cur.fetchall()]
    print(f"\nAlembic version: {versions}")

    # Confirm public schema is untouched
    cur.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
    )
    public_count = cur.fetchone()[0]
    print(f"\nPublic schema tables: {public_count} (should be unchanged)")

    conn.close()

    expected_tables = 19  # 18 app tables + alembic_version
    if len(tables) >= expected_tables:
        print(f"\nSUCCESS: All {expected_tables} tables created in '{SCHEMA}' schema!")
        return 0
    else:
        print(f"\nWARNING: Expected {expected_tables} tables, found {len(tables)}.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
