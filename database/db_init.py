"""
Database Initialization Module
Handles PostgreSQL database setup and initialization for the apartment management system.
"""

import psycopg2
from psycopg2 import sql, extensions
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from pathlib import Path
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """
    Handles database creation, initialization, and schema setup.
    """
    
    def __init__(self, 
                 host: str = 'localhost',
                 port: int = 5432,
                 database: str = 'apartment_mgmt',
                 user: str = 'postgres',
                 password: str = 'postgres'):
        """
        Initialize database configuration.
        
        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.conn: Optional[extensions.connection] = None
        
    def _get_connection(self, database: str = 'postgres') -> extensions.connection:
        """
        Create a connection to PostgreSQL.
        
        Args:
            database: Database to connect to (default 'postgres' for admin operations)
            
        Returns:
            psycopg2 connection object
        """
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=database,
                user=self.user,
                password=self.password
            )
            logger.info(f"Connected to database: {database}")
            return conn
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database {database}: {e}")
            raise
    
    def database_exists(self) -> bool:
        """
        Check if the target database exists.
        
        Returns:
            True if database exists, False otherwise
        """
        conn = self._get_connection('postgres')
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (self.database,)
                )
                exists = cur.fetchone() is not None
                logger.info(f"Database '{self.database}' exists: {exists}")
                return exists
        finally:
            conn.close()
    
    def create_database(self, drop_if_exists: bool = False) -> None:
        """
        Create the database if it doesn't exist.
        
        Args:
            drop_if_exists: If True, drop existing database before creating
        """
        conn = self._get_connection('postgres')
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        try:
            with conn.cursor() as cur:
                if drop_if_exists and self.database_exists():
                    logger.warning(f"Dropping existing database: {self.database}")
                    # Terminate existing connections
                    cur.execute(sql.SQL("""
                        SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.datname = %s
                        AND pid <> pg_backend_pid()
                    """), (self.database,))
                    
                    cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(
                        sql.Identifier(self.database)
                    ))
                    logger.info(f"Database '{self.database}' dropped")
                
                if not self.database_exists():
                    cur.execute(sql.SQL("CREATE DATABASE {}").format(
                        sql.Identifier(self.database)
                    ))
                    logger.info(f"Database '{self.database}' created successfully")
                else:
                    logger.info(f"Database '{self.database}' already exists")
        finally:
            conn.close()
    
    def execute_schema(self, schema_file: Path) -> None:
        """
        Execute SQL schema file to create tables and constraints.
        
        Args:
            schema_file: Path to the SQL schema file
        """
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")
        
        conn = self._get_connection(self.database)
        
        try:
            with schema_file.open('r') as f:
                schema_sql = f.read()
            
            with conn.cursor() as cur:
                logger.info("Executing schema creation...")
                cur.execute(schema_sql)
                conn.commit()
                logger.info("Schema created successfully")
                
        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"Error executing schema: {e}")
            raise
        finally:
            conn.close()
    
    def verify_schema(self) -> dict:
        """
        Verify that all expected tables were created.
        
        Returns:
            Dictionary with table names and their row counts
        """
        expected_tables = [
            'users', 'buildings', 'units', 'tenants', 'service_types',
            'providers', 'provider_staff', 'bookings', 'assignments',
            'invoices', 'payments', 'reviews', 'notifications', 'audit_logs'
        ]
        
        conn = self._get_connection(self.database)
        table_info = {}
        
        try:
            with conn.cursor() as cur:
                for table in expected_tables:
                    # Check if table exists
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = %s
                        )
                    """, (table,))
                    exists = cur.fetchone()[0]
                    
                    if exists:
                        # Get row count
                        cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
                            sql.Identifier(table)
                        ))
                        count = cur.fetchone()[0]
                        table_info[table] = {'exists': True, 'rows': count}
                        logger.info(f"Table '{table}': {count} rows")
                    else:
                        table_info[table] = {'exists': False, 'rows': 0}
                        logger.warning(f"Table '{table}' does not exist!")
                        
        finally:
            conn.close()
        
        return table_info
    
    def initialize(self, schema_file: Path, drop_if_exists: bool = False) -> None:
        """
        Complete database initialization process.
        
        Args:
            schema_file: Path to the SQL schema file
            drop_if_exists: If True, drop and recreate database
        """
        logger.info("Starting database initialization...")
        
        # Step 1: Create database
        self.create_database(drop_if_exists=drop_if_exists)
        
        # Step 2: Execute schema
        self.execute_schema(schema_file)
        
        # Step 3: Verify schema
        table_info = self.verify_schema()
        
        # Check if all tables exist
        missing_tables = [t for t, info in table_info.items() if not info['exists']]
        if missing_tables:
            logger.error(f"Missing tables: {', '.join(missing_tables)}")
            raise RuntimeError(f"Schema initialization incomplete. Missing tables: {missing_tables}")
        
        logger.info("Database initialization completed successfully!")
    
    def get_connection(self) -> extensions.connection:
        """
        Get a connection to the initialized database.
        Use this for the communication layer.
        
        Returns:
            Active database connection
        """
        if not self.database_exists():
            raise RuntimeError(f"Database '{self.database}' does not exist. Run initialize() first.")
        
        return self._get_connection(self.database)


def main():
    """
    Main function to initialize the database.
    """
    # Configuration - adjust these as needed
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'apartment_mgmt'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres')
    }
    
    # Path to schema file
    schema_file = Path('/mnt/user-data/uploads/Database_Scheme.sql')
    
    # Initialize database
    db_init = DatabaseInitializer(**config)
    
    # Initialize with drop_if_exists=True to recreate fresh database
    # Set to False to preserve existing data
    db_init.initialize(schema_file, drop_if_exists=True)
    
    print("\n" + "="*50)
    print("Database initialized successfully!")
    print(f"Database: {config['database']}")
    print(f"Host: {config['host']}:{config['port']}")
    print("="*50)


if __name__ == '__main__':
    main()
