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
import psycopg
import os
from dotenv import load_dotenv

# Add project root to path so imports work
# This script is in database/, so parent is the project root
sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

DB_CONFIG = {
    "DB_HOST": os.getenv("DB_HOST"),
    "DB_PORT": os.getenv("DB_PORT"),
    "DB_NAME": os.getenv("DB_NAME"),
    "DB_USER": os.getenv("DB_USER"),
    "DB_PASSWORD": os.getenv("DB_PASSWORD"),
}


def run_sql_file(sql_file_path: str, db_conf) -> None:
    # Read SQL file
    with open(sql_file_path, "r", encoding="utf-8") as f:
        sql = f.read()
        
    # Connect and execute
    with psycopg.connect(**db_conf) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()

class DatabaseInitializer:
    def __init__(self, db_config: dict):
        self.db_host=db_config["DB_HOST"]
        self.db_port=db_config["DB_PORT"]
        self.db_name=db_config["DB_NAME"]
        self.db_user=db_config["DB_USER"]
        self.db_password=db_config["DB_PASSWORD"]
        self.db_config = {
            "host": self.db_host,
            "port": self.db_port,
            "dbname": self.db_name,
            "user": self.db_user,
            "password": self.db_password
        }
    def initialize(self, schema_file_path: str, drop_if_exists: bool = True):
        run_sql_file(schema_file_path, self.db_config)
        pass


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
    print(f"Database: {DB_CONFIG['DB_NAME']}@{DB_CONFIG['DB_HOST']}:{DB_CONFIG['DB_PORT']}")
    print()
    
    try:
        db_init = DatabaseInitializer(DB_CONFIG)
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
        print(f"   psql -h {DB_CONFIG['DB_HOST']} -U {DB_CONFIG['DB_USER']} -d {DB_CONFIG['DB_NAME']}")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())
