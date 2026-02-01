"""
Database Connection Manager
Provides connection pooling and management for the communication layer.
"""

import psycopg2
from psycopg2 import pool, extensions
from psycopg2.extras import RealDictCursor
from typing import Optional, Any, Dict, List, Tuple
from contextlib import contextmanager
import logging
import os

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Manages database connections with pooling for efficient resource usage.
    Singleton pattern to ensure single connection pool instance.
    """
    
    _instance: Optional['DatabaseConnection'] = None
    _pool: Optional[pool.SimpleConnectionPool] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the connection pool if not already initialized."""
        if self._pool is None:
            self._initialize_pool()
    
    def _initialize_pool(self, 
                        host: str = None,
                        port: int = None,
                        database: str = None,
                        user: str = None,
                        password: str = None,
                        min_conn: int = 1,
                        max_conn: int = 10) -> None:
        """
        Initialize the connection pool.
        
        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            min_conn: Minimum connections in pool
            max_conn: Maximum connections in pool
        """
        # Use environment variables or defaults
        self.host = host or os.getenv('DB_HOST', 'localhost')
        self.port = port or int(os.getenv('DB_PORT', 5432))
        self.database = database or os.getenv('DB_NAME', 'apartment_mgmt')
        self.user = user or os.getenv('DB_USER', 'postgres')
        self.password = password or os.getenv('DB_PASSWORD', 'postgres')
        
        try:
            self._pool = pool.SimpleConnectionPool(
                min_conn,
                max_conn,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info(f"Connection pool created: {self.database}@{self.host}:{self.port}")
        except psycopg2.Error as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for getting a connection from the pool.
        Automatically returns connection to pool when done.
        
        Usage:
            with db.get_connection() as conn:
                # use connection
                pass
        
        Yields:
            Database connection
        """
        if self._pool is None:
            raise RuntimeError("Connection pool not initialized")
        
        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                self._pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = True):
        """
        Context manager for getting a cursor.
        Automatically handles connection management and commits/rollbacks.
        
        Args:
            dict_cursor: If True, use RealDictCursor to return rows as dictionaries
        
        Usage:
            with db.get_cursor() as cur:
                cur.execute("SELECT * FROM users")
                results = cur.fetchall()
        
        Yields:
            Database cursor
        """
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cur = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cur
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction rolled back due to error: {e}")
                raise
            finally:
                cur.close()
    
    def execute_query(self, 
                     query: str, 
                     params: Tuple = None,
                     fetch: str = 'all',
                     dict_cursor: bool = True) -> Optional[Any]:
        """
        Execute a SELECT query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters (tuple)
            fetch: 'all', 'one', or 'none'
            dict_cursor: Return results as dictionaries
        
        Returns:
            Query results based on fetch parameter
        """
        with self.get_cursor(dict_cursor=dict_cursor) as cur:
            cur.execute(query, params)
            
            if fetch == 'all':
                return cur.fetchall()
            elif fetch == 'one':
                return cur.fetchone()
            elif fetch == 'none':
                return None
            else:
                raise ValueError(f"Invalid fetch parameter: {fetch}")
    
    def execute_update(self, 
                      query: str, 
                      params: Tuple = None) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query.
        
        Args:
            query: SQL query string
            params: Query parameters (tuple)
        
        Returns:
            Number of affected rows
        """
        with self.get_cursor(dict_cursor=False) as cur:
            cur.execute(query, params)
            return cur.rowcount
    
    def execute_batch(self, 
                     query: str, 
                     params_list: List[Tuple]) -> int:
        """
        Execute the same query with multiple parameter sets efficiently.
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
        
        Returns:
            Total number of affected rows
        """
        from psycopg2.extras import execute_batch
        
        with self.get_cursor(dict_cursor=False) as cur:
            execute_batch(cur, query, params_list)
            return cur.rowcount
    
    def close_all_connections(self) -> None:
        """Close all connections in the pool."""
        if self._pool:
            self._pool.closeall()
            logger.info("All database connections closed")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.close_all_connections()


# Global database connection instance
db = DatabaseConnection()


def get_db() -> DatabaseConnection:
    """
    Get the global database connection instance.
    
    Returns:
        DatabaseConnection instance
    """
    return db
