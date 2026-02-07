"""
Data Access Layer (Communication Layer)
Provides minimal class-based access to database entities with lazy instantiation.
All heavy processing is delegated to the database.
"""

from typing import List, Dict, Any, Optional, Union
from uuid import UUID
from datetime import datetime, date
from .db_connection import get_db
import logging

logger = logging.getLogger(__name__)


class DataAccessLayer:
    """
    Base data access layer providing common database operations.
    This class should not be instantiated directly - use specific entity methods.
    """
    
    def __init__(self):
        self.db = get_db()
    
    # ==================== SIMPLE DATA QUERIES ====================
    # These methods return simple data (IDs, counts, lists) without instantiating objects
    
    def get_all_ids(self, table: str) -> List[str]:
        """
        Get all IDs from a table.
        
        Args:
            table: Table name
        
        Returns:
            List of UUID strings
        """
        query = f"SELECT id FROM {table} ORDER BY created_at DESC"
        results = self.db.execute_query(query, fetch='all')
        return [str(row['id']) for row in results] if results else []
    
    def get_filtered_ids(self, 
                        table: str, 
                        where_clause: str, 
                        params: tuple) -> List[str]:
        """
        Get filtered IDs from a table based on conditions.
        
        Args:
            table: Table name
            where_clause: SQL WHERE clause (without WHERE keyword)
            params: Query parameters
        
        Returns:
            List of UUID strings
        """
        query = f"SELECT id FROM {table} WHERE {where_clause} ORDER BY created_at DESC"
        results = self.db.execute_query(query, params, fetch='all')
        return [str(row['id']) for row in results] if results else []
    
    def count_records(self, table: str, where_clause: str = None, params: tuple = None) -> int:
        """
        Count records in a table.
        
        Args:
            table: Table name
            where_clause: Optional WHERE clause
            params: Query parameters
        
        Returns:
            Record count
        """
        query = f"SELECT COUNT(*) as count FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        result = self.db.execute_query(query, params, fetch='one')
        return result['count'] if result else 0
    
    def record_exists(self, table: str, id_value: Union[str, UUID]) -> bool:
        """
        Check if a record exists by ID.
        
        Args:
            table: Table name
            id_value: UUID or UUID string
        
        Returns:
            True if record exists
        """
        query = f"SELECT EXISTS(SELECT 1 FROM {table} WHERE id = %s) as exists"
        result = self.db.execute_query(query, (str(id_value),), fetch='one')
        return result['exists'] if result else False
    
    # ==================== COMPLETE DATA QUERIES ====================
    # These methods return complete record data as dictionaries (not instantiated objects)
    
    def get_record_by_id(self, table: str, id_value: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """
        Get complete record data by ID.
        Returns a dictionary, not an instantiated object.
        
        Args:
            table: Table name
            id_value: UUID or UUID string
        
        Returns:
            Dictionary with all record fields or None if not found
        """
        query = f"SELECT * FROM {table} WHERE id = %s"
        return self.db.execute_query(query, (str(id_value),), fetch='one')
    
    def get_records_by_ids(self, table: str, id_list: List[Union[str, UUID]]) -> List[Dict[str, Any]]:
        """
        Get multiple complete records by IDs.
        
        Args:
            table: Table name
            id_list: List of UUIDs or UUID strings
        
        Returns:
            List of dictionaries with record data
        """
        if not id_list:
            return []
        
        # Convert all to strings
        id_strings = [str(id_val) for id_val in id_list]
        
        query = f"SELECT * FROM {table} WHERE id = ANY(%s)"
        results = self.db.execute_query(query, (id_strings,), fetch='all')
        return results if results else []
    
    def get_filtered_records(self, 
                            table: str, 
                            where_clause: str, 
                            params: tuple,
                            limit: int = None,
                            offset: int = None,
                            order_by: str = "created_at DESC") -> List[Dict[str, Any]]:
        """
        Get filtered records based on conditions.
        
        Args:
            table: Table name
            where_clause: SQL WHERE clause
            params: Query parameters
            limit: Maximum number of records
            offset: Number of records to skip
            order_by: ORDER BY clause
        
        Returns:
            List of dictionaries with record data
        """
        query = f"SELECT * FROM {table} WHERE {where_clause}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        if offset:
            query += f" OFFSET {offset}"
        
        results = self.db.execute_query(query, params, fetch='all')
        return results if results else []
    
    # ==================== MODIFICATION OPERATIONS ====================
    
    def insert_record(self, table: str, data: Dict[str, Any]) -> str:
        """
        Insert a new record.
        
        Args:
            table: Table name
            data: Dictionary of column: value pairs
        
        Returns:
            UUID of inserted record as string
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = tuple(data.values())
        
        query = f"""
            INSERT INTO {table} ({columns})
            VALUES ({placeholders})
            RETURNING id
        """
        
        result = self.db.execute_query(query, values, fetch='one', dict_cursor=True)
        return str(result['id']) if result else None
    
    def update_record(self, table: str, id_value: Union[str, UUID], data: Dict[str, Any]) -> bool:
        """
        Update a record by ID.
        
        Args:
            table: Table name
            id_value: UUID or UUID string
            data: Dictionary of column: value pairs to update
        
        Returns:
            True if record was updated
        """
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        values = tuple(data.values()) + (str(id_value),)
        
        query = f"UPDATE {table} SET {set_clause} WHERE id = %s"
        
        rows_affected = self.db.execute_update(query, values)
        return rows_affected > 0
    
    def delete_record(self, table: str, id_value: Union[str, UUID]) -> bool:
        """
        Delete a record by ID.
        
        Args:
            table: Table name
            id_value: UUID or UUID string
        
        Returns:
            True if record was deleted
        """
        query = f"DELETE FROM {table} WHERE id = %s"
        rows_affected = self.db.execute_update(query, (str(id_value),))
        return rows_affected > 0
    
    # ==================== COMPLEX QUERIES ====================
    # Database-heavy operations that leverage PostgreSQL capabilities
    
    def execute_aggregation(self, 
                           table: str,
                           agg_function: str,
                           column: str,
                           where_clause: str = None,
                           params: tuple = None,
                           group_by: str = None) -> Any:
        """
        Execute aggregation queries (SUM, AVG, MAX, MIN, etc.).
        
        Args:
            table: Table name
            agg_function: Aggregation function (e.g., 'SUM', 'AVG', 'COUNT')
            column: Column to aggregate
            where_clause: Optional WHERE clause
            params: Query parameters
            group_by: Optional GROUP BY clause
        
        Returns:
            Aggregation result
        """
        query = f"SELECT {agg_function}({column}) as result FROM {table}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        if group_by:
            query += f" GROUP BY {group_by}"
        
        result = self.db.execute_query(query, params, fetch='one')
        return result['result'] if result else None
    
    def execute_join_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Execute complex JOIN queries.
        This delegates all processing to PostgreSQL.
        
        Args:
            query: Complete SQL query
            params: Query parameters
        
        Returns:
            List of result dictionaries
        """
        results = self.db.execute_query(query, params, fetch='all')
        return results if results else []
    
    def execute_custom_query(self, 
                            query: str, 
                            params: tuple = None,
                            fetch: str = 'all') -> Any:
        """
        Execute any custom SQL query.
        Use this for complex database operations.
        
        Args:
            query: SQL query
            params: Query parameters
            fetch: 'all', 'one', or 'none'
        
        Returns:
            Query results
        """
        return self.db.execute_query(query, params, fetch=fetch)


# Global instance (lazy initialization)
_dal_instance: Optional[DataAccessLayer] = None


def get_dal() -> DataAccessLayer:
    """
    Get the global DataAccessLayer instance.
    Uses lazy initialization - creates instance only when first needed.
    
    Returns:
        DataAccessLayer instance
    """
    global _dal_instance
    if _dal_instance is None:
        _dal_instance = DataAccessLayer()
    return _dal_instance
