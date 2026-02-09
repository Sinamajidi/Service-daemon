"""
Configuration file for database settings.
Can be customized based on environment (development, production, etc.)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database Configuration (matches db_init.py format)
DB_CONFIG = {
    'DB_HOST': os.getenv('DB_HOST', 'localhost'),
    'DB_PORT': os.getenv('DB_PORT', '5432'),
    'DB_NAME': os.getenv('DB_NAME', 'apartment_mgmt'),
    'DB_USER': os.getenv('DB_USER', 'postgres'),
    'DB_PASSWORD': os.getenv('DB_PASSWORD', 'postgres')
}

# Legacy format for db_connection.py (lowercase keys without prefix)
DB_CONNECTION_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'apartment_mgmt'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# Connection Pool Settings
POOL_CONFIG = {
    'min_connections': int(os.getenv('DB_POOL_MIN', 1)),
    'max_connections': int(os.getenv('DB_POOL_MAX', 10))
}

# File Paths
BASE_DIR = Path(__file__).parent

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Application Settings
APP_TIMEZONE = 'UTC'
DEFAULT_PAGE_SIZE = 50  # For paginated queries
MAX_PAGE_SIZE = 1000

# Role definitions
USER_ROLES = ['tenant', 'manager', 'provider_staff', 'admin']

# Booking status values
BOOKING_STATUSES = ['requested', 'scheduled', 'assigned', 'in_progress', 'completed', 'cancelled']

# Priority levels
PRIORITY_LEVELS = ['low', 'normal', 'high', 'emergency']

# Connection Pool Settings
POOL_CONFIG = {
    'min_connections': int(os.getenv('DB_POOL_MIN', 1)),
    'max_connections': int(os.getenv('DB_POOL_MAX', 10))
}

# File Paths
BASE_DIR = Path(__file__).parent
SCHEMA_FILE = BASE_DIR / 'database' / 'schema.sql'

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Application Settings
APP_TIMEZONE = 'UTC'
DEFAULT_PAGE_SIZE = 50  # For paginated queries
MAX_PAGE_SIZE = 1000

# Role definitions
USER_ROLES = ['tenant', 'manager', 'provider_staff', 'admin']

# Booking status values
BOOKING_STATUSES = ['requested', 'scheduled', 'assigned', 'in_progress', 'completed', 'cancelled']

# Priority levels
PRIORITY_LEVELS = ['low', 'normal', 'high', 'emergency']
