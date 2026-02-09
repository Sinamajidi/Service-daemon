/*! \file sample_data.sql
 *  \brief Sample data for the service daemon (operations + scheduled tasks).
 */

-- Users (tenants, managers, providers)
INSERT INTO users (id, email, password_hash, full_name, phone, role)
VALUES
  ('11111111-1111-1111-1111-111111111111', 'alex.tenant@example.com', NULL, 'Alex Tenant', '+1-555-0100', 'tenant'),
  ('22222222-2222-2222-2222-222222222222', 'maria.tenant@example.com', NULL, 'Maria Tenant', '+1-555-0101', 'tenant'),
  ('33333333-3333-3333-3333-333333333333', 'jordan.tenant@example.com', NULL, 'Jordan Tenant', '+1-555-0105', 'tenant'),
  ('44444444-4444-4444-4444-444444444444', 'li.manager@example.com', NULL, 'Li Manager', '+1-555-0102', 'manager'),
  ('55555555-5555-5555-5555-555555555555', 'sam.it@example.com', NULL, 'Sam IT Manager', '+1-555-0103', 'provider_staff'),
  ('66666666-6666-6666-6666-666666666666', 'riley.cleaning@example.com', NULL, 'Riley Cleaning', '+1-555-0104', 'provider_staff');

-- Buildings
INSERT INTO buildings (id, name, address, city, state, postal_code, timezone)
VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Sunset Villas', '123 Oak Street', 'Springfield', 'IL', '62701', 'America/Chicago'),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Riverside Towers', '987 River Road', 'Springfield', 'IL', '62702', 'America/Chicago');

-- Units
INSERT INTO units (id, building_id, unit_number, floor, bedrooms, bathrooms, sqft)
VALUES
  ('cccccccc-cccc-cccc-cccc-cccccccccccc', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '1A', 1, 2, 1.5, 950),
  ('dddddddd-dddd-dddd-dddd-dddddddddddd', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '2B', 2, 3, 2.0, 1200),
  ('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '8C', 8, 1, 1.0, 720);

-- Tenants
INSERT INTO tenants (id, user_id, unit_id, move_in_date)
VALUES
  ('f1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'cccccccc-cccc-cccc-cccc-cccccccccccc', '2023-06-01'),
  ('f2222222-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222222', 'dddddddd-dddd-dddd-dddd-dddddddddddd', '2024-01-15'),
  ('f3333333-3333-3333-3333-333333333333', '33333333-3333-3333-3333-333333333333', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', '2024-09-01');

-- Operations (service types)
INSERT INTO service_types (id, code, name, description, default_duration_minutes, default_price_cents)
VALUES
  ('0a0a0a0a-0a0a-0a0a-0a0a-0a0a0a0a0a0a', 'house_cleaning', 'House Cleaning', 'Full home cleaning service', 120, 18000),
  ('0b0b0b0b-0b0b-0b0b-0b0b-0b0b0b0b0b0b', 'vacuum_cleaning', 'Vacuum Cleaning', 'Vacuum and dusting service', 60, 8000),
  ('0c0c0c0c-0c0c-0c0c-0c0c-0c0c0c0c0c0c', 'it_manager', 'IT Manager Visit', 'On-site IT support for smart-home and devices', 90, 15000),
  ('0d0d0d0d-0d0d-0d0d-0d0d-0d0d0d0d0d0d', 'window_washing', 'Window Washing', 'Interior and exterior window cleaning', 90, 12000);

-- Providers
INSERT INTO providers (id, name, contact_email, contact_phone, address, rating)
VALUES
  ('1111aaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Sparkle Services', 'dispatch@sparkle.example.com', '+1-555-0200', '10 Clean Ave, Springfield, IL', 4.8),
  ('2222bbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'SmartHome IT', 'support@smarthome.example.com', '+1-555-0201', '55 Tech Park, Springfield, IL', 4.6);

-- Provider staff
INSERT INTO provider_staff (id, provider_id, user_id, display_name, skills)
VALUES
  (
    '3333cccc-cccc-cccc-cccc-cccccccccccc',
    '2222bbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    '55555555-5555-5555-5555-555555555555',
    'Sam (IT Manager)',
    ARRAY['it_manager']
  ),
  (
    '4444dddd-dddd-dddd-dddd-dddddddddddd',
    '1111aaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    '66666666-6666-6666-6666-666666666666',
    'Riley (Cleaning Lead)',
    ARRAY['house_cleaning', 'vacuum_cleaning', 'window_washing']
  );

-- Scheduled tasks (bookings)
INSERT INTO bookings (
  id,
  reference,
  tenant_id,
  requestor_user_id,
  unit_id,
  service_type_id,
  provider_staff_id,
  status,
  priority,
  notes,
  estimated_duration_minutes,
  price_cents,
  scheduled_range,
  scheduled_start,
  scheduled_end
)
VALUES
  (
    '5555eeee-eeee-eeee-eeee-eeeeeeeeeeee',
    'BK-1001',
    'f1111111-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111111',
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    '0a0a0a0a-0a0a-0a0a-0a0a-0a0a0a0a0a0a',
    '4444dddd-dddd-dddd-dddd-dddddddddddd',
    'scheduled',
    'normal',
    'Deep clean for living room and kitchen.',
    120,
    18500,
    tstzrange('2025-02-12 09:00:00-06', '2025-02-12 11:00:00-06', '[)'),
    '2025-02-12 09:00:00-06',
    '2025-02-12 11:00:00-06'
  ),
  (
    '6666ffff-ffff-ffff-ffff-ffffffffffff',
    'BK-1002',
    'f2222222-2222-2222-2222-222222222222',
    '22222222-2222-2222-2222-222222222222',
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    '0b0b0b0b-0b0b-0b0b-0b0b-0b0b0b0b0b0b',
    '4444dddd-dddd-dddd-dddd-dddddddddddd',
    'scheduled',
    'high',
    'Vacuum and dust after renovation.',
    60,
    9000,
    tstzrange('2025-02-12 13:00:00-06', '2025-02-12 14:00:00-06', '[)'),
    '2025-02-12 13:00:00-06',
    '2025-02-12 14:00:00-06'
  ),
  (
    '77770000-0000-0000-0000-000000000000',
    'BK-1003',
    'f3333333-3333-3333-3333-333333333333',
    '44444444-4444-4444-4444-444444444444',
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    '0c0c0c0c-0c0c-0c0c-0c0c-0c0c0c0c0c0c',
    '3333cccc-cccc-cccc-cccc-cccccccccccc',
    'scheduled',
    'normal',
    'Reconnect smart thermostat and update router firmware.',
    90,
    15500,
    tstzrange('2025-02-12 15:00:00-06', '2025-02-12 16:30:00-06', '[)'),
    '2025-02-12 15:00:00-06',
    '2025-02-12 16:30:00-06'
  );

-- Assignments (link bookings to providers)
INSERT INTO assignments (id, booking_id, provider_id, provider_staff_id, assigned_by, status)
VALUES
  (
    '88881111-1111-1111-1111-111111111111',
    '5555eeee-eeee-eeee-eeee-eeeeeeeeeeee',
    '1111aaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    '4444dddd-dddd-dddd-dddd-dddddddddddd',
    '44444444-4444-4444-4444-444444444444',
    'assigned'
  ),
  (
    '99992222-2222-2222-2222-222222222222',
    '6666ffff-ffff-ffff-ffff-ffffffffffff',
    '1111aaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    '4444dddd-dddd-dddd-dddd-dddddddddddd',
    '44444444-4444-4444-4444-444444444444',
    'assigned'
  ),
  (
    'aaaa3333-3333-3333-3333-333333333333',
    '77770000-0000-0000-0000-000000000000',
    '2222bbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    '3333cccc-cccc-cccc-cccc-cccccccccccc',
    '44444444-4444-4444-4444-444444444444',
    'assigned'
  );
