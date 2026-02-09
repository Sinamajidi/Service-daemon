# Service Daemon

Service Daemon is a Python + PostgreSQL data layer and demo app for managing apartment service workflows (users, units, tenants, service types, bookings, and provider assignments). It ships with a database schema, helpers for initialization/connection pooling, and an example script to show common reads/writes.

If you are new, follow the **Novice Setup** below. If you are experienced and want more control, skip to **Senior Setup**.

---

## Novice Setup (step-by-step)

### 1) Install prerequisites

- **Python 3.7+**
- **PostgreSQL** (local or Docker)
- **Git** (only if you need to clone the repo)

### 2) Get the code

```bash
git clone <your-repo-url>
cd Service-daemon
```

### 3) Create a virtual environment (recommended)

```bash
python -m venv venv

# macOS / Linux / WSL
source venv/bin/activate

# Windows PowerShell
venv\Scripts\Activate.ps1
```

### 4) Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5) Set up PostgreSQL

**Easy option (Linux/WSL):**

```bash
./setup_postgresql.sh
```

This script installs PostgreSQL if needed, starts the service, creates the database, and sets up your `.env` file.

**Manual option (macOS/Windows/Linux/Docker):**

Follow the instructions in `POSTGRESQL_SETUP_GUIDE.md`.

### 6) Configure your database connection

If you used the script, a `.env` file should already exist. Otherwise, create one at the project root with:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=apartment_mgmt
DB_USER=postgres
DB_PASSWORD=your_password_here
```

> These values are read in `config.py` and used by the database helpers.

### 7) Initialize the database schema

```bash
python database/db_init.py
```

Alternatively, you can run the convenience wrapper:

```bash
python init_database.py
```

You should see “Database initialized successfully!”.

### 8) Try the example usage

```bash
python examples/example_usage.py
```

This creates sample data (buildings, units, tenants, bookings) and prints results.

### 9) (Optional) Run the GUI

```bash
python gui_app.py
```

The GUI lets you test DB connectivity and inspect booking data in a desktop interface.

### 10) Run diagnostics

```bash
python diagnostic_test.py
python test_setup.py
```

If these complete without errors, your setup is correct.

---

## Senior Setup (fast + configurable)

### Quick install

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Database configuration

The project reads DB settings from environment variables (or `.env`) in `config.py`:

- `DB_HOST` (default: `localhost`)
- `DB_PORT` (default: `5432`)
- `DB_NAME` (default: `apartment_mgmt`)
- `DB_USER` (default: `postgres`)
- `DB_PASSWORD` (default: `postgres`)

Set them in your shell or `.env` before running scripts:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=apartment_mgmt
export DB_USER=postgres
export DB_PASSWORD=postgres
```

### Schema + initialization

The schema lives at `database/schema.sql`. Initialize or reset via:

```bash
python database/db_init.py
```

### Core usage (data access layer)

- **Connection pooling:** `database/db_connection.py`
- **DAL helpers:** `database/data_access_layer.py`
- **Entity accessors:** `database/entity_access.py`

Example snippet:

```python
from database.entity_access import get_user_access

user_access = get_user_access()
user_ids = user_access.get_all_user_ids()
```

The repository includes `examples/example_usage.py` for a full walkthrough of reads/writes and entity creation.

### Useful scripts

- `diagnostic_test.py`: quick checks for Python path, imports, and DB connectivity
- `test_setup.py`: larger end-to-end validation
- `init_database.py`: convenience wrapper for initializing the schema
- `setup_postgresql.sh`: WSL/Linux PostgreSQL setup automation
- `sql_setup/`: optional SQL scripts (loaded via the GUI SQL panel)

---

## Project layout

```
.
├── config.py
├── database/
│   ├── schema.sql
│   ├── db_init.py
│   ├── db_connection.py
│   ├── data_access_layer.py
│   └── entity_access.py
├── examples/
│   └── example_usage.py
├── init_database.py
├── gui_app.py
├── diagnostic_test.py
├── sql_setup/
│   └── task_tables.sql
└── test_setup.py
```

---

## Need more detail?

- Full setup guide: `GETTING_STARTED.md`
- PostgreSQL walkthrough: `POSTGRESQL_SETUP_GUIDE.md`
