-- Optional bootstrap SQL. The app primarily manages schema with SQLAlchemy on startup.
-- Keep this file for DB-side extensions, defaults, and future migrations.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Minimal audit index in case table is created externally.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_logs') THEN
        CREATE INDEX IF NOT EXISTS idx_audit_logs_action_created_at ON audit_logs (action, created_at DESC);
    END IF;
END
$$;
