/*! \file sample_data.sql
 *  \brief Sample data for the service daemon (operations + scheduled tasks).
 */

-- Users (tenants, managers, providers)
WITH new_users AS (
  INSERT INTO users (email, password_hash, full_name, phone, role)
  VALUES
    ('alex.tenant@example.com', NULL, 'Alex Tenant', '+1-555-0100', 'tenant'),
    ('maria.tenant@example.com', NULL, 'Maria Tenant', '+1-555-0101', 'tenant'),
    ('li.manager@example.com', NULL, 'Li Manager', '+1-555-0102', 'manager'),
    ('jordan.tenant@example.com', NULL, 'Jordan Tenant', '+1-555-0105', 'tenant'),
    ('sam.it@example.com', NULL, 'Sam IT Manager', '+1-555-0103', 'provider_staff'),
    ('riley.cleaning@example.com', NULL, 'Riley Cleaning', '+1-555-0104', 'provider_staff')
  RETURNING id, email
),
new_buildings AS (
  INSERT INTO buildings (name, address, city, state, postal_code, timezone)
  VALUES
    ('Sunset Villas', '123 Oak Street', 'Springfield', 'IL', '62701', 'America/Chicago'),
    ('Riverside Towers', '987 River Road', 'Springfield', 'IL', '62702', 'America/Chicago')
  RETURNING id, name
),
new_units AS (
  INSERT INTO units (building_id, unit_number, floor, bedrooms, bathrooms, sqft)
  VALUES
    ((SELECT id FROM new_buildings WHERE name = 'Sunset Villas'), '1A', 1, 2, 1.5, 950),
    ((SELECT id FROM new_buildings WHERE name = 'Sunset Villas'), '2B', 2, 3, 2.0, 1200),
    ((SELECT id FROM new_buildings WHERE name = 'Riverside Towers'), '8C', 8, 1, 1.0, 720)
  RETURNING id, unit_number
),
new_tenants AS (
  INSERT INTO tenants (user_id, unit_id, move_in_date)
  VALUES
    ((SELECT id FROM new_users WHERE email = 'alex.tenant@example.com'), (SELECT id FROM new_units WHERE unit_number = '1A'), '2023-06-01'),
    ((SELECT id FROM new_users WHERE email = 'maria.tenant@example.com'), (SELECT id FROM new_units WHERE unit_number = '2B'), '2024-01-15'),
    ((SELECT id FROM new_users WHERE email = 'jordan.tenant@example.com'), (SELECT id FROM new_units WHERE unit_number = '8C'), '2024-09-01')
  RETURNING id, user_id, unit_id
),
new_service_types AS (
  INSERT INTO service_types (code, name, description, default_duration_minutes, default_price_cents)
  VALUES
    ('house_cleaning', 'House Cleaning', 'Full home cleaning service', 120, 18000),
    ('vacuum_cleaning', 'Vacuum Cleaning', 'Vacuum and dusting service', 60, 8000),
    ('it_manager', 'IT Manager Visit', 'On-site IT support for smart-home and devices', 90, 15000),
    ('window_washing', 'Window Washing', 'Interior and exterior window cleaning', 90, 12000)
  RETURNING id, code
),
new_providers AS (
  INSERT INTO providers (name, contact_email, contact_phone, address, rating)
  VALUES
    ('Sparkle Services', 'dispatch@sparkle.example.com', '+1-555-0200', '10 Clean Ave, Springfield, IL', 4.8),
    ('SmartHome IT', 'support@smarthome.example.com', '+1-555-0201', '55 Tech Park, Springfield, IL', 4.6)
  RETURNING id, name
),
new_provider_staff AS (
  INSERT INTO provider_staff (provider_id, user_id, display_name, skills)
  VALUES
    (
      (SELECT id FROM new_providers WHERE name = 'SmartHome IT'),
      (SELECT id FROM new_users WHERE email = 'sam.it@example.com'),
      'Sam (IT Manager)',
      ARRAY['it_manager']
    ),
    (
      (SELECT id FROM new_providers WHERE name = 'Sparkle Services'),
      (SELECT id FROM new_users WHERE email = 'riley.cleaning@example.com'),
      'Riley (Cleaning Lead)',
      ARRAY['house_cleaning', 'vacuum_cleaning', 'window_washing']
    )
  RETURNING id, display_name
)
INSERT INTO bookings (
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
    'BK-1001',
    (SELECT id FROM new_tenants WHERE unit_id = (SELECT id FROM new_units WHERE unit_number = '1A')),
    (SELECT id FROM new_users WHERE email = 'alex.tenant@example.com'),
    (SELECT id FROM new_units WHERE unit_number = '1A'),
    (SELECT id FROM new_service_types WHERE code = 'house_cleaning'),
    (SELECT id FROM new_provider_staff WHERE display_name = 'Riley (Cleaning Lead)'),
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
    'BK-1002',
    (SELECT id FROM new_tenants WHERE unit_id = (SELECT id FROM new_units WHERE unit_number = '2B')),
    (SELECT id FROM new_users WHERE email = 'maria.tenant@example.com'),
    (SELECT id FROM new_units WHERE unit_number = '2B'),
    (SELECT id FROM new_service_types WHERE code = 'vacuum_cleaning'),
    (SELECT id FROM new_provider_staff WHERE display_name = 'Riley (Cleaning Lead)'),
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
    'BK-1003',
    (SELECT id FROM new_tenants WHERE unit_id = (SELECT id FROM new_units WHERE unit_number = '8C')),
    (SELECT id FROM new_users WHERE email = 'li.manager@example.com'),
    (SELECT id FROM new_units WHERE unit_number = '8C'),
    (SELECT id FROM new_service_types WHERE code = 'it_manager'),
    (SELECT id FROM new_provider_staff WHERE display_name = 'Sam (IT Manager)'),
    'scheduled',
    'normal',
    'Reconnect smart thermostat and update router firmware.',
    90,
    15500,
    tstzrange('2025-02-12 15:00:00-06', '2025-02-12 16:30:00-06', '[)'),
    '2025-02-12 15:00:00-06',
    '2025-02-12 16:30:00-06'
  );

-- Link bookings to provider assignments
INSERT INTO assignments (booking_id, provider_id, provider_staff_id, assigned_by, status)
SELECT
  bookings.id,
  (SELECT id FROM providers WHERE name = 'Sparkle Services'),
  (SELECT id FROM provider_staff WHERE display_name = 'Riley (Cleaning Lead)'),
  (SELECT id FROM users WHERE email = 'li.manager@example.com'),
  'assigned'
FROM bookings
WHERE reference IN ('BK-1001', 'BK-1002');

INSERT INTO assignments (booking_id, provider_id, provider_staff_id, assigned_by, status)
SELECT
  bookings.id,
  (SELECT id FROM providers WHERE name = 'SmartHome IT'),
  (SELECT id FROM provider_staff WHERE display_name = 'Sam (IT Manager)'),
  (SELECT id FROM users WHERE email = 'li.manager@example.com'),
  'assigned'
FROM bookings
WHERE reference = 'BK-1003';
