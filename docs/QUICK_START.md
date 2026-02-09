# Quick Start

This guide covers the minimum steps to get the Service Daemon data layer and GUI running.

## 1) Install dependencies

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## 2) Configure PostgreSQL

Create a `.env` file in the project root (or run `./setup_postgresql.sh` on WSL/Linux):

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=apartment_mgmt
DB_USER=postgres
DB_PASSWORD=your_password_here
```

## 3) Initialize the schema

```bash
python database/db_init.py
```

## 4) Run the example

```bash
python examples/example_usage.py
```

## 5) Launch the GUI (optional)

```bash
python gui_app.py
# or
python -m gui_app
```

## Minimal code sample

```python
from database.entity_access import get_user_access

user_access = get_user_access()
user_ids = user_access.get_all_user_ids()

if user_ids:
    user_data = user_access.get_user_data(user_ids[0])
    print(user_data)
```

## Optional task tables

If you plan to use task templates or instances, load the optional SQL script from the GUI
(SQL panel) or run it manually:

```bash
psql -h localhost -U postgres -d apartment_mgmt -f sql_setup/task_tables.sql
```
