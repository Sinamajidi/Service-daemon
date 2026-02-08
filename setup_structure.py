#!/usr/bin/env python3
"""
Setup Script for Apartment Management Project
This script creates the recommended directory structure and moves files to proper locations.

Usage:
    python setup_structure.py [--simple]

Options:
    --simple    Use the simpler directory structure (recommended for starting out)
    (default)   Use the full professional structure
"""

import os
import shutil
from pathlib import Path
import sys


def create_directory_structure(base_path: Path, simple: bool = True):
    """
    Create the directory structure.
    
    Args:
        base_path: Base path for the project
        simple: If True, use simpler structure; if False, use full structure
    """
    if simple:
        print("Creating SIMPLE directory structure...")
        directories = [
            'database',
            'examples',
            'docs',
        ]
    else:
        print("Creating FULL directory structure...")
        directories = [
            'src',
            'src/database',
            'src/models',
            'src/middleware',
            'src/gui',
            'database/schema',
            'database/migrations',
            'scripts',
            'tests',
            'tests/test_database',
            'tests/test_middleware',
            'docs',
            'examples',
        ]
    
    for directory in directories:
        dir_path = base_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created: {directory}/")
        
        # Create __init__.py files for Python packages
        if directory.startswith('src') or directory.startswith('tests'):
            init_file = dir_path / '__init__.py'
            if not init_file.exists():
                init_file.touch()
                print(f"    ✓ Created: {directory}/__init__.py")


def move_files_simple(base_path: Path):
    """Move files to simple structure."""
    print("\nMoving files to simple structure...")
    
    file_moves = {
        # Database files
        'db_init.py': 'database/db_init.py',
        'db_connection.py': 'database/db_connection.py',
        'data_access_layer.py': 'database/data_access_layer.py',
        'entity_access.py': 'database/entity_access.py',
        
        # Schema
        'Database_Scheme.sql': 'database/schema.sql',
        
        # Documentation
        'example_usage.py': 'examples/example_usage.py',
        'QUICK_START.py': 'docs/QUICK_START.md',
        'PROJECT_SUMMARY.md': 'docs/PROJECT_SUMMARY.md',
        
        # Root files (these stay in root)
        'README.md': 'README.md',
        'requirements.txt': 'requirements.txt',
        'config.py': 'config.py',
        '.gitignore': '.gitignore',
        '.env.example': '.env.example',
    }
    
    move_files(base_path, file_moves)
    
    # Create __init__.py for database package
    init_file = base_path / 'database' / '__init__.py'
    if not init_file.exists():
        init_file.touch()
        print(f"  ✓ Created: database/__init__.py")


def move_files_full(base_path: Path):
    """Move files to full structure."""
    print("\nMoving files to full structure...")
    
    file_moves = {
        # Config
        'config.py': 'src/config.py',
        
        # Database files
        'db_init.py': 'src/database/db_init.py',
        'db_connection.py': 'src/database/db_connection.py',
        'data_access_layer.py': 'src/database/data_access_layer.py',
        'entity_access.py': 'src/database/entity_access.py',
        
        # Schema
        'Database_Scheme.sql': 'database/schema/Database_Scheme.sql',
        
        # Documentation
        'example_usage.py': 'examples/example_usage.py',
        'QUICK_START.py': 'docs/QUICK_START.md',
        'PROJECT_SUMMARY.md': 'docs/PROJECT_SUMMARY.md',
        
        # Root files
        'README.md': 'README.md',
        'requirements.txt': 'requirements.txt',
        '.gitignore': '.gitignore',
        '.env.example': '.env.example',
    }
    
    move_files(base_path, file_moves)


def move_files(base_path: Path, file_moves: dict):
    """Move files according to the mapping."""
    for source, destination in file_moves.items():
        source_path = base_path / source
        dest_path = base_path / destination
        
        if source_path.exists():
            # Create parent directory if it doesn't exist
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            shutil.move(str(source_path), str(dest_path))
            print(f"  ✓ Moved: {source} → {destination}")
        else:
            print(f"  ⚠ Skipped (not found): {source}")


def update_imports_simple(base_path: Path):
    """Update imports for simple structure."""
    print("\nUpdating imports for simple structure...")
    
    # Files that need import updates
    files_to_update = {
        'database/entity_access.py': {
            'from data_access_layer import': 'from .data_access_layer import',
        },
        'database/data_access_layer.py': {
            'from db_connection import': 'from .db_connection import',
        },
        'examples/example_usage.py': {
            'from db_init import DatabaseInitializer': 'from database.db_init import DatabaseInitializer',
            'from db_connection import get_db': 'from database.db_connection import get_db',
            'from data_access_layer import get_dal': 'from database.data_access_layer import get_dal',
            'from entity_access import': 'from database.entity_access import',
            'from config import DB_CONFIG': 'from config import DB_CONFIG',
            'from pathlib import Path\nfrom datetime import': 'from pathlib import Path\nfrom datetime import',
            'import logging\n\n# Import our modules': 'import logging\nimport sys\n\n# Add project root to path\nsys.path.insert(0, str(Path(__file__).parent.parent))\n\n# Import our modules',
        },
        'docs/QUICK_START.py': {
            'from db_init import DatabaseInitializer': 'from database.db_init import DatabaseInitializer',
            'from entity_access import': 'from database.entity_access import',
            'from data_access_layer import get_dal': 'from database.data_access_layer import get_dal',
        },
        'config.py': {
            "SCHEMA_FILE = Path('/mnt/user-data/uploads/Database_Scheme.sql')": "SCHEMA_FILE = BASE_DIR / 'database' / 'schema.sql'",
        },
    }
    
    for file_path, replacements in files_to_update.items():
        full_path = base_path / file_path
        if not full_path.exists():
            print(f"  ⚠ Skipped (not found): {file_path}")
            continue
        
        try:
            content = full_path.read_text()
            updated = False
            
            for old_text, new_text in replacements.items():
                if old_text in content:
                    content = content.replace(old_text, new_text)
                    updated = True
            
            if updated:
                full_path.write_text(content)
                print(f"  ✓ Updated imports: {file_path}")
            else:
                print(f"  - No changes needed: {file_path}")
                
        except Exception as e:
            print(f"  ✗ Error updating {file_path}: {e}")
    
    # Create database/__init__.py
    create_database_init(base_path)


def update_imports_full(base_path: Path):
    """Update imports for full structure."""
    print("\nUpdating imports for full structure...")
    
    files_to_update = [
        'src/database/db_init.py',
        'src/database/entity_access.py',
        'examples/example_usage.py',
    ]
    
    import_replacements = {
        'from db_connection import': 'from src.database.db_connection import',
        'from data_access_layer import': 'from src.database.data_access_layer import',
        'from entity_access import': 'from src.database.entity_access import',
        'from db_init import': 'from src.database.db_init import',
        'from config import': 'from src.config import',
    }
    
    update_imports(base_path, files_to_update, import_replacements)


def update_imports(base_path: Path, files: list, replacements: dict):
    """Update imports in files."""
    for file_path in files:
        full_path = base_path / file_path
        if not full_path.exists():
            print(f"  ⚠ Skipped (not found): {file_path}")
            continue
        
        try:
            content = full_path.read_text()
            updated = False
            
            for old_import, new_import in replacements.items():
                if old_import in content:
                    content = content.replace(old_import, new_import)
                    updated = True
            
            if updated:
                full_path.write_text(content)
                print(f"  ✓ Updated imports: {file_path}")
            else:
                print(f"  - No changes needed: {file_path}")
                
        except Exception as e:
            print(f"  ✗ Error updating {file_path}: {e}")


def create_database_init(base_path: Path):
    """Create a proper __init__.py for the database package."""
    init_content = '''"""
Database Package
Provides database initialization, connection management, and data access.
"""

from .db_init import DatabaseInitializer
from .db_connection import DatabaseConnection, get_db
from .data_access_layer import DataAccessLayer, get_dal
from .entity_access import (
    User, Tenant, Unit, Booking,
    UserAccess, TenantAccess, UnitAccess, BookingAccess,
    get_user_access, get_tenant_access, get_unit_access, get_booking_access
)

__all__ = [
    # Initialization
    'DatabaseInitializer',
    
    # Connection
    'DatabaseConnection',
    'get_db',
    
    # Data Access Layer
    'DataAccessLayer',
    'get_dal',
    
    # Entity Classes
    'User',
    'Tenant',
    'Unit',
    'Booking',
    
    # Entity Access Classes
    'UserAccess',
    'TenantAccess',
    'UnitAccess',
    'BookingAccess',
    
    # Factory Functions
    'get_user_access',
    'get_tenant_access',
    'get_unit_access',
    'get_booking_access',
]
'''
    
    init_file = base_path / 'database' / '__init__.py'
    init_file.write_text(init_content)
    print(f"  ✓ Created: database/__init__.py")


def create_init_script(base_path: Path, simple: bool):
    """Create an initialization script in the scripts directory."""
    if simple:
        script_path = base_path / 'database' / 'init_db.py'
        schema_path = 'database/schema.sql'
    else:
        script_path = base_path / 'scripts' / 'init_db.py'
        schema_path = 'database/schema/Database_Scheme.sql'
    
    script_content = f'''#!/usr/bin/env python3
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
    schema_file = project_root / '{schema_path}'
    
    if not schema_file.exists():
        print(f"Error: Schema file not found at {{schema_file}}")
        print("Expected location: {schema_path}")
        return 1
    
    # Initialize database
    print("Initializing database...")
    print(f"Using schema: {{schema_file}}")
    print(f"Database: {{DB_CONFIG['database']}}@{{DB_CONFIG['host']}}:{{DB_CONFIG['port']}}")
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
        print(f"Error: {{e}}")
        print()
        print("Troubleshooting:")
        print("1. Make sure PostgreSQL is running:")
        print("   sudo service postgresql status")
        print("2. Check your .env file has correct credentials")
        print("3. Test connection manually:")
        print(f"   psql -h {{DB_CONFIG['host']}} -U {{DB_CONFIG['user']}} -d {{DB_CONFIG['database']}}")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())
'''
    
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(script_content)
    script_path.chmod(0o755)  # Make executable
    print(f"  ✓ Created initialization script: {script_path}")


def main():
    """Main setup function."""
    print("=" * 70)
    print("APARTMENT MANAGEMENT PROJECT - DIRECTORY SETUP")
    print("=" * 70)
    print()
    
    # Check for --simple flag
    simple = '--simple' in sys.argv or len(sys.argv) == 1
    
    if simple:
        print("Setting up SIMPLE structure (recommended for starting out)")
    else:
        print("Setting up FULL professional structure")
    
    print()
    
    # Get current directory
    base_path = Path.cwd()
    print(f"Base directory: {base_path}")
    print()
    
    # Create directory structure
    create_directory_structure(base_path, simple)
    
    # Move files
    if simple:
        move_files_simple(base_path)
        update_imports_simple(base_path)
    else:
        move_files_full(base_path)
        update_imports_full(base_path)
    
    # Create initialization script
    create_init_script(base_path, simple)
    
    print()
    print("=" * 70)
    print("✓ SETUP COMPLETE!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Copy .env.example to .env and fill in your database credentials:")
    print("   cp .env.example .env")
    print()
    print("2. Add files to your existing Git repository:")
    print("   git add .")
    print("   git commit -m 'Add database and communication layer'")
    print("   git push")
    print()
    print("3. Your collaborators can pull the changes:")
    print("   git pull")
    print()
    print("4. Initialize the database:")
    if simple:
        print("   python database/init_db.py")
    else:
        print("   python scripts/init_db.py")
    print()
    print("5. Run the example:")
    print("   python examples/example_usage.py")
    print()


if __name__ == '__main__':
    main()
