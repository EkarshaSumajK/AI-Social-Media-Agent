"""
Pre-flight safety check for company database migration.

Connects to the company DB and checks for conflicts before creating
our wng_content schema and tables.

Usage:
    python scripts/check_company_db.py
    # or with explicit URL:
    DATABASE_URL_DASHBOARD=postgresql://... python scripts/check_company_db.py
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

# Our 18 tables
OUR_TABLES = [
    "users", "topics", "articles", "audit_logs", "social_posts",
    "campaigns", "campaign_pieces", "competitors", "hook_templates",
    "swipe_files", "daily_post_batches", "thought_leadership_generations",
    "platform_content_generations", "youtube_shorts", "social_accounts",
    "scheduled_posts", "regional_content", "competitor_analyses",
]

# Our 6 enum types (will be created inside wng_content schema)
OUR_ENUMS = [
    "userrole", "platform", "topicstatus", "articlestatus",
    "socialplatform", "socialstatus",
]


def main() -> int:
    print(f"Connecting to company database...")
    print(f"Target schema: {SCHEMA}")
    print()

    try:
        conn = psycopg.connect(DASHBOARD_URL, autocommit=True)
    except Exception as exc:
        print(f"FAILED to connect: {exc}")
        return 1

    cur = conn.cursor()
    issues = 0

    # ── 1. Check if wng_content schema exists ────────────────────────────
    cur.execute(
        "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s",
        (SCHEMA,),
    )
    schema_exists = cur.fetchone() is not None
    if schema_exists:
        print(f"[INFO] Schema '{SCHEMA}' already exists.")

        # Check for existing tables inside it
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = %s ORDER BY table_name",
            (SCHEMA,),
        )
        existing = [row[0] for row in cur.fetchall()]
        if existing:
            print(f"[WARN] Tables already in '{SCHEMA}' schema:")
            for t in existing:
                print(f"       - {t}")
            conflicts = set(OUR_TABLES) & set(existing)
            if conflicts:
                print(f"\n[ERROR] {len(conflicts)} of our tables already exist in '{SCHEMA}':")
                for c in sorted(conflicts):
                    print(f"        - {c}")
                issues += len(conflicts)
            else:
                print(f"  (none of our tables conflict)")
        else:
            print(f"  Schema exists but has no tables — safe to proceed.")
    else:
        print(f"[OK] Schema '{SCHEMA}' does not exist — will be created fresh.")

    # ── 2. Check enum conflicts inside wng_content schema ────────────────
    print()
    if schema_exists:
        cur.execute(
            "SELECT t.typname FROM pg_type t "
            "JOIN pg_namespace n ON t.typnamespace = n.oid "
            "WHERE n.nspname = %s AND t.typtype = 'e' "
            "ORDER BY t.typname",
            (SCHEMA,),
        )
        existing_enums = [row[0] for row in cur.fetchall()]
        if existing_enums:
            print(f"[INFO] Enum types already in '{SCHEMA}' schema:")
            for e in existing_enums:
                print(f"       - {e}")
            enum_conflicts = set(OUR_ENUMS) & set(existing_enums)
            if enum_conflicts:
                print(f"\n[ERROR] {len(enum_conflicts)} of our enums already exist in '{SCHEMA}':")
                for c in sorted(enum_conflicts):
                    print(f"        - {c}")
                issues += len(enum_conflicts)
        else:
            print(f"[OK] No enum types in '{SCHEMA}' schema.")
    else:
        print(f"[OK] Schema doesn't exist yet — no enum conflicts possible.")

    # ── 3. Show public schema summary (informational) ────────────────────
    print()
    cur.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
    )
    public_count = cur.fetchone()[0]
    print(f"[INFO] Company 'public' schema has {public_count} tables (will NOT be touched).")

    cur.execute(
        "SELECT count(*) FROM pg_type t "
        "JOIN pg_namespace n ON t.typnamespace = n.oid "
        "WHERE n.nspname = 'public' AND t.typtype = 'e'"
    )
    public_enum_count = cur.fetchone()[0]
    print(f"[INFO] Company 'public' schema has {public_enum_count} enum types (will NOT be touched).")

    # ── 4. Check alembic_version in wng_content ──────────────────────────
    print()
    if schema_exists:
        cur.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = %s AND table_name = 'alembic_version'",
            (SCHEMA,),
        )
        if cur.fetchone():
            cur.execute(f"SELECT version_num FROM {SCHEMA}.alembic_version")
            versions = [row[0] for row in cur.fetchall()]
            print(f"[WARN] alembic_version already exists in '{SCHEMA}': {versions}")
            issues += 1
        else:
            print(f"[OK] No alembic_version in '{SCHEMA}' — clean slate.")
    else:
        print(f"[OK] No alembic_version conflict (schema doesn't exist yet).")

    # ── Summary ──────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    if issues == 0:
        print("RESULT: SAFE — No conflicts detected. Ready to create tables.")
        conn.close()
        return 0
    else:
        print(f"RESULT: {issues} CONFLICT(S) FOUND — Review before proceeding.")
        conn.close()
        return 1


if __name__ == "__main__":
    sys.exit(main())
