-- ============================================================
-- Inventory schema repair for existing Supabase databases
-- ============================================================
-- 001_create_inventory.sql creates item_type for fresh databases, but
-- CREATE TABLE IF NOT EXISTS does not repair older inventory tables.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TABLE IF NOT EXISTS inventory (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_name          VARCHAR(200) NOT NULL,
    available_quantity INT NOT NULL DEFAULT 0 CHECK (available_quantity >= 0),
    location           VARCHAR(200) NOT NULL DEFAULT 'Unknown',
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE inventory ADD COLUMN IF NOT EXISTS id UUID DEFAULT gen_random_uuid();
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS item_type VARCHAR(50);
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS item_name VARCHAR(200);
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS available_quantity INT DEFAULT 0;
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS location VARCHAR(200) DEFAULT 'Unknown';
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

UPDATE inventory SET id = gen_random_uuid() WHERE id IS NULL;
UPDATE inventory SET item_name = 'unknown item ' || id::TEXT WHERE item_name IS NULL;
UPDATE inventory SET updated_at = NOW() WHERE updated_at IS NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'inventory'
          AND column_name = 'quantity'
    ) THEN
        UPDATE inventory
        SET available_quantity = quantity
        WHERE available_quantity IS NULL;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'inventory'
          AND column_name = 'shelter_id'
    ) THEN
        UPDATE inventory
        SET location = shelter_id::TEXT
        WHERE location IS NULL;
    END IF;
END;
$$;

UPDATE inventory SET available_quantity = 0 WHERE available_quantity IS NULL;
UPDATE inventory SET location = 'Unknown' WHERE location IS NULL;

UPDATE inventory
SET item_type = CASE
    WHEN item_name IN (
        'water pouches (500ml)',
        'water purification tabs',
        'bottled water (1L)'
    ) THEN 'water'
    WHEN item_name IN (
        'ORS kits',
        'first aid kits',
        'trauma kits',
        'anti-cholera tablets'
    ) THEN 'meds'
    WHEN item_name IN (
        'NDRF team',
        'State rescue team',
        'Boat rescue unit'
    ) THEN 'rescue_team'
    WHEN item_name ILIKE '%water%' OR item_name ILIKE '%purification%' THEN 'water'
    WHEN item_name ILIKE '%ors%' OR item_name ILIKE '%aid%' OR item_name ILIKE '%kit%'
        OR item_name ILIKE '%tablet%' OR item_name ILIKE '%med%' OR item_name ILIKE '%trauma%' THEN 'meds'
    WHEN item_name ILIKE '%team%' OR item_name ILIKE '%rescue%' OR item_name ILIKE '%ndrf%'
        OR item_name ILIKE '%boat%' THEN 'rescue_team'
    ELSE 'food'
END
WHERE item_type IS NULL;

ALTER TABLE inventory ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE inventory ALTER COLUMN id SET NOT NULL;
ALTER TABLE inventory ALTER COLUMN item_type SET NOT NULL;
ALTER TABLE inventory ALTER COLUMN item_name SET NOT NULL;
ALTER TABLE inventory ALTER COLUMN available_quantity SET DEFAULT 0;
ALTER TABLE inventory ALTER COLUMN available_quantity SET NOT NULL;
ALTER TABLE inventory ALTER COLUMN location SET DEFAULT 'Unknown';
ALTER TABLE inventory ALTER COLUMN location SET NOT NULL;
ALTER TABLE inventory ALTER COLUMN updated_at SET DEFAULT NOW();
ALTER TABLE inventory ALTER COLUMN updated_at SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'inventory_pkey'
          AND conrelid = 'inventory'::regclass
    ) THEN
        ALTER TABLE inventory
            ADD CONSTRAINT inventory_pkey
            PRIMARY KEY (id);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'inventory_item_type_check'
          AND conrelid = 'inventory'::regclass
    ) THEN
        ALTER TABLE inventory
            ADD CONSTRAINT inventory_item_type_check
            CHECK (item_type IN ('food', 'water', 'meds', 'rescue_team'));
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'inventory_available_quantity_check'
          AND conrelid = 'inventory'::regclass
    ) THEN
        ALTER TABLE inventory
            ADD CONSTRAINT inventory_available_quantity_check
            CHECK (available_quantity >= 0);
    END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS idx_inventory_item_type ON inventory (item_type);
CREATE INDEX IF NOT EXISTS idx_inventory_item_name ON inventory (item_name);

DROP TRIGGER IF EXISTS trg_inventory_updated_at ON inventory;
CREATE TRIGGER trg_inventory_updated_at
    BEFORE UPDATE ON inventory
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

NOTIFY pgrst, 'reload schema';
