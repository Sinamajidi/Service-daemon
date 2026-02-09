"""
Example Usage and Testing
Demonstrates how to use the database initialization and communication layer.
"""

from pathlib import Path
from datetime import date, datetime, timedelta
import logging
import sys

# Add project root to path so imports work from anywhere
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import our modules
from database.db_init import DatabaseInitializer
from database.db_connection import get_db
from database.data_access_layer import get_dal
from database.entity_access import (
    get_user_access, 
    get_tenant_access, 
    get_unit_access, 
    get_booking_access
)
from config import DB_CONFIG

# Get schema file path
SCHEMA_FILE = Path(__file__).parent.parent / 'database' / 'schema.sql'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def initialize_database():
    """Step 1: Initialize the database"""
    logger.info("="*60)
    logger.info("STEP 1: DATABASE INITIALIZATION")
    logger.info("="*60)
    
    db_init = DatabaseInitializer(DB_CONFIG)
    
    # Initialize database (drop and recreate)
    db_init.initialize(SCHEMA_FILE, drop_if_exists=True)
    
    logger.info("Database initialized successfully!")
    print()


def example_simple_queries():
    """
    Demonstrate simple queries that return IDs without instantiating objects.
    This is the preferred approach - get IDs first, then fetch complete data only when needed.
    """
    logger.info("="*60)
    logger.info("STEP 2: SIMPLE QUERIES (IDs only)")
    logger.info("="*60)
    
    user_access = get_user_access()
    
    # Get all user IDs
    user_ids = user_access.get_all_user_ids()
    logger.info(f"Total users: {len(user_ids)}")
    
    # Get users by role
    tenant_ids = user_access.get_users_by_role_ids('tenant')
    logger.info(f"Tenant users: {len(tenant_ids)}")
    
    # Count users
    admin_count = user_access.count_users_by_role('admin')
    logger.info(f"Admin count: {admin_count}")
    
    # Check if user exists
    if user_ids:
        exists = user_access.user_exists(user_ids[0])
        logger.info(f"First user exists: {exists}")
    
    print()


def example_complete_data_queries():
    """
    Demonstrate complete data queries that return dictionaries.
    Objects are NOT instantiated unless explicitly requested.
    """
    logger.info("="*60)
    logger.info("STEP 3: COMPLETE DATA QUERIES (Dictionaries)")
    logger.info("="*60)
    
    user_access = get_user_access()
    
    # Get user data as dictionary (no object instantiation)
    user_ids = user_access.get_all_user_ids()
    
    if user_ids:
        user_data = user_access.get_user_data(user_ids[0])
        logger.info(f"User data (dict): {user_data}")
        
        # Only instantiate object when GUI explicitly needs it
        user_obj = user_access.get_user(user_ids[0])
        logger.info(f"User object: {user_obj}")
        logger.info(f"User to_dict(): {user_obj.to_dict()}")
    
    print()


def example_data_creation():
    """
    Demonstrate creating records in the database.
    """
    logger.info("="*60)
    logger.info("STEP 4: DATA CREATION")
    logger.info("="*60)
    
    user_access = get_user_access()
    tenant_access = get_tenant_access()
    dal = get_dal()
    
    # Create a building first
    building_data = {
        'name': 'Sunset Apartments',
        'address': '123 Main Street',
        'city': 'San Francisco',
        'state': 'CA',
        'postal_code': '94102',
        'timezone': 'America/Los_Angeles'
    }
    building_id = dal.insert_record('buildings', building_data)
    logger.info(f"Created building: {building_id}")
    
    # Create a unit
    unit_access = get_unit_access()
    unit_id = unit_access.create_unit(
        building_id=building_id,
        unit_number='101',
        floor=1,
        bedrooms=2,
        bathrooms=1.5,
        sqft=850
    )
    logger.info(f"Created unit: {unit_id}")
    
    # Create users
    user1_id = user_access.create_user(
        email='john.doe@example.com',
        full_name='John Doe',
        role='tenant',
        phone='555-0101'
    )
    logger.info(f"Created user 1: {user1_id}")
    
    user2_id = user_access.create_user(
        email='jane.smith@example.com',
        full_name='Jane Smith',
        role='manager',
        phone='555-0102'
    )
    logger.info(f"Created user 2: {user2_id}")
    
    # Create tenant
    tenant_id = tenant_access.create_tenant(
        user_id=user1_id,
        unit_id=unit_id,
        move_in_date=date.today() - timedelta(days=30)
    )
    logger.info(f"Created tenant: {tenant_id}")
    
    # Create service type
    service_data = {
        'code': 'plumbing',
        'name': 'Plumbing Service',
        'description': 'General plumbing repairs and maintenance',
        'default_duration_minutes': 120,
        'default_price_cents': 15000  # $150.00
    }
    service_id = dal.insert_record('service_types', service_data)
    logger.info(f"Created service type: {service_id}")
    
    # Create booking
    booking_access = get_booking_access()
    booking_id = booking_access.create_booking(
        unit_id=unit_id,
        service_type_id=service_id,
        tenant_id=tenant_id,
        requestor_user_id=user1_id,
        priority='normal',
        notes='Leaky faucet in kitchen',
        estimated_duration_minutes=120,
        price_cents=15000
    )
    logger.info(f"Created booking: {booking_id}")
    
    print()
    return {
        'building_id': building_id,
        'unit_id': unit_id,
        'user1_id': user1_id,
        'user2_id': user2_id,
        'tenant_id': tenant_id,
        'service_id': service_id,
        'booking_id': booking_id
    }


def example_complex_queries(created_ids):
    """
    Demonstrate complex queries that leverage database processing.
    """
    logger.info("="*60)
    logger.info("STEP 5: COMPLEX QUERIES (Database-side processing)")
    logger.info("="*60)
    
    booking_access = get_booking_access()
    tenant_access = get_tenant_access()
    unit_access = get_unit_access()
    
    # Get booking with all related details (JOIN query processed in database)
    booking_details = booking_access.get_booking_with_details(created_ids['booking_id'])
    logger.info(f"Booking with details: {booking_details}")
    
    # Get tenant with user information (JOIN query)
    tenant_info = tenant_access.get_tenant_with_user_info(created_ids['tenant_id'])
    logger.info(f"Tenant with user info: {tenant_info}")
    
    # Get vacant units (subquery processed in database)
    vacant_ids = unit_access.get_vacant_unit_ids()
    logger.info(f"Vacant units: {vacant_ids}")
    
    # Custom aggregation query
    dal = get_dal()
    total_bookings = dal.execute_aggregation(
        table='bookings',
        agg_function='COUNT',
        column='*',
        where_clause="status != 'cancelled'",
        params=()
    )
    logger.info(f"Total non-cancelled bookings: {total_bookings}")
    
    # Average price of bookings
    avg_price = dal.execute_aggregation(
        table='bookings',
        agg_function='AVG',
        column='price_cents',
        where_clause="price_cents IS NOT NULL",
        params=()
    )
    logger.info(f"Average booking price: ${avg_price/100:.2f}" if avg_price else "No prices set")
    
    print()


def example_updates(created_ids):
    """
    Demonstrate updating records.
    """
    logger.info("="*60)
    logger.info("STEP 6: UPDATE OPERATIONS")
    logger.info("="*60)
    
    booking_access = get_booking_access()
    user_access = get_user_access()
    
    # Update booking status
    success = booking_access.update_booking_status(
        created_ids['booking_id'], 
        'scheduled'
    )
    logger.info(f"Booking status updated: {success}")
    
    # Update booking with scheduled time
    success = booking_access.update_booking(
        created_ids['booking_id'],
        scheduled_start=datetime.utcnow() + timedelta(days=1),
        scheduled_end=datetime.utcnow() + timedelta(days=1, hours=2)
    )
    logger.info(f"Booking scheduled time updated: {success}")
    
    # Update user information
    success = user_access.update_user(
        created_ids['user1_id'],
        phone='555-9999'
    )
    logger.info(f"User phone updated: {success}")
    
    # Verify updates
    booking_data = booking_access.get_booking_data(created_ids['booking_id'])
    logger.info(f"Updated booking status: {booking_data['status']}")
    
    user_data = user_access.get_user_data(created_ids['user1_id'])
    logger.info(f"Updated user phone: {user_data['phone']}")
    
    print()


def example_lazy_instantiation():
    """
    Demonstrate the lazy instantiation pattern.
    Objects are only created when explicitly requested.
    """
    logger.info("="*60)
    logger.info("STEP 7: LAZY INSTANTIATION PATTERN")
    logger.info("="*60)
    
    user_access = get_user_access()
    
    # Scenario 1: GUI requests list of user IDs (no objects created)
    logger.info("Scenario 1: Get IDs only (no objects)")
    user_ids = user_access.get_all_user_ids()
    logger.info(f"Retrieved {len(user_ids)} user IDs - NO objects instantiated")
    
    # Scenario 2: GUI requests complete data for one user (still no object)
    logger.info("\nScenario 2: Get data as dictionary (still no object)")
    if user_ids:
        user_dict = user_access.get_user_data(user_ids[0])
        logger.info(f"Retrieved user data - returned as DICTIONARY, not object")
        logger.info(f"Type: {type(user_dict)}")
    
    # Scenario 3: GUI explicitly needs an object (now we instantiate)
    logger.info("\nScenario 3: GUI explicitly needs object")
    if user_ids:
        user_obj = user_access.get_user(user_ids[0])
        logger.info(f"NOW created User object: {type(user_obj)}")
        logger.info(f"Object: {user_obj}")
    
    logger.info("\nKey Point: Objects are only created when explicitly requested!")
    logger.info("Most operations work with IDs and dictionaries, keeping memory usage minimal.")
    
    print()


def example_gui_workflow():
    """
    Simulate a typical GUI workflow.
    """
    logger.info("="*60)
    logger.info("STEP 8: TYPICAL GUI WORKFLOW")
    logger.info("="*60)
    
    booking_access = get_booking_access()
    booking_full=None
    unit_bookings=None
    
    # Step 1: GUI shows list of bookings (only IDs needed)
    logger.info("GUI Action: Show booking list")
    booking_ids = booking_access.get_bookings_by_status_ids('requested')
    logger.info(f"  - Retrieved {len(booking_ids)} booking IDs")
    logger.info(f"  - Memory: Minimal (just strings)")
    
    # Step 2: User clicks on a booking (get data for display)
    if booking_ids:
        logger.info("\nGUI Action: User clicks on booking")
        booking_data = booking_access.get_booking_data(booking_ids[0])
        logger.info(f"  - Retrieved booking data as dictionary")
        logger.info(f"  - Can display: {booking_data.get('notes', 'N/A')}")
    
    # Step 3: User wants detailed view with all relations (complex JOIN)
    if booking_ids:
        logger.info("\nGUI Action: Show detailed view")
        booking_full = booking_access.get_booking_with_details(booking_ids[0])
        logger.info(f"  - Retrieved full booking with tenant, unit, service info")
        logger.info(f"  - All processing done in database (efficient)")
        logger.info(f"  - Tenant: {booking_full.get('tenant_name', 'N/A')}")
        logger.info(f"  - Unit: {booking_full.get('unit_number', 'N/A')}")
        logger.info(f"  - Service: {booking_full.get('service_type_name', 'N/A')}")
    
    # Step 4: User filters bookings (database does the filtering)
    logger.info("\nGUI Action: Filter by unit")
    if not booking_full==None:
        unit_bookings = booking_access.get_bookings_by_unit_ids(booking_full['unit_id'])
    if not unit_bookings==None:
        logger.info(f"  - Database filtered to {len(unit_bookings)} bookings for this unit")
    
    logger.info("\nWorkflow complete - minimal objects, maximum database efficiency!")
    
    print()


def main():
    """
    Run all examples.
    """
    print("\n")
    print("*" * 60)
    print("APARTMENT MANAGEMENT DATABASE - INITIALIZATION & DEMO")
    print("*" * 60)
    print("\n")
    
    try:
        # Initialize database
        initialize_database()
        
        # Create sample data
        created_ids = example_data_creation()
        
        # Demonstrate different query patterns
        example_simple_queries()
        example_complete_data_queries()
        example_complex_queries(created_ids)
        example_updates(created_ids)
        example_lazy_instantiation()
        example_gui_workflow()
        
        print("*" * 60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("*" * 60)
        print("\nKey Takeaways:")
        print("1. Database initialization is automated and robust")
        print("2. Use get_*_ids() methods for lists (no object instantiation)")
        print("3. Use get_*_data() methods for complete data (returns dict)")
        print("4. Use get_*() methods only when GUI needs actual objects")
        print("5. All complex processing is delegated to PostgreSQL")
        print("6. Memory usage is minimized through lazy instantiation")
        print("*" * 60)
        
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
