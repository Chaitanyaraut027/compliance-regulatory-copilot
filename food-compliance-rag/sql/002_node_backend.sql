-- ============================================================
-- Node.js Backend Schema Additions
-- Run this in the Supabase SQL Editor AFTER 001_setup.sql
-- ============================================================

-- 1. Users table
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. Compliance Audit History table
CREATE TABLE IF NOT EXISTS audit_history (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question            TEXT NOT NULL,
    compliance_area     TEXT NOT NULL,
    company_evidence    TEXT NOT NULL,
    facility_description TEXT,
    overall_status      TEXT,
    summary             TEXT,
    findings            JSONB DEFAULT '[]',
    disclaimer          TEXT,
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_history(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_history(created_at DESC);

-- 3. Company Policy Documents table (for PDF uploads)
CREATE TABLE IF NOT EXISTS company_policy_docs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename        TEXT NOT NULL,
    extracted_text  TEXT NOT NULL,
    char_count      INTEGER,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_policy_docs_user_id ON company_policy_docs(user_id);

-- 4. Auto-update updated_at on users
CREATE OR REPLACE FUNCTION update_user_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated ON users;
CREATE TRIGGER trg_users_updated
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_user_timestamp();
