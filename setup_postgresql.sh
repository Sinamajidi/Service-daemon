#!/bin/bash
##! @file setup_postgresql.sh
##  @brief PostgreSQL quick setup script for WSL/Linux.
##
##  This script automates PostgreSQL installation and setup.
# PostgreSQL Quick Setup Script for WSL/Linux
# This script automates the PostgreSQL installation and setup

set -e  # Exit on error

echo "=========================================="
echo "PostgreSQL Setup for Apartment Management"
echo "=========================================="
echo ""

# Detect if running on WSL
if grep -qi microsoft /proc/version; then
    echo "✓ Detected: WSL (Windows Subsystem for Linux)"
    IS_WSL=true
else
    echo "✓ Detected: Native Linux"
    IS_WSL=false
fi
echo ""

# Check if PostgreSQL is installed
if command -v psql &> /dev/null; then
    echo "✓ PostgreSQL is already installed"
    psql --version
else
    echo "PostgreSQL not found. Installing..."
    sudo apt update
    sudo apt install -y postgresql postgresql-contrib
    echo "✓ PostgreSQL installed successfully"
fi
echo ""

# Start PostgreSQL
echo "Starting PostgreSQL service..."
if $IS_WSL; then
    sudo service postgresql start
    sudo service postgresql status
else
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    sudo systemctl status postgresql --no-pager
fi
echo ""

# Prompt for password
echo "=========================================="
echo "Database Configuration"
echo "=========================================="
read -sp "Enter password for PostgreSQL user 'postgres': " PG_PASSWORD
echo ""
read -sp "Confirm password: " PG_PASSWORD_CONFIRM
echo ""

if [ "$PG_PASSWORD" != "$PG_PASSWORD_CONFIRM" ]; then
    echo "✗ Passwords don't match!"
    exit 1
fi
echo ""

# Set PostgreSQL password
echo "Setting PostgreSQL password..."
sudo -u postgres psql -c "ALTER USER postgres PASSWORD '$PG_PASSWORD';"
echo "✓ Password set"
echo ""

# Create database
echo "Creating database 'apartment_mgmt'..."
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw apartment_mgmt; then
    echo "⚠ Database 'apartment_mgmt' already exists"
    read -p "Drop and recreate? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo -u postgres psql -c "DROP DATABASE apartment_mgmt;"
        sudo -u postgres psql -c "CREATE DATABASE apartment_mgmt;"
        echo "✓ Database recreated"
    else
        echo "Using existing database"
    fi
else
    sudo -u postgres psql -c "CREATE DATABASE apartment_mgmt;"
    echo "✓ Database created"
fi
echo ""

# Test connection
echo "Testing database connection..."
if PGPASSWORD=$PG_PASSWORD psql -h localhost -U postgres -d apartment_mgmt -c "SELECT 1;" &> /dev/null; then
    echo "✓ Connection successful!"
else
    echo "✗ Connection failed. Checking pg_hba.conf..."
    
    # Find pg_hba.conf
    PG_HBA=$(sudo find /etc/postgresql -name pg_hba.conf 2>/dev/null | head -1)
    
    if [ -n "$PG_HBA" ]; then
        echo "Found pg_hba.conf at: $PG_HBA"
        echo "Updating authentication method..."
        
        # Backup original
        sudo cp "$PG_HBA" "${PG_HBA}.backup"
        
        # Update authentication to md5
        sudo sed -i 's/local\s*all\s*postgres\s*peer/local   all   postgres   md5/' "$PG_HBA"
        sudo sed -i 's/local\s*all\s*all\s*peer/local   all   all   md5/' "$PG_HBA"
        
        # Restart PostgreSQL
        if $IS_WSL; then
            sudo service postgresql restart
        else
            sudo systemctl restart postgresql
        fi
        
        echo "✓ Configuration updated and PostgreSQL restarted"
        
        # Test again
        if PGPASSWORD=$PG_PASSWORD psql -h localhost -U postgres -d apartment_mgmt -c "SELECT 1;" &> /dev/null; then
            echo "✓ Connection successful after configuration update!"
        else
            echo "✗ Still cannot connect. Please check manually."
            exit 1
        fi
    fi
fi
echo ""

# Create .env file
echo "Creating .env file..."
if [ -f .env ]; then
    echo "⚠ .env file already exists"
    read -p "Overwrite? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing .env file"
        echo ""
        echo "=========================================="
        echo "Setup Complete!"
        echo "=========================================="
        echo ""
        echo "Next steps:"
        echo "1. Review your .env file"
        echo "2. Run: python database/init_db.py"
        echo "3. Run: python examples/example_usage.py"
        exit 0
    fi
fi

cat > .env << EOF
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=apartment_mgmt
DB_USER=postgres
DB_PASSWORD=$PG_PASSWORD

# Connection Pool Settings
DB_POOL_MIN=1
DB_POOL_MAX=10

# Application Settings
LOG_LEVEL=INFO
APP_TIMEZONE=UTC
ENVIRONMENT=development
DEBUG=true
EOF

echo "✓ .env file created"
echo ""

# Summary
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Database Details:"
echo "  Host:     localhost"
echo "  Port:     5432"
echo "  Database: apartment_mgmt"
echo "  User:     postgres"
echo ""
echo "Next steps:"
echo "1. Run: python database/init_db.py"
echo "2. Run: python examples/example_usage.py"
echo ""
echo "To manually connect to the database:"
echo "  psql -h localhost -U postgres -d apartment_mgmt"
echo ""

if $IS_WSL; then
    echo "Note: On WSL, start PostgreSQL with:"
    echo "  sudo service postgresql start"
fi

echo ""
echo "=========================================="
