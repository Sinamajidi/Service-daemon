#!/usr/bin/env python3
"""! @file db_init.py
@brief Database initialization entry point.

Run this script to initialize the database.

Usage:
    python database/db_init.py

Or from anywhere:
    python -m database.db_init
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
    """Execute SQL commands from a file."""
    # Read SQL file
    with open(sql_file_path, "r", encoding="utf-8") as f:
        sql = f.read()
        
    # Connect and execute
    with psycopg.connect(**db_conf) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()


def drop_all_tables(db_conf) -> None:
    """Drop all tables in the database (CASCADE to handle dependencies)."""
    with psycopg.connect(**db_conf) as conn:
        with conn.cursor() as cur:
            # Drop all tables in the public schema
            cur.execute("""
                DO $$ DECLARE
                    r RECORD;
                BEGIN
                    -- Drop all tables
                    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                    END LOOP;
                    
                    -- Drop all sequences
                    FOR r IN (SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public') LOOP
                        EXECUTE 'DROP SEQUENCE IF EXISTS ' || quote_ident(r.sequence_name) || ' CASCADE';
                    END LOOP;
                    
                    -- Drop all types
                    FOR r IN (SELECT typname FROM pg_type WHERE typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public') AND typtype = 'e') LOOP
                        EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
                    END LOOP;
                END $$;
            """)
        conn.commit()
        print("✓ All existing tables dropped")


class DatabaseInitializer:
    """! @brief Initializes the database schema and optional reset."""
    def __init__(self, db_config: dict):
        """! @brief Store database configuration for initialization."""
        self.db_host = db_config["DB_HOST"]
        self.db_port = db_config["DB_PORT"]
        self.db_name = db_config["DB_NAME"]
        self.db_user = db_config["DB_USER"]
        self.db_password = db_config["DB_PASSWORD"]
        self.db_config = {
            "host": self.db_host,
            "port": self.db_port,
            "dbname": self.db_name,
            "user": self.db_user,
            "password": self.db_password
        }
    
    def initialize(self, schema_file_path: str, drop_if_exists: bool = True):
        """! @brief Initialize the database schema.

        Args:
            schema_file_path: Path to the SQL schema file.
            drop_if_exists: If True, drop all existing tables before creating new ones.
        """
        if drop_if_exists:
            print("Dropping existing tables...")
            drop_all_tables(self.db_config)
        
        print("Creating tables from schema...")
        run_sql_file(schema_file_path, self.db_config)
        print("✓ Schema created successfully")


def main():
    """! @brief Initialize the database from the default schema file."""
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
        db_init.initialize(str(schema_file), drop_if_exists=True)
        
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
