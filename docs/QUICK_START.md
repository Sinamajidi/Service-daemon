"""
QUICK START GUIDE
=================

This file provides the absolute minimum code needed to get started.
"""

# =============================================================================
# STEP 1: INSTALL DEPENDENCIES
# =============================================================================
# Run in terminal:
# pip install psycopg2-binary python-dotenv


# =============================================================================
# STEP 2: INITIALIZE DATABASE (Run once)
# =============================================================================

from db_init import DatabaseInitializer
from pathlib import Path

# Configure your database
db_init = DatabaseInitializer(
    host='localhost',
    port=5432,
    database='apartment_mgmt',
    user='postgres',
    password='your_password_here'
)

# Initialize with your schema file
schema_file = Path('/mnt/user-data/uploads/Database_Scheme.sql')
db_init.initialize(schema_file, drop_if_exists=True)

print("Database initialized!")


# =============================================================================
# STEP 3: USE THE COMMUNICATION LAYER
# =============================================================================

from entity_access import (
    get_user_access,
    get_tenant_access,
    get_unit_access,
    get_booking_access
)

# Get access objects
user_access = get_user_access()
tenant_access = get_tenant_access()
unit_access = get_unit_access()
booking_access = get_booking_access()


# =============================================================================
# COMMON OPERATIONS
# =============================================================================

# --- GET LIST OF IDs (No objects created) ---
user_ids = user_access.get_all_user_ids()
tenant_ids = tenant_access.get_current_tenant_ids()
booking_ids = booking_access.get_bookings_by_status_ids('requested')

print(f"Found {len(user_ids)} users")


# --- GET COMPLETE DATA (Returns dictionary) ---
user_data = user_access.get_user_data(user_ids[0])
print(f"User email: {user_data['email']}")


# --- GET OBJECT (Only when GUI needs it) ---
user_obj = user_access.get_user(user_ids[0])
print(f"User name: {user_obj.full_name}")


# --- CREATE NEW RECORDS ---
new_user_id = user_access.create_user(
    email='test@example.com',
    full_name='Test User',
    role='tenant',
    phone='555-1234'
)
print(f"Created user: {new_user_id}")


# --- UPDATE RECORDS ---
success = user_access.update_user(
    new_user_id,
    phone='555-9999'
)
print(f"Updated: {success}")


# --- COMPLEX QUERIES (Database does the work) ---
booking_full = booking_access.get_booking_with_details(booking_ids[0])
print(f"Booking for: {booking_full['tenant_name']}")


# =============================================================================
# TYPICAL GUI WORKFLOW
# =============================================================================

def show_booking_list():
    """GUI shows list of bookings"""
    # Get IDs only (minimal memory)
    booking_ids = booking_access.get_bookings_by_status_ids('requested')
    return booking_ids


def show_booking_details(booking_id):
    """User clicks on a booking"""
    # Get data as dictionary
    booking_data = booking_access.get_booking_data(booking_id)
    return booking_data


def show_booking_full_view(booking_id):
    """Show detailed view with all relations"""
    # Database does the JOIN
    booking_full = booking_access.get_booking_with_details(booking_id)
    return booking_full


# =============================================================================
# CUSTOM QUERIES
# =============================================================================

from data_access_layer import get_dal

dal = get_dal()

# Execute any SQL you need
results = dal.execute_custom_query(
    """
    SELECT u.full_name, COUNT(b.id) as total_bookings
    FROM users u
    JOIN tenants t ON u.id = t.user_id
    LEFT JOIN bookings b ON t.id = b.tenant_id
    GROUP BY u.id, u.full_name
    """,
    fetch='all'
)

for row in results:
    print(f"{row['full_name']}: {row['total_bookings']} bookings")


# =============================================================================
# KEY POINTS TO REMEMBER
# =============================================================================

"""
1. Use get_*_ids() for lists → Returns List[str], no objects
2. Use get_*_data() for details → Returns Dict, no objects
3. Use get_*() for objects → Only when GUI needs it
4. Use get_*_with_details() for complex views → Database JOINs
5. All heavy processing happens in PostgreSQL
6. Objects are only created when explicitly requested

PREFER:  user_ids = get_all_user_ids()
OVER:    users = [get_user(id) for id in ids]

Only create objects when you need to manipulate them or when
the GUI framework requires objects instead of dictionaries.
"""
