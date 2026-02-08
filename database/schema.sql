-- Enable extension (run once)
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS btree_gist;



-- Users (system login / accounts)
CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text UNIQUE NOT NULL,
  password_hash text,                 -- nullable for third-party auth
  full_name text NOT NULL,
  phone text,
  role text NOT NULL,                 -- e.g. 'tenant','manager','provider_staff','admin'
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  is_active boolean NOT NULL DEFAULT true
);

-- Buildings
CREATE TABLE buildings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text,
  address text NOT NULL,
  city text,
  state text,
  postal_code text,
  country text DEFAULT 'US',
  timezone text NOT NULL DEFAULT 'UTC', -- e.g. 'America/Chicago'
  metadata jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Units (apartments, houses)
CREATE TABLE units (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  building_id uuid NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
  unit_number text,
  floor integer,
  bedrooms integer,
  bathrooms numeric,
  sqft integer,
  metadata jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(building_id, unit_number)
);

-- Tenants (residents) - separate from users if needed
CREATE TABLE tenants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid UNIQUE REFERENCES users(id) ON DELETE SET NULL,
  unit_id uuid REFERENCES units(id) ON DELETE SET NULL,
  move_in_date date,
  move_out_date date,
  metadata jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Service types & categories
CREATE TABLE service_types (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code text UNIQUE NOT NULL,           -- e.g. 'laundry', 'plumbing'
  name text NOT NULL,
  description text,
  default_duration_minutes integer NOT NULL DEFAULT 60,
  default_price_cents bigint,          -- optional
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Providers (companies)
CREATE TABLE providers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  contact_email text,
  contact_phone text,
  address text,
  rating numeric,                      -- aggregated
  metadata jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Provider staff / technicians
CREATE TABLE provider_staff (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_id uuid NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
  user_id uuid REFERENCES users(id),
  display_name text,
  skills text[],                       -- array of service_type codes or ids
  active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Bookings (service orders)
CREATE TABLE bookings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  reference text UNIQUE,                -- optional human reference
  tenant_id uuid REFERENCES tenants(id) ON DELETE SET NULL,
  requestor_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
  unit_id uuid REFERENCES units(id) ON DELETE SET NULL,
  service_type_id uuid REFERENCES service_types(id),
  provider_staff_id uuid,               -- for exclusion constraint on staff scheduling
  status text NOT NULL DEFAULT 'requested', -- requested, scheduled, assigned, in_progress, completed, cancelled
  priority text DEFAULT 'normal',       -- low, normal, high, emergency
  notes text,
  estimated_duration_minutes integer,   -- override or computed
  price_cents bigint,
  scheduled_range tstzrange,            -- time range for the booking
  scheduled_start timestamptz,          -- separate start/end for convenience
  scheduled_end timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  cancelled_at timestamptz,
  cancelled_by uuid REFERENCES users(id)
);

-- Assignment (which provider / staff is assigned)
CREATE TABLE assignments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_id uuid UNIQUE REFERENCES bookings(id) ON DELETE CASCADE,
  provider_id uuid REFERENCES providers(id),
  provider_staff_id uuid REFERENCES provider_staff(id),
  assigned_by uuid REFERENCES users(id),
  assigned_at timestamptz NOT NULL DEFAULT now(),
  status text DEFAULT 'assigned'       -- assigned, en_route, completed, cancelled
);

-- Invoices and payments
CREATE TABLE invoices (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_id uuid REFERENCES bookings(id) ON DELETE SET NULL,
  tenant_id uuid REFERENCES tenants(id),
  amount_cents bigint NOT NULL,
  tax_cents bigint,
  currency text DEFAULT 'USD',
  status text DEFAULT 'unpaid',        -- unpaid, paid, refunded
  issued_at timestamptz NOT NULL DEFAULT now(),
  paid_at timestamptz,
  metadata jsonb
);

CREATE TABLE payments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  invoice_id uuid REFERENCES invoices(id) ON DELETE CASCADE,
  amount_cents bigint NOT NULL,
  method text,                         -- card, wallet, cash, stripe_id...
  status text DEFAULT 'completed',
  paid_at timestamptz NOT NULL DEFAULT now(),
  metadata jsonb
);

-- Reviews
CREATE TABLE reviews (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_id uuid REFERENCES bookings(id) ON DELETE SET NULL,
  reviewer_user_id uuid REFERENCES users(id),
  provider_id uuid REFERENCES providers(id),
  rating integer CHECK (rating >= 1 AND rating <= 5),
  comment text,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Notifications (push, email)
CREATE TABLE notifications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES users(id),
  type text,                           -- 'booking_created', 'assignment', ...
  payload jsonb,
  sent_at timestamptz,
  read boolean DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Audit log (change history)
CREATE TABLE audit_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity text NOT NULL,
  entity_id uuid,
  action text NOT NULL,                -- created, updated, deleted
  performed_by uuid REFERENCES users(id),
  payload jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Indexes for common queries
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_bookings_unit ON bookings(unit_id);
CREATE INDEX idx_bookings_tenant ON bookings(tenant_id);
CREATE INDEX idx_bookings_scheduled_range ON bookings USING GIST (scheduled_range);
CREATE INDEX idx_provider_staff_provider ON provider_staff(provider_id);

-- Exclusion constraints to prevent overlapping bookings
-- Prevent overlapping bookings on the same unit (only when both unit_id and scheduled_range are not null)
ALTER TABLE bookings
  ADD CONSTRAINT no_overlap_unit EXCLUDE USING GIST (
    unit_id WITH =,
    scheduled_range WITH &&
  ) WHERE (unit_id IS NOT NULL AND scheduled_range IS NOT NULL);

-- Prevent overlapping bookings for the same provider_staff (only when both provider_staff_id and scheduled_range are not null)
ALTER TABLE bookings 
  ADD CONSTRAINT no_overlap_provider_staff EXCLUDE USING GIST (
    provider_staff_id WITH =,
    scheduled_range WITH &&
  ) WHERE (provider_staff_id IS NOT NULL AND scheduled_range IS NOT NULL);
