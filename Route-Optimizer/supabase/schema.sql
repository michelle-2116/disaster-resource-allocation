-- Enable PostGIS for location features
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Incidents
CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    type TEXT, -- flood, fire, earthquake
    severity TEXT CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    summary TEXT,
    location_lat FLOAT NOT NULL,
    location_lng FLOAT NOT NULL,
    status TEXT DEFAULT 'verified', -- verified, active, closed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Inventory
CREATE TABLE inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_name TEXT UNIQUE NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    unit TEXT -- liters, kg, units
);

-- 3. Shelters
CREATE TABLE shelters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    capacity INTEGER,
    current_occupancy INTEGER DEFAULT 0,
    lat FLOAT NOT NULL,
    lng FLOAT NOT NULL
);

-- 4. Need Cards (Allocations)
CREATE TABLE need_cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID REFERENCES incidents(id),
    shelter_id UUID REFERENCES shelters(id),
    item_type TEXT,
    requested_qty INTEGER,
    status TEXT DEFAULT 'pending_approval', -- pending_approval, approved, dispatched, delivered
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Dispatches (Routing)
CREATE TABLE dispatches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    need_card_id UUID REFERENCES need_cards(id),
    route_geometry JSONB, -- GeoJSON of the route
    estimated_time FLOAT,
    distance FLOAT,
    status TEXT DEFAULT 'en_route'
);

-- 6. Blocked Roads
CREATE TABLE blocked_roads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lat FLOAT NOT NULL,
    lng FLOAT NOT NULL,
    radius_meters FLOAT DEFAULT 500,
    reason TEXT
);

-- Initial Data
INSERT INTO inventory (item_name, quantity, unit) VALUES 
('Water', 10000, 'liters'),
('Food Rations', 5000, 'units'),
('Medical Kits', 500, 'kits'),
('Rescue Teams', 50, 'personnel');

INSERT INTO shelters (name, capacity, lat, lng) VALUES 
('Central Shelter Alpha', 500, 34.0522, -118.2437),
('Eastside Refuge', 300, 34.0600, -118.2100);