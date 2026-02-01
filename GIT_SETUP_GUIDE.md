# Git Setup Guide - Step by Step

## Quick Answer: Use the Simple Structure

**Yes, for now, I recommend the SIMPLE structure:**

```
apartment-management/
├── database/           # All database code
├── config.py          # Configuration
├── examples/          # Example code
├── docs/              # Documentation
├── .gitignore
├── .env.example
├── README.md
└── requirements.txt
```

## Complete Setup Instructions

### Option 1: Automated Setup (RECOMMENDED)

I've created a script that does everything for you!

#### Step 1: Download all files to your existing repository
```bash
# Navigate to your existing repository
cd /path/to/your/existing/repo

# Copy all the files I provided into this directory
```

#### Step 2: Run the setup script
```bash
# For simple structure (RECOMMENDED)
python setup_structure.py --simple

# OR for full professional structure
python setup_structure.py
```

The script will:
- ✅ Create all necessary directories
- ✅ Move files to the right locations
- ✅ Update all import statements
- ✅ Create initialization scripts

#### Step 3: Configure environment and commit
```bash
# Create .env file from template
cp .env.example .env

# Edit .env with your database credentials
nano .env  # or use your preferred editor

# Add all files to Git
git add .

# Make first commit
git commit -m "Add database and communication layer"

# Push to your existing repository
git push
```

Done! 🎉

---

### Option 2: Manual Setup (If You Prefer)

If you want to understand what's happening:

#### Step 1: Create directory structure in your existing repo
```bash
# Navigate to your existing repository
cd /path/to/your/existing/repo

# Create directories
mkdir database examples docs

# Create __init__.py for Python package
touch database/__init__.py
```

#### Step 2: Move files manually
```bash
# Move database files
mv db_init.py database/
mv db_connection.py database/
mv data_access_layer.py database/
mv entity_access.py database/

# Move schema
mv Database_Scheme.sql database/schema.sql

# Move documentation
mv example_usage.py examples/
mv QUICK_START.py docs/QUICK_START.md
mv PROJECT_SUMMARY.md docs/

# Keep in root
# - README.md
# - requirements.txt
# - config.py
# - .gitignore
# - .env.example
```

#### Step 3: Update imports in files

**In `database/db_init.py`, `database/entity_access.py`:**
```python
# Change this:
from db_connection import get_db

# To this:
from database.db_connection import get_db
```

**In `examples/example_usage.py`:**
```python
# Change:
from db_init import DatabaseInitializer
from entity_access import get_user_access

# To:
from database.db_init import DatabaseInitializer
from database.entity_access import get_user_access
```

#### Step 4: Create initialization script

Create `database/init_db.py`:
```python
#!/usr/bin/env python3
from pathlib import Path
from database.db_init import DatabaseInitializer
from config import DB_CONFIG

schema_file = Path(__file__).parent / 'schema.sql'
db_init = DatabaseInitializer(**DB_CONFIG)
db_init.initialize(schema_file, drop_if_exists=True)
print("✓ Database initialized!")
```

#### Step 5: Configure environment and commit
```bash
# Create .env from template
cp .env.example .env
# Edit .env with your credentials

# Add files to your existing repository
git add .

# Commit
git commit -m "Add database and communication layer"

# Push to your existing remote repository
git push
```

---

## Final Directory Structure (Simple)

After setup, you'll have:

```
apartment-management/
│
├── .git/                      # Git repository (created by git init)
├── .gitignore                 # Tells Git what to ignore
├── .env.example               # Template for environment variables
├── .env                       # Your actual credentials (NOT in Git)
│
├── README.md                  # Main documentation
├── requirements.txt           # Python dependencies
├── config.py                  # Configuration settings
│
├── database/                  # Database layer
│   ├── __init__.py
│   ├── schema.sql            # Database schema
│   ├── db_init.py            # Initialization
│   ├── db_connection.py      # Connection management
│   ├── data_access_layer.py  # Generic operations
│   ├── entity_access.py      # Entity-specific access
│   └── init_db.py            # Script to initialize DB
│
├── examples/                  # Example code
│   └── example_usage.py
│
└── docs/                      # Documentation
    ├── QUICK_START.md
    └── PROJECT_SUMMARY.md
```

## Verifying Your Setup

### Test 1: Check directory structure
```bash
tree -L 2 -I '.git|__pycache__'
```

### Test 2: Check imports
```bash
# This should work without errors:
python -c "from database.db_connection import get_db; print('✓ Imports work!')"
```

### Test 3: Initialize database
```bash
# Make sure .env is configured first!
python database/init_db.py
```

### Test 4: Run example
```bash
python examples/example_usage.py
```

## Git Best Practices

### What to commit:
- ✅ All `.py` files
- ✅ `requirements.txt`
- ✅ `.gitignore`
- ✅ `.env.example` (template only!)
- ✅ `README.md` and documentation
- ✅ SQL schema files

### What NOT to commit:
- ❌ `.env` (contains passwords!)
- ❌ `__pycache__/` directories
- ❌ `.venv/` or `venv/` (virtual environment)
- ❌ `.idea/`, `.vscode/` (IDE settings)
- ❌ Database files (`.db`, `.sqlite`)
- ❌ Log files

The `.gitignore` file I created handles all of this automatically.

## Using Environment Variables

### Step 1: Create .env file
```bash
cp .env.example .env
```

### Step 2: Edit with your credentials
```bash
# .env file content:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=apartment_mgmt
DB_USER=postgres
DB_PASSWORD=your_actual_password
```

### Step 3: The config.py file reads from .env
The `config.py` file automatically reads these values:
```python
import os

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    # ...
}
```

### Important for Team Collaboration

**Each team member needs their own `.env` file:**
- `.env.example` is committed to Git (it's a template)
- `.env` is in `.gitignore` (NOT committed - contains passwords)
- Each person creates their own `.env` from the template
- Each person uses their own database credentials

Your friend should:
1. Pull the repository: `git pull`
2. Copy the template: `cp .env.example .env`
3. Edit `.env` with their own database credentials
4. Never commit their `.env` file (it's already ignored)

## Common Git Commands

```bash
# Check status
git status

# Add new files
git add filename.py

# Add all changed files
git add .

# Commit changes
git commit -m "Description of changes"

# Push to remote
git push

# Pull from remote
git pull

# Create a new branch
git checkout -b feature-name

# Switch branches
git checkout main
```

## Troubleshooting

### Import errors after moving files?
Make sure you updated all import statements. Run:
```bash
grep -r "from db_init import" .
grep -r "from entity_access import" .
```

If you see any in your moved files, they need updating.

### Git ignoring files you want to track?
Check your `.gitignore` file. Make sure the file pattern isn't listed there.

### Database connection errors?
1. Check your `.env` file has correct credentials
2. Make sure PostgreSQL is running
3. Verify the database user has proper permissions

## Summary

**Recommended approach:**
1. ✅ Use the automated setup script: `python setup_structure.py --simple`
2. ✅ Configure `.env` file with your database credentials
3. ✅ Add to your existing Git repository: `git add . && git commit -m "Add database layer" && git push`
4. ✅ Test: `python examples/example_usage.py`
5. ✅ Your friend can pull: `git pull` to get the changes

This gives you a clean, professional structure that's easy to work with and expand later!
