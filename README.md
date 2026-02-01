# Apartment Management System - Database & Communication Layer

## Overview

This project implements a robust database initialization system and communication layer for an apartment management application. The system follows a **lazy instantiation** pattern where objects are only created when explicitly requested, and all heavy processing is delegated to PostgreSQL.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         GUI Layer                           │
│                    (Not Implemented Yet)                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Communication Layer                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Entity Access Classes                               │   │
│  │  - UserAccess, TenantAccess, UnitAccess, etc.       │   │
│  │  - Provides entity-specific methods                  │   │
│  │  - Returns IDs or dictionaries (not objects)        │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Data Access Layer (DAL)                             │   │
│  │  - Generic CRUD operations                           │   │
│  │  - Query execution                                   │   │
│  │  - Aggregations and JOINs                           │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Database Connection Manager                         │   │
│  │  - Connection pooling                                │   │
│  │  - Context managers                                  │   │
│  │  - Transaction handling                              │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   PostgreSQL Database                       │
│  - All tables and relationships                             │
│  - Constraints and indexes                                  │
│  - Heavy processing (JOINs, aggregations, etc.)            │
└─────────────────────────────────────────────────────────────┘
```

## Design Principles

### 1. Lazy Instantiation
Objects are **only instantiated when explicitly requested**. Most operations work with:
- **IDs** (strings): For lists and references
- **Dictionaries**: For complete data without object overhead
- **Objects**: Only when the GUI explicitly needs them

### 2. Database-Centric Processing
All heavy processing is done in PostgreSQL:
- Complex JOINs
- Aggregations (SUM, AVG, COUNT)
- Filtering and sorting
- Subqueries

### 3. Minimal Class Usage
Classes are lightweight wrappers that:
- Don't store state
- Don't cache data
- Delegate all work to the database
- Only exist to organize related methods

## File Structure

```
.
├── config.py                 # Configuration settings
├── db_init.py               # Database initialization
├── db_connection.py         # Connection pooling and management
├── data_access_layer.py     # Generic database operations
├── entity_access.py         # Entity-specific access classes
├── example_usage.py         # Comprehensive examples and demos
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Database Schema

The system manages:
- **Users**: System accounts with roles (tenant, manager, provider_staff, admin)
- **Buildings**: Physical buildings/properties
- **Units**: Individual apartments/units within buildings
- **Tenants**: Residents linked to users and units
- **Service Types**: Categories of services (plumbing, electrical, etc.)
- **Providers**: Service companies
- **Provider Staff**: Technicians and workers
- **Bookings**: Service requests and appointments
- **Assignments**: Provider/staff assignments to bookings
- **Invoices & Payments**: Financial transactions
- **Reviews**: Service ratings and feedback
- **Notifications**: User notifications
- **Audit Logs**: Change tracking

## Installation

1. **Install PostgreSQL** (version 12 or higher)

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure database connection** (optional):
   Set environment variables or edit `config.py`:
   ```bash
   export DB_HOST=localhost
   export DB_PORT=5432
   export DB_NAME=apartment_mgmt
   export DB_USER=postgres
   export DB_PASSWORD=your_password
   ```

4. **Initialize the database**:
   ```bash
   python db_init.py
   ```

## Usage Examples

### Initialize Database

```python
from db_init import DatabaseInitializer
from config import DB_CONFIG, SCHEMA_FILE

db_init = DatabaseInitializer(**DB_CONFIG)
db_init.initialize(SCHEMA_FILE, drop_if_exists=True)
```

### Simple Queries (IDs Only)

```python
from entity_access import get_user_access

user_access = get_user_access()

# Get all user IDs (no objects created)
user_ids = user_access.get_all_user_ids()

# Get filtered IDs
tenant_ids = user_access.get_users_by_role_ids('tenant')
active_ids = user_access.get_active_user_ids()

# Count records
admin_count = user_access.count_users_by_role('admin')

# Check existence
exists = user_access.user_exists(some_id)
```

### Complete Data Queries (Dictionaries)

```python
# Get data as dictionary (no object)
user_data = user_access.get_user_data(user_id)
print(user_data['email'])  # Access like a dict

# Get multiple records
users_data = user_access.get_all_users_data(active_only=True)
```

### Object Instantiation (When Needed)

```python
# Only instantiate when GUI needs an object
user_obj = user_access.get_user(user_id)
print(user_obj.email)  # Access like an object
print(user_obj.to_dict())  # Convert back to dict
```

### Complex Queries (Database Processing)

```python
from entity_access import get_booking_access

booking_access = get_booking_access()

# Get booking with all related data (JOIN in database)
booking_full = booking_access.get_booking_with_details(booking_id)
# Returns: booking + tenant + user + unit + service type

# Custom complex queries
from data_access_layer import get_dal

dal = get_dal()
avg_price = dal.execute_aggregation(
    table='bookings',
    agg_function='AVG',
    column='price_cents',
    where_clause="status = 'completed'",
    params=()
)
```

### Creating Records

```python
# Create a user
user_id = user_access.create_user(
    email='john@example.com',
    full_name='John Doe',
    role='tenant',
    phone='555-0101'
)

# Create a booking
from entity_access import get_booking_access

booking_access = get_booking_access()
booking_id = booking_access.create_booking(
    unit_id=unit_id,
    service_type_id=service_id,
    tenant_id=tenant_id,
    priority='high',
    notes='Emergency repair needed'
)
```

### Updating Records

```python
# Update user
success = user_access.update_user(
    user_id,
    phone='555-9999',
    full_name='John Smith'
)

# Update booking status
success = booking_access.update_booking_status(
    booking_id,
    'completed'
)
```

## Typical GUI Workflow

Here's how the GUI should interact with the communication layer:

### Scenario 1: Display List of Bookings

```python
# GUI requests booking IDs
booking_ids = booking_access.get_bookings_by_status_ids('requested')

# Display in list (just showing IDs or minimal info)
# No objects created, memory usage is minimal
```

### Scenario 2: User Clicks on a Booking

```python
# GUI needs to display booking details
booking_data = booking_access.get_booking_data(booking_id)

# Display in GUI using dictionary
# Still no object instantiation
```

### Scenario 3: Show Full Booking Details

```python
# GUI needs booking with all related information
booking_full = booking_access.get_booking_with_details(booking_id)

# This returns a single dictionary with:
# - Booking info
# - Tenant name and email
# - Unit number and building
# - Service type name
# - Assignment status
# All JOINed in the database (efficient)
```

### Scenario 4: Filter and Search

```python
# All filtering done in database
unit_bookings = booking_access.get_bookings_by_unit_ids(unit_id)
tenant_bookings = booking_access.get_bookings_by_tenant_ids(tenant_id)

# Custom filtering
from data_access_layer import get_dal
dal = get_dal()

urgent_bookings = dal.get_filtered_ids(
    'bookings',
    "priority = 'emergency' AND status != 'completed'",
    ()
)
```

## Key Benefits

1. **Memory Efficient**: Objects only created when needed
2. **Performance**: Heavy processing in database
3. **Scalable**: Connection pooling handles multiple requests
4. **Maintainable**: Clear separation of concerns
5. **Flexible**: Easy to add new queries and operations
6. **Type Safe**: Dataclasses provide structure when objects are used

## When to Use What

| Use Case | Method Type | Returns | Objects Created |
|----------|-------------|---------|-----------------|
| List view | `get_*_ids()` | `List[str]` | None |
| Simple display | `get_*_data()` | `Dict` | None |
| Object manipulation | `get_*()` | Object | One |
| Complex view | `get_*_with_details()` | `Dict` | None |
| Counting | `count_*()` | `int` | None |
| Checking existence | `*_exists()` | `bool` | None |

## Advanced Features

### Custom Queries

```python
from data_access_layer import get_dal

dal = get_dal()

# Execute any SQL query
results = dal.execute_custom_query(
    """
    SELECT u.full_name, COUNT(b.id) as booking_count
    FROM users u
    JOIN tenants t ON u.id = t.user_id
    JOIN bookings b ON t.id = b.tenant_id
    WHERE b.status = 'completed'
    GROUP BY u.id, u.full_name
    ORDER BY booking_count DESC
    LIMIT 10
    """,
    fetch='all'
)
```

### Batch Operations

```python
# Insert multiple records efficiently
from db_connection import get_db

db = get_db()
params_list = [
    ('user1@example.com', 'User One', 'tenant'),
    ('user2@example.com', 'User Two', 'tenant'),
    ('user3@example.com', 'User Three', 'tenant'),
]

db.execute_batch(
    "INSERT INTO users (email, full_name, role) VALUES (%s, %s, %s)",
    params_list
)
```

### Transaction Management

```python
from db_connection import get_db

db = get_db()

# Manual transaction control
with db.get_cursor() as cur:
    # Multiple operations in one transaction
    cur.execute("INSERT INTO buildings (...) VALUES (...)")
    building_id = cur.fetchone()['id']
    
    cur.execute("INSERT INTO units (...) VALUES (...)", (building_id,))
    # Automatically commits if no exception
    # Automatically rolls back on exception
```

## Running the Demo

To see all features in action:

```bash
python example_usage.py
```

This will:
1. Initialize the database
2. Create sample data
3. Demonstrate all query patterns
4. Show lazy instantiation in action
5. Simulate typical GUI workflows

## Next Steps

For the middle layer implementation, you should:

1. **Define API contracts**: What methods will the GUI call?
2. **Add pagination**: For large result sets
3. **Add caching** (optional): For frequently accessed data
4. **Add validation**: Input validation before database operations
5. **Add error handling**: User-friendly error messages
6. **Add logging**: Track operations for debugging
7. **Add business logic**: Complex operations combining multiple entities

## Notes

- The database uses UUIDs for all primary keys
- All timestamps use UTC (convert in GUI if needed)
- The `metadata` fields use JSONB for flexible data storage
- Connection pooling is automatic and thread-safe
- All queries use parameterized statements (SQL injection safe)

## Support

For questions or issues:
1. Check the examples in `example_usage.py`
2. Review the inline documentation in each module
3. Examine the SQL schema in `Database_Scheme.sql`
