#!/usr/bin/env python3
"""
Test Script - Verify Folder Structure and Imports

Run this from the project root to verify everything is set up correctly.
Usage: python test_setup.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("="*70)
print("TESTING PROJECT STRUCTURE AND IMPORTS")
print("="*70)
print()

# Test 1: Check directory structure
print("Test 1: Checking directory structure...")
required_dirs = ['database', 'examples', 'docs']
required_files = [
    'config.py',
    'requirements.txt',
    'database/__init__.py',
    'database/db_init.py',
    'database/db_connection.py',
    'database/data_access_layer.py',
    'database/entity_access.py',
    'database/schema.sql',
]

all_good = True
for dirname in required_dirs:
    if Path(dirname).is_dir():
        print(f"  ✓ {dirname}/ exists")
    else:
        print(f"  ✗ {dirname}/ MISSING")
        all_good = False

for filename in required_files:
    if Path(filename).is_file():
        print(f"  ✓ {filename} exists")
    else:
        print(f"  ✗ {filename} MISSING")
        all_good = False

if not all_good:
    print("\n❌ Directory structure incomplete!")
    print("Run: python setup_structure.py --simple")
    sys.exit(1)

print("  ✓ Directory structure OK\n")

# Test 2: Check imports
print("Test 2: Testing imports...")
try:
    from database import DatabaseInitializer
    print("  ✓ from database import DatabaseInitializer")
except ImportError as e:
    print(f"  ✗ Failed to import DatabaseInitializer: {e}")
    all_good = False

try:
    from database import get_db
    print("  ✓ from database import get_db")
except ImportError as e:
    print(f"  ✗ Failed to import get_db: {e}")
    all_good = False

try:
    from database import get_dal
    print("  ✓ from database import get_dal")
except ImportError as e:
    print(f"  ✗ Failed to import get_dal: {e}")
    all_good = False

try:
    from database.entity_access import get_user_access, get_booking_access
    print("  ✓ from database.entity_access import get_user_access, get_booking_access")
except ImportError as e:
    print(f"  ✗ Failed to import entity access: {e}")
    all_good = False

try:
    from config import DB_CONFIG, SCHEMA_FILE
    print("  ✓ from config import DB_CONFIG, SCHEMA_FILE")
except ImportError as e:
    print(f"  ✗ Failed to import config: {e}")
    all_good = False

if not all_good:
    print("\n❌ Import tests failed!")
    sys.exit(1)

print("  ✓ All imports OK\n")

# Test 3: Check schema file path
print("Test 3: Checking schema file path...")
try:
    from config import SCHEMA_FILE
    if SCHEMA_FILE.exists():
        print(f"  ✓ Schema file found: {SCHEMA_FILE}")
    else:
        print(f"  ⚠ Schema file not found: {SCHEMA_FILE}")
        print(f"    Make sure your Database_Scheme.sql is in database/schema.sql")
except Exception as e:
    print(f"  ✗ Error checking schema: {e}")

print()

# Test 4: Check .env file
print("Test 4: Checking configuration...")
env_file = Path('.env')
env_example = Path('.env.example')

if env_file.exists():
    print("  ✓ .env file exists")
    print("    Remember: Each team member needs their own .env with their credentials")
else:
    if env_example.exists():
        print("  ⚠ .env file not found")
        print("    Run: cp .env.example .env")
        print("    Then edit .env with your database credentials")
    else:
        print("  ✗ .env.example not found")

print()

# Summary
print("="*70)
if all_good:
    print("✅ ALL TESTS PASSED!")
    print("="*70)
    print()
    print("Next steps:")
    if not env_file.exists():
        print("1. Create .env file: cp .env.example .env")
        print("2. Edit .env with your database credentials")
        print("3. Initialize database: python database/init_db.py")
    else:
        print("1. Initialize database: python database/init_db.py")
        print("2. Run example: python examples/example_usage.py")
else:
    print("❌ SOME TESTS FAILED")
    print("="*70)
    print()
    print("Fix the issues above, then run this test again.")

print()
