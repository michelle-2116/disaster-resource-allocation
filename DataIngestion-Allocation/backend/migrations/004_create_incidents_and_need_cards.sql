-- ============================================================
-- Incident audit log and need cards
-- ============================================================
-- The application uses incidents.incident_id as the stable external
-- incident identifier, while need_cards.incident_id stores the UUID FK.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TABLE IF NOT EXISTS incidents (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id   TEXT UNIQUE,
    incident_name TEXT,
    incident_type TEXT,
    location      TEXT,
    title         TEXT,
    severity      INT CHECK (severity IS NULL OR severity BETWEEN 1 AND 10),
    summary       TEXT,
    status        TEXT NOT NULL DEFAULT 'active',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE incidents ADD COLUMN IF NOT EXISTS id UUID DEFAULT gen_random_uuid();
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS incident_id TEXT;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS incident_name TEXT;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS incident_type TEXT;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS location TEXT;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS severity INT;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS summary TEXT;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

UPDATE incidents
SET incident_id = id::TEXT
WHERE incident_id IS NULL;

ALTER TABLE incidents ALTER COLUMN incident_id SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'incidents_incident_id_key'
    ) THEN
        ALTER TABLE incidents ADD CONSTRAINT incidents_incident_id_key UNIQUE (incident_id);
    END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS idx_incidents_incident_id ON incidents (incident_id);
CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents (created_at DESC);

CREATE TABLE IF NOT EXISTS need_cards (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id      UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    type             TEXT NOT NULL,
    item             TEXT NOT NULL,
    qty              NUMERIC NOT NULL CHECK (qty >= 0),
    note             TEXT,
    explanation      TEXT NOT NULL,
    done_by          TEXT,
    fulfilled        BOOLEAN NOT NULL DEFAULT FALSE,
    pending_approval BOOLEAN NOT NULL DEFAULT FALSE,
    show_pd          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE need_cards ADD COLUMN IF NOT EXISTS incident_id UUID;
ALTER TABLE need_cards ADD COLUMN IF NOT EXISTS type TEXT;
ALTER TABLE need_cards ADD COLUMN IF NOT EXISTS item TEXT;
ALTER TABLE need_cards ADD COLUMN IF NOT EXISTS qty NUMERIC;
ALTER TABLE need_cards ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE need_cards ADD COLUMN IF NOT EXISTS explanation TEXT;
ALTER TABLE need_cards ADD COLUMN IF NOT EXISTS done_by TEXT;
ALTER TABLE need_cards ADD COLUMN IF NOT EXISTS fulfilled BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE need_cards ADD COLUMN IF NOT EXISTS pending_approval BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE need_cards ADD COLUMN IF NOT EXISTS show_pd BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE need_cards ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE need_cards ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_need_cards_incident_id ON need_cards (incident_id);
CREATE INDEX IF NOT EXISTS idx_need_cards_created_at ON need_cards (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_need_cards_show_pd ON need_cards (show_pd);

DROP TRIGGER IF EXISTS trg_incidents_updated_at ON incidents;
CREATE TRIGGER trg_incidents_updated_at
    BEFORE UPDATE ON incidents
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_need_cards_updated_at ON need_cards;
CREATE TRIGGER trg_need_cards_updated_at
    BEFORE UPDATE ON need_cards
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

NOTIFY pgrst, 'reload schema';
