# Getting Started - Complete Setup Guide

This guide outlines the full setup process.

## Prerequisites

- Git (for cloning/pulling the repository)
- Python 3.7+ (`python --version`)
- PostgreSQL OR Docker

---

## Setup Steps

### Step 1: Retrieve the code

```bash
# If starting fresh
git clone <your-repo-url>
cd Service-daemon

# If already cloned
cd Service-daemon
git pull
```

### Step 2: Set up the Python environment (recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On WSL/Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Prompt should display (venv)
```

### Step 3: Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set up PostgreSQL

**Option A: Automated Setup (WSL/Linux)**
```bash
./setup_postgresql.sh
```
This will:
- Install PostgreSQL if needed
- Start the service
- Create the database
- Set up your .env file

**Option B: Manual Setup**
See `POSTGRESQL_SETUP_GUIDE.md` for detailed instructions for:
- WSL/Linux
- macOS
- Windows
- Docker

### Step 5: Verify setup

```bash
# Run diagnostic test
python diagnostic_test.py

# Run full test
python test_setup.py
```

Both checks should complete successfully.

### Step 6: Initialize the database

```bash
# This creates all tables and schema
python database/db_init.py
```

Expected output:
```
Initializing database...
Database initialized successfully!
```

### Step 7: Run the example

```bash
python examples/example_usage.py
```

The example creates sample data and runs queries.

### Step 8: Optional SQL execution

Place manual SQL files in `manual_sql/` to expose them in the GUI SQL Query Execution tab.
The `manual_sql/task_templates_seed.sql` file can be run to insert the baseline task templates.

---

## Troubleshooting

### Import errors
```bash
# Make sure you're in project root
pwd

# Verify structure
python test_setup.py
```

### Database connection errors
```bash
# Check PostgreSQL is running
# WSL/Linux:
sudo service postgresql status

# macOS:
brew services list

# Check your .env file
cat .env
```

### "Module not found" errors
```bash
# Make sure dependencies are installed
pip install -r requirements.txt

# Check you're in the virtual environment
which python
# Should show path with 'venv' in it
```

---

## Project Structure

Expected structure after setup:

```
Service-daemon/
├── .env                    # Your database credentials
├── .env.example           # Template
├── requirements.txt       # Python packages
├── config.py             # Configuration
│
├── database/             # Database layer
│   ├── __init__.py
│   ├── schema.sql        # Database schema
│   ├── db_init.py       # Initialization
│   ├── db_connection.py # Connection management
│   ├── data_access_layer.py
│   └── entity_access.py
│
├── examples/
│   └── example_usage.py  # Demo code
│
├── docs/
│   └── ... documentation
│
├── gui_app.py            # Desktop GUI
├── gui_app_info.json     # Info tab configuration
├── init_database.py      # Convenience init wrapper
├── sql_setup/            # Optional SQL scripts
│   └── task_tables.sql
├── manual_sql/           # SQL files exposed in the GUI
│   └── task_templates_seed.sql
└── tests/                # Tests (future)
```

---

## Daily Workflow

### Starting Work

```bash
# 1. Pull latest changes
git pull

# 2. Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Start PostgreSQL (if not auto-started)
sudo service postgresql start  # WSL/Linux
# OR
brew services start postgresql@15  # macOS
# OR
docker start apartment-postgres  # Docker
```

### Testing Your Changes

```bash
# Quick test
python diagnostic_test.py

# Full test
python test_setup.py

# Test specific functionality
python examples/example_usage.py
```

### Committing Changes

```bash
git add .
git commit -m "Description of changes"
git push
```

---

## Common Commands

### Database Management

```bash
# Connect to database
psql -h localhost -U postgres -d apartment_mgmt

# Reinitialize database (DROPS ALL DATA!)
python database/db_init.py

# In psql shell:
\l          # List databases
\dt         # List tables
\d+ users   # Describe users table
\q          # Quit
```

### Python

```bash
# Install new package
pip install package-name
pip freeze > requirements.txt  # Update requirements

# Run Python REPL with imports
python
>>> from database import get_user_access
>>> users = get_user_access()
>>> users.get_all_user_ids()
```

### Git

```bash
git status              # See what's changed
git diff                # See changes
git log                 # See commit history
git pull                # Get updates from team
git push                # Send your changes
```

---

## For Team Members

If you're a collaborator joining the project:

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd Service-daemon
   ```

2. **Follow Steps 2-7 above**

3. **Your own .env file**
   ```bash
   cp .env.example .env
   nano .env  # Edit with YOUR credentials
   ```
   Never commit your .env file!

4. **Stay synced**
   ```bash
   git pull  # Before starting work
   git push  # After committing changes
   ```

See `TEAM_SETUP.md` for more details.

---

## Configuration Files

### .env (Your Credentials)
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=apartment_mgmt
DB_USER=postgres
DB_PASSWORD=your_password
```

**NEVER commit this file to Git!** (It's in .gitignore)

### .env.example (Template)
This IS committed to Git. It shows others what variables they need.

---

## Next Steps

Now that you have the database layer working, you can:

1. **Add more data models** - Create access classes for other entities (providers, invoices, etc.)

2. **Build the middle layer** - Add business logic, validation, etc.

3. **Connect to GUI** - Integrate with your GUI framework

4. **Add tests** - Write unit tests for your functions

5. **Add features** - Implement booking logic, notifications, etc.

---

## Getting Help

1. **Check the guides:**
   - `POSTGRESQL_SETUP_GUIDE.md` - Database setup
   - `MIGRATION_GUIDE.md` - Fixing structure issues
   - `TEAM_SETUP.md` - For collaborators
   - `README.md` - Full documentation

2. **Run diagnostics:**
   ```bash
   python diagnostic_test.py
   python test_setup.py
   ```

3. **Check logs:**
   - PostgreSQL logs: `sudo journalctl -u postgresql`
   - Application errors: Check terminal output

---

## Summary Checklist

- [ ] Code downloaded/cloned
- [ ] Virtual environment created and activated
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] PostgreSQL installed and running
- [ ] Database created
- [ ] `.env` file configured
- [ ] `diagnostic_test.py` passes
- [ ] `test_setup.py` passes
- [ ] `database/db_init.py` runs successfully
- [ ] `examples/example_usage.py` works

Once all are checked, you're ready to start developing! 🚀
