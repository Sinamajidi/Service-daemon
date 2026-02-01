#!/usr/bin/env python3
"""
Database Initialization Script
Run this script to initialize the database.

Usage:
    python init_db.py
"""

from pathlib import Path
from database.db_init import DatabaseInitializer
from config import DB_CONFIG

def main():
    """Initialize the database."""
    # Get the schema file path
    base_dir = Path(__file__).parent.parent
    schema_file = base_dir / 'database/schema.sql'
    
    if not schema_file.exists():
        print(f"Error: Schema file not found at {schema_file}")
        return
    
    # Initialize database
    print("Initializing database...")
    db_init = DatabaseInitializer(**DB_CONFIG)
    db_init.initialize(schema_file, drop_if_exists=True)
    
    print("✓ Database initialized successfully!")

if __name__ == '__main__':
    main()
