#!/usr/bin/env python3
"""
Database Initialization Script
Run this script to initialize the database.

Usage:
    python database/init_db.py
    
Or from anywhere:
    python -m database.init_db
"""

import sys
from pathlib import Path

# Add project root to path so imports work
# This script is in database/, so parent is the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_init import DatabaseInitializer
from config import DB_CONFIG

def main():
    """Initialize the database."""
    # Get the schema file path (relative to project root)
    project_root = Path(__file__).parent.parent
    schema_file = project_root / 'database' / 'schema.sql'
    
    if not schema_file.exists():
        print(f"Error: Schema file not found at {schema_file}")
        print("Expected location: database/schema.sql")
        return 1
    
    # Initialize database
    print("Initializing database...")
    print(f"Using schema: {schema_file}")
    print(f"Database: {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print()
    
    try:
        db_init = DatabaseInitializer(**DB_CONFIG)
        db_init.initialize(schema_file, drop_if_exists=True)
        
        print()
        print("="*60)
        print("✓ Database initialized successfully!")
        print("="*60)
        print()
        print("Next steps:")
        print("  python examples/example_usage.py")
        print()
        return 0
        
    except Exception as e:
        print()
        print("="*60)
        print("✗ Database initialization failed!")
        print("="*60)
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Make sure PostgreSQL is running:")
        print("   sudo service postgresql status")
        print("2. Check your .env file has correct credentials")
        print("3. Test connection manually:")
        print(f"   psql -h {DB_CONFIG['host']} -U {DB_CONFIG['user']} -d {DB_CONFIG['database']}")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())
