#!/usr/bin/env python3
"""
Diagnostic Test - Find Which Import is Hanging

This script tests each import individually to identify the problem.
"""

import sys
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("="*70)
print("DIAGNOSTIC IMPORT TEST")
print("="*70)
print()

def test_import(module_name, import_statement):
    """Test a single import and report if it hangs."""
    print(f"Testing: {import_statement}")
    start = time.time()
    
    try:
        exec(import_statement)
        elapsed = time.time() - start
        print(f"  ✓ Success ({elapsed:.2f}s)")
        return True
    except ImportError as e:
        print(f"  ✗ ImportError: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

# Test imports one by one
print("Testing basic imports...")
test_import("pathlib", "from pathlib import Path")
test_import("datetime", "from datetime import datetime")
print()

print("Testing config...")
test_import("config", "from config import DB_CONFIG")
print()

print("Testing database.db_connection...")
test_import("database.db_connection", "from database import db_connection")
print()

print("Testing database.db_init...")
test_import("database.db_init", "from database.db_init import DatabaseInitializer")
print()

print("Testing database.data_access_layer...")
test_import("database.data_access_layer", "from database.data_access_layer import get_dal")
print()

print("Testing database.entity_access...")
test_import("database.entity_access", "from database.entity_access import get_user_access")
print()

print("Testing full database import...")
test_import("database", "from database import get_db, get_dal, get_user_access")
print()

print("="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70)
print()
print("If any import took more than 2-3 seconds, that's the problem.")
print("Check that module for issues (database connections, file operations, etc.)")
