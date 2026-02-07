#!/usr/bin/env python3
"""
Initialize Database
Run this from the project root to initialize the database.
"""

from database.db_init import DatabaseInitializer
from config import DB_CONFIG, SCHEMA_FILE

def main():
    print("Initializing database...")
    print(f"Database: {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"Schema: {SCHEMA_FILE}")
    print()
    
    try:
        db_init = DatabaseInitializer(**DB_CONFIG)
        db_init.initialize(SCHEMA_FILE, drop_if_exists=True)
        
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
