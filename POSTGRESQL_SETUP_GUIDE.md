# How to Install and Run PostgreSQL

## Quick Detection - What System Are You On?

Run this to find out:
```bash
uname -a
```

- Contains "microsoft" or "WSL" → You're on **WSL (Windows Subsystem for Linux)**
- Contains "Darwin" → You're on **macOS**
- Contains "Linux" (no microsoft) → You're on **native Linux**
- On Windows PowerShell/CMD → You're on **Windows**

---

## Option 1: WSL (Windows Subsystem for Linux) - RECOMMENDED FOR YOU

Based on your path, you're likely using WSL. Here's how to set it up:

### Step 1: Install PostgreSQL in WSL

```bash
# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Check version
psql --version
```

### Step 2: Start PostgreSQL Service

```bash
# Start PostgreSQL
sudo service postgresql start

# Check if it's running
sudo service postgresql status
# Should say "online" or "running"
```

### Step 3: Set Up PostgreSQL User and Database

```bash
# Switch to postgres user
sudo -u postgres psql

# You're now in PostgreSQL shell (postgres=#)
# Run these commands:
```

In the PostgreSQL shell:
```sql
-- Create a password for postgres user
ALTER USER postgres PASSWORD 'your_password_here';

-- Create your database
CREATE DATABASE apartment_mgmt;

-- Check it was created
\l

-- Exit PostgreSQL shell
\q
```

### Step 4: Test Connection

```bash
# Try connecting to your database
psql -h localhost -U postgres -d apartment_mgmt

# If it asks for password, enter the one you set above
# You should see: apartment_mgmt=#
# Type \q to exit
```

### Step 5: Configure Your .env File

```bash
# In your project directory
cd /path/to/your/project

# Edit .env file
nano .env
```

Set these values:
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=apartment_mgmt
DB_USER=postgres
DB_PASSWORD=your_password_here  # The password you set in Step 3
```

### Step 6: Initialize Your Database

```bash
# Run the initialization script
python database/init_db.py
```

### Auto-start PostgreSQL on WSL Boot (Optional)

Add this to your `~/.bashrc` or `~/.zshrc`:
```bash
# Auto-start PostgreSQL
if ! service postgresql status > /dev/null 2>&1; then
    sudo service postgresql start
fi
```

---

## Option 2: Native Linux

### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql  # Auto-start on boot
sudo systemctl status postgresql
```

### Fedora/RHEL/CentOS:
```bash
sudo dnf install postgresql-server postgresql-contrib
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl status postgresql
```

Then follow Steps 3-6 from WSL section above.

---

## Option 3: macOS

### Using Homebrew (Recommended):
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL
brew services start postgresql@15

# Check status
brew services list | grep postgresql
```

### Create Database:
```bash
# Create user (if needed)
createuser -s postgres

# Create database
createdb apartment_mgmt

# Set password
psql postgres
```

In psql:
```sql
ALTER USER postgres PASSWORD 'your_password';
\q
```

Then follow Steps 5-6 from WSL section above.

---

## Option 4: Windows (Native)

### Download and Install:

1. **Download PostgreSQL:**
   - Go to: https://www.postgresql.org/download/windows/
   - Download the installer (usually PostgreSQL 15 or 16)
   - Run the installer

2. **During Installation:**
   - Set a password for the `postgres` user (remember this!)
   - Port: 5432 (default)
   - Locale: Default
   - Install with default components

3. **PostgreSQL should auto-start**

### Verify Installation:

Open Command Prompt or PowerShell:
```cmd
# Add PostgreSQL to PATH if needed, then:
psql -U postgres

# In psql shell:
CREATE DATABASE apartment_mgmt;
\q
```

### Configure .env:
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=apartment_mgmt
DB_USER=postgres
DB_PASSWORD=password_you_set_during_install
```

---

## Option 5: Docker (Easiest - Works Everywhere)

If you have Docker installed:

### Step 1: Run PostgreSQL in Docker

```bash
docker run --name apartment-postgres \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -e POSTGRES_DB=apartment_mgmt \
  -p 5432:5432 \
  -d postgres:15
```

### Step 2: Verify It's Running

```bash
docker ps | grep apartment-postgres
```

### Step 3: Configure .env

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=apartment_mgmt
DB_USER=postgres
DB_PASSWORD=mysecretpassword
```

### Useful Docker Commands:

```bash
# Stop PostgreSQL
docker stop apartment-postgres

# Start PostgreSQL
docker start apartment-postgres

# Connect to PostgreSQL
docker exec -it apartment-postgres psql -U postgres -d apartment_mgmt

# Remove container (data will be lost!)
docker rm -f apartment-postgres
```

---

## Common Issues and Solutions

### "Could not connect to server"

**Check if PostgreSQL is running:**
```bash
# WSL/Linux:
sudo service postgresql status

# macOS:
brew services list

# Docker:
docker ps
```

**Start if not running:**
```bash
# WSL/Linux:
sudo service postgresql start

# macOS:
brew services start postgresql@15

# Docker:
docker start apartment-postgres
```

### "password authentication failed for user postgres"

Your password in `.env` doesn't match the database password.

**Reset password:**
```bash
sudo -u postgres psql
```
```sql
ALTER USER postgres PASSWORD 'newpassword';
\q
```

Then update `.env` with the new password.

### "database does not exist"

Create the database:
```bash
# Method 1: Using psql
sudo -u postgres psql
CREATE DATABASE apartment_mgmt;
\q

# Method 2: Using createdb command
sudo -u postgres createdb apartment_mgmt
```

### "port 5432 already in use"

Another PostgreSQL instance is running, or another app is using that port.

**Find what's using the port:**
```bash
# Linux/WSL/macOS:
sudo lsof -i :5432

# Windows:
netstat -ano | findstr :5432
```

### "peer authentication failed"

PostgreSQL is trying to use system user authentication instead of password.

**Fix:** Edit `pg_hba.conf`:
```bash
# Find the file
sudo find / -name pg_hba.conf 2>/dev/null

# Edit it (example path)
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Change this line:
# local   all   postgres   peer
# To:
local   all   postgres   md5

# Save and restart PostgreSQL
sudo service postgresql restart
```

---

## Testing Your Setup

After setting up PostgreSQL, run these tests:

### Test 1: Can you connect?
```bash
psql -h localhost -U postgres -d apartment_mgmt
# Enter password when prompted
# Should show: apartment_mgmt=#
```

### Test 2: Run diagnostic test
```bash
cd /path/to/your/project
python diagnostic_test.py
```

### Test 3: Initialize database
```bash
python database/init_db.py
```

### Test 4: Run example
```bash
python examples/example_usage.py
```

---

## Quick Reference

| Task | WSL/Linux | macOS | Docker |
|------|-----------|-------|--------|
| **Start** | `sudo service postgresql start` | `brew services start postgresql@15` | `docker start apartment-postgres` |
| **Stop** | `sudo service postgresql stop` | `brew services stop postgresql@15` | `docker stop apartment-postgres` |
| **Status** | `sudo service postgresql status` | `brew services list` | `docker ps` |
| **Connect** | `psql -U postgres` | `psql postgres` | `docker exec -it apartment-postgres psql -U postgres` |
| **Logs** | `sudo journalctl -u postgresql` | `brew services info postgresql@15` | `docker logs apartment-postgres` |

---

## Recommended for Your Setup (WSL)

Based on your system, here's the quickest path:

```bash
# 1. Install
sudo apt update && sudo apt install postgresql postgresql-contrib -y

# 2. Start
sudo service postgresql start

# 3. Set up database
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'mypassword';"
sudo -u postgres psql -c "CREATE DATABASE apartment_mgmt;"

# 4. Configure .env
echo "DB_HOST=localhost
DB_PORT=5432
DB_NAME=apartment_mgmt
DB_USER=postgres
DB_PASSWORD=mypassword" > .env

# 5. Test
psql -h localhost -U postgres -d apartment_mgmt
```

Then run: `python database/init_db.py`

Done! 🎉
