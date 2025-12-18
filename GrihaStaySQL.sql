-- === Extensions (run once) ===
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS postgis;   -- optional, recommended for geo queries

-- === Enums ===
CREATE TYPE booking_status AS ENUM ('PENDING','CONFIRMED','CANCELLED','CHECKED_IN','CHECKED_OUT','NO_SHOW');
CREATE TYPE payment_status AS ENUM ('PENDING','PAID','FAILED','REFUNDED');
CREATE TYPE payment_method AS ENUM ('GATEWAY','OFFLINE','PAY_AT_PROPERTY','WALLET');
CREATE TYPE user_role AS ENUM ('OWNER','MANAGER','RECEPTIONIST','HOUSEKEEPING','AUDITOR');
CREATE TYPE room_status AS ENUM ('AVAILABLE','OCCUPIED','OUT_OF_SERVICE','MAINTENANCE');
CREATE TYPE listing_status AS ENUM ('DRAFT','LISTED','UNLISTED','SUSPENDED');
CREATE TYPE pricing_modifier_type AS ENUM ('AMOUNT','PERCENT');
CREATE TYPE community_media_type AS ENUM ('IMAGE','VIDEO','DOCUMENT');

-- === Country Table ===
CREATE TABLE country (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  code TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);  
-- === State Table ===
CREATE TABLE state (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  country_id UUID NOT NULL REFERENCES country(id) ON DELETE        CASCADE,
  name TEXT NOT NULL,
  code TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);  
-- === District Table ===
CREATE TABLE district (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  state_id UUID NOT NULL REFERENCES state(id) ON DELETE CASCADE,                
  name TEXT NOT NULL,
  code TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
-- === Municipality Table ===
CREATE TABLE municipality (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  district_id UUID NOT NULL REFERENCES district(id) ON DELETE CASCADE,                
  name TEXT NOT NULL,
  code TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
-- city table --
CREATE TABLE city (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  district_id UUID NOT NULL REFERENCES district(id) ON DELETE CASCADE,                
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- === Community Table ===
CREATE TABLE community (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,

  state_id UUID REFERENCES state(id) ON DELETE SET NULL,
  district_id UUID REFERENCES district(id) ON DELETE SET NULL,
  municipality_id UUID REFERENCES municipality(id) ON DELETE SET NULL,

  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),

  -- prevent duplicate community names within same municipality
  UNIQUE (name, municipality_id)
);
CREATE INDEX idx_community_state ON community (state_id);
CREATE INDEX idx_community_district ON community (district_id);
CREATE INDEX idx_community_municipality ON community (municipality_id);

-- === Community Table ===
CREATE TABLE community_media (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  community_id UUID NOT NULL REFERENCES community(id) ON DELETE CASCADE,
  media_name TEXT NOT NULL,
  media_file_name TEXT NOT NULL,
  media_type community_media_type DEFAULT 'IMAGE',
  media_status BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_community_media_community
ON community_media (community_id);
-- === Tenants & Users ===
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  contact_email TEXT,
  contact_phone TEXT,
  registration_number TEXT ,
  currency VARCHAR(8) DEFAULT 'NPR',
  timezone TEXT DEFAULT 'Asia/Kathmandu',
  locale TEXT DEFAULT 'en',
  plan TEXT DEFAULT 'free',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_tenants_name ON tenants (name);

CREATE TABLE tenant_users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  role user_role NOT NULL DEFAULT 'RECEPTIONIST',
  user_name TEXT NOT NULL UNIQUE, -- for login it can be email or mobile number
  email TEXT,
  password_hash TEXT, -- store salted hash
  full_name TEXT,
  mobile_number TEXT,
  is_active BOOLEAN DEFAULT true,
  email_verified BOOLEAN DEFAULT false,
  mobile_verified BOOLEAN DEFAULT false,
  last_login_at TIMESTAMPTZ,
  verification_token TEXT,
  reset_password_token TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (tenant_id, user_name)
);
CREATE INDEX idx_tenant_users_tenant ON tenant_users (tenant_id);

-- API keys / integrations for tenants (for webhooks, channel managers)
CREATE TABLE tenant_api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  key TEXT NOT NULL UNIQUE,
  description TEXT,
  scopes TEXT[], -- e.g., ['bookings:write','inventory:read']
  disabled BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_api_keys_tenant ON tenant_api_keys (tenant_id);
-- add property type table it can be eg Hotel, Resort, Apartment etc

CREATE TABLE property_types (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  description TEXT
);

-- === Properties (each belongs to a tenant) ===
CREATE TABLE properties (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  property_type_id UUID REFERENCES property_types(id) ON DELETE SET NULL,
  name TEXT NOT NULL,
  description TEXT,
  address TEXT,
  state_id UUID REFERENCES state(id) ON DELETE SET NULL,    
  district_id UUID REFERENCES district(id) ON DELETE SET NULL,
  municipality_id UUID REFERENCES municipality(id) ON DELETE SET NULL,
  city_id UUID REFERENCES city(id) ON DELETE SET NULL,
  lat DOUBLE PRECISION,
  lon DOUBLE PRECISION,
  geom geometry(Point,4326), -- uses PostGIS
  timezone TEXT DEFAULT 'Asia/Kathmandu',
  currency VARCHAR(8),
  status listing_status DEFAULT 'DRAFT',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  community_id UUID REFERENCES community(id) ON DELETE SET NULL
);
CREATE INDEX idx_properties_tenant ON properties (tenant_id);
CREATE INDEX idx_properties_geom ON properties USING GIST (geom);

-- === Amenities (global master list) ===
CREATE TABLE amenities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT
);

CREATE TABLE property_amenities (
  property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  amenity_id UUID NOT NULL REFERENCES amenities(id) ON DELETE CASCADE,
  PRIMARY KEY (property_id, amenity_id)
);

-- === Room types and rooms (tenant manages these) ===
CREATE TABLE room_types (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  name TEXT NOT NULL,                    -- e.g., "Double Room"
  slug TEXT,
  max_occupancy INTEGER DEFAULT 2,
  default_base_price NUMERIC(12,2) DEFAULT 0,
  currency VARCHAR(8),
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_roomtypes_property ON room_types (property_id);

CREATE TABLE rooms (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  room_type_id UUID NOT NULL REFERENCES room_types(id) ON DELETE CASCADE,
  room_number TEXT,
  status room_status DEFAULT 'AVAILABLE',
  price_override NUMERIC(12,2),  -- optional per-room price override
  currency VARCHAR(8),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_rooms_roomtype ON rooms (room_type_id);

CREATE TABLE room_images (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  room_type_id UUID REFERENCES room_types(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  sort_order INTEGER DEFAULT 0
);

-- === Rate plans, seasonal rules, occupancy rules ===
CREATE TABLE rate_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  room_type_id UUID REFERENCES room_types(id) ON DELETE SET NULL,
  name TEXT NOT NULL,
  description TEXT,
  pricing_model TEXT DEFAULT 'STATIC', -- STATIC or COMPLEX (rules apply)
  currency VARCHAR(8),
  base_price NUMERIC(12,2) NOT NULL DEFAULT 0, -- default nightly price
  min_stay INTEGER DEFAULT 1,
  max_stay INTEGER,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_rateplans_roomtype ON rate_plans (room_type_id);

-- Rate plan rules (seasonal / weekday / occupancy / modifiers)
CREATE TABLE rate_plan_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rate_plan_id UUID NOT NULL REFERENCES rate_plans(id) ON DELETE CASCADE,
  start_date DATE,           -- nullable => always applicable
  end_date DATE,             -- nullable => open-ended
  days_of_week INTEGER[],    -- e.g., {1,2,3,4,5,6,7}
  min_occupancy INTEGER,
  max_occupancy INTEGER,
  modifier_type pricing_modifier_type DEFAULT 'AMOUNT',
  modifier_value NUMERIC(12,2) DEFAULT 0,  -- if PERCENT, supply percentage value e.g., 10 => +10%
  priority INTEGER DEFAULT 100, -- lower = higher priority
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_rateplanrules_rateplan ON rate_plan_rules (rate_plan_id);

-- === Inventory & channel allotments per date (tenant controls counts) ===
CREATE TABLE inventory (
  id BIGSERIAL PRIMARY KEY,
  room_type_id UUID NOT NULL REFERENCES room_types(id) ON DELETE CASCADE,
  dt DATE NOT NULL,
  available_count INTEGER NOT NULL DEFAULT 0,
  blocked_count INTEGER NOT NULL DEFAULT 0,   -- for maintenance / owner hold
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (room_type_id, dt)
);
CREATE INDEX idx_inventory_roomdate ON inventory (room_type_id, dt);

-- Channel allocations (distribution to marketplace and OTAs)
CREATE TABLE channel_allocations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  room_type_id UUID NOT NULL REFERENCES room_types(id) ON DELETE CASCADE,
  channel_code TEXT NOT NULL,   -- e.g., 'MARKETPLACE','AIRBNB','BOOKING'
  allocated_count INTEGER NOT NULL DEFAULT 0,
  effective_from DATE,
  effective_to DATE
);
CREATE INDEX idx_channel_alloc_room ON channel_allocations (room_type_id, channel_code);

-- === Holds table (temporary holds created by availability check) ===
CREATE TABLE inventory_holds (
  hold_token TEXT PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  room_type_id UUID NOT NULL REFERENCES room_types(id),
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  quantity INTEGER NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL,
  metadata JSONB
);
CREATE INDEX idx_holds_room ON inventory_holds (room_type_id);

-- === Guests ===
-- Global guest profile for travelers (public)
CREATE TABLE guests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  nationality TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Tenant-specific saved guest profiles (hosts may want private notes)
CREATE TABLE tenant_guest_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  guest_id UUID REFERENCES guests(id) ON DELETE SET NULL,
  display_name TEXT,
  notes TEXT,
  last_seen_at TIMESTAMPTZ
);
CREATE INDEX idx_tenant_guest_profiles_tenant ON tenant_guest_profiles (tenant_id);


-- === Bookings & booking items ===
CREATE TABLE bookings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id TEXT, -- OTA external ref
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  room_type_id UUID NOT NULL REFERENCES room_types(id) ON DELETE CASCADE,
  room_id UUID REFERENCES rooms(id),
  source TEXT NOT NULL DEFAULT 'MARKETPLACE', -- 'OWNER','OTA','AGENT'
  checkin DATE NOT NULL,
  checkout DATE NOT NULL,
  nights INTEGER NOT NULL,
  guests_count INTEGER DEFAULT 1,
  status booking_status DEFAULT 'PENDING',
  payment_status payment_status DEFAULT 'PENDING',
  total_amount NUMERIC(12,2) DEFAULT 0,
  currency VARCHAR(8) DEFAULT 'NPR',
  commission_amount NUMERIC(12,2) DEFAULT 0,
  hold_token TEXT,
  created_by_type TEXT NOT NULL DEFAULT 'VISITOR',
  created_by_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_bookings_tenant ON bookings (tenant_id);
CREATE INDEX idx_bookings_property_dates ON bookings (property_id, checkin, checkout);
-- Partitioning recommendation: Partition bookings by checkin year at scale.

CREATE TABLE booking_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_id UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
  code TEXT,            -- e.g., "MEAL_BREAKFAST"
  description TEXT,
  quantity INTEGER DEFAULT 1,
  unit_price NUMERIC(12,2),
  total_price NUMERIC(12,2)
);
CREATE INDEX idx_booking_items_booking ON booking_items (booking_id);

-- Booking-specific guest info (snapshot at booking time)
CREATE TABLE booking_guest_info (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_id UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  nationality TEXT,
  is_primary BOOLEAN DEFAULT false
);
CREATE INDEX idx_booking_guest_info_booking ON booking_guest_info (booking_id);


-- === Payments & Refunds ===
CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_id UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
  gateway TEXT,
  method payment_method DEFAULT 'GATEWAY',
  amount NUMERIC(12,2),
  currency VARCHAR(8) DEFAULT 'NPR',
  status payment_status DEFAULT 'PENDING',
  transaction_id TEXT,
  raw_payload JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_payments_booking ON payments (booking_id);

-- === Invoices & Payouts ===
CREATE TABLE invoices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_id UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
  invoice_number TEXT,
  pdf_url TEXT,
  amount NUMERIC(12,2),
  tax_amount NUMERIC(12,2),
  issued_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_invoices_booking ON invoices (booking_id);

CREATE TABLE payouts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  amount NUMERIC(12,2),
  currency VARCHAR(8) DEFAULT 'NPR',
  status TEXT DEFAULT 'PENDING',
  scheduled_at TIMESTAMPTZ,
  processed_at TIMESTAMPTZ,
  metadata JSONB
);
CREATE INDEX idx_payouts_tenant ON payouts (tenant_id);

-- === Webhooks, idempotency & audit ===
CREATE TABLE webhook_registrations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  events TEXT[] NOT NULL,
  secret TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_webhooks_tenant ON webhook_registrations (tenant_id);

CREATE TABLE idempotency_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  key TEXT UNIQUE NOT NULL,
  tenant_id UUID,
  endpoint TEXT,
  request_hash TEXT,
  response_payload JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE audit_logs (
  id BIGSERIAL PRIMARY KEY,
  tenant_id UUID,
  actor TEXT,
  action TEXT,
  details JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- === Triggers: updated_at ===
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = now();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to commonly updated tables
CREATE TRIGGER tr_tenants_updated_at BEFORE UPDATE ON tenants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER tr_properties_updated_at BEFORE UPDATE ON properties FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER tr_room_types_updated_at BEFORE UPDATE ON room_types FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER tr_rooms_updated_at BEFORE UPDATE ON rooms FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER tr_rateplans_updated_at BEFORE UPDATE ON rate_plans FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER tr_bookings_updated_at BEFORE UPDATE ON bookings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER tr_payments_updated_at BEFORE UPDATE ON payments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER tr_community_updated_at
BEFORE UPDATE ON community
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER tr_community_media_updated_at
BEFORE UPDATE ON community_media
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- === Helpful Indexes (performance) ===
CREATE INDEX idx_bookings_status ON bookings (status);
CREATE INDEX idx_inventory_dt ON inventory (dt, room_type_id);
CREATE INDEX idx_rateplanrules_dates ON rate_plan_rules (start_date, end_date);



CREATE INDEX idx_properties_community ON properties (community_id);

ALTER TABLE bookings
ADD CONSTRAINT chk_booking_dates CHECK (checkout > checkin);

ALTER TABLE inventory
ADD CONSTRAINT chk_inventory_counts
CHECK (available_count >= blocked_count AND blocked_count >= 0);
