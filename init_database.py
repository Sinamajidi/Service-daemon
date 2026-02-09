#!/usr/bin/env python3
"""! @file init_database.py
@brief Convenience wrapper to initialize the database from project root.
"""

from pathlib import Path
from database.db_init import DatabaseInitializer
from config import DB_CONFIG

def main():
    """! @brief Initialize the database using the default schema."""
    # Get schema file path
    schema_file = Path(__file__).parent / 'database' / 'schema.sql'
    
    print("Initializing database...")
    print(f"Database: {DB_CONFIG['DB_NAME']}@{DB_CONFIG['DB_HOST']}:{DB_CONFIG['DB_PORT']}")
    print(f"Schema: {schema_file}")
    print()
    
    try:
        db_init = DatabaseInitializer(DB_CONFIG)
        db_init.initialize(str(schema_file), drop_if_exists=True)
        
        print()
        print("="*60)
        print("✓ Database initialized successfully!")
        print("="*60)
        print()
        print("Next step: python examples/example_usage.py")
        
    except Exception as e:
        print()
        print("="*60)
        print("✗ Failed!")
        print("="*60)
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Is PostgreSQL running? sudo service postgresql status")
        print("  2. Check .env file for correct credentials")

if __name__ == '__main__':
    main()
