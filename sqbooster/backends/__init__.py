"""
Abstract base class for all sqbooster database backends.

Defines the unified interface that all backends must implement,
enabling seamless switching between databases.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..schema import Column, TableSchema
from ..query import Query


class DatabaseBackend(ABC):
    """Abstract base class defining the unified database interface.

    Every backend (SQLite, PostgreSQL, etc.) must implement these methods.
    This ensures you can swap backends by changing only the constructor call.
    """

    @property
    @abstractmethod
    def placeholder(self):
        """Return the query placeholder character ('?' for SQLite, '%s' for PostgreSQL)."""
        ...

    @abstractmethod
    def __init__(self, serialization="json", **kwargs):
        """Initialize the backend.

        Args:
            serialization: Serialization format for key-value mode.
                          'json' (default) or 'pickle'.
        """
        ...

    
    @abstractmethod
    def create_table(self, name, columns):
        """Create a new table.

        Args:
            name: Table name.
            columns: List of Column instances or a TableSchema.

        Returns:
            True on success.
        """
        ...

    @abstractmethod
    def drop_table(self, name, if_exists=True):
        """Drop a table.

        Args:
            name: Table name.
            if_exists: If True, don't raise error when table doesn't exist.

        Returns:
            True on success.
        """
        ...

    @abstractmethod
    def table_exists(self, name):
        """Check if a table exists.

        Args:
            name: Table name.

        Returns:
            True if table exists.
        """
        ...

    @abstractmethod
    def get_tables(self):
        """List all table names.

        Returns:
            List of table name strings.
        """
        ...

    @abstractmethod
    def get_schema(self, table_name):
        """Get the schema for a table.

        Args:
            table_name: Table name.

        Returns:
            TableSchema instance.
        """
        ...


    @abstractmethod
    def insert(self, table, data):
        """Insert a single row.

        Args:
            table: Table name.
            data: Dict of column_name -> value.

        Returns:
            True on success.
        """
        ...

    @abstractmethod
    def insert_many(self, table, data_list):
        """Insert multiple rows at once.

        Args:
            table: Table name.
            data_list: List of dicts, each representing a row.

        Returns:
            True on success.
        """
        ...

    @abstractmethod
    def update(self, table, data, **filters):
        """Update rows matching filters.

        Args:
            table: Table name.
            data: Dict of column_name -> new_value.
            **filters: Filter conditions (same syntax as Query.filter).

        Returns:
            Number of rows updated.
        """
        ...

    @abstractmethod
    def delete(self, table, **filters):
        """Delete rows matching filters.

        Args:
            table: Table name.
            **filters: Filter conditions.

        Returns:
            Number of rows deleted.
        """
        ...

    @abstractmethod
    def query(self, table):
        """Create a Query builder for this table.

        Args:
            table: Table name.

        Returns:
            Query instance for chaining.
        """
        ...

    @abstractmethod
    def execute(self, sql, params=None, fetch=False):
        """Execute raw SQL.

        Args:
            sql: SQL string.
            params: Query parameters.
            fetch: If True, return results.

        Returns:
            Query results if fetch=True, else None.
        """
        ...

    @abstractmethod
    def count(self, table, **filters):
        """Count rows matching filters.

        Args:
            table: Table name.
            **filters: Filter conditions.

        Returns:
            Row count.
        """
        ...


    @abstractmethod
    def write(self, key, value, commit=None):
        """Write a key-value pair (backward-compatible API).

        Uses an internal _kv_store table. Serialization depends on
        the serialization mode (json or pickle).
        """
        ...

    @abstractmethod
    def read(self, key, default=None):
        """Read a value by key (backward-compatible API)."""
        ...

    @abstractmethod
    def delete_key(self, key, commit=None):
        """Delete a key-value pair (backward-compatible API)."""
        ...

    @abstractmethod
    def keys(self, pattern=None):
        """Get all keys, optionally filtered (backward-compatible API)."""
        ...

    @abstractmethod
    def exists(self, key):
        """Check if a key exists (backward-compatible API)."""
        ...

    @abstractmethod
    def get_size(self):
        """Get number of key-value pairs (backward-compatible API)."""
        ...

    @abstractmethod
    def delete_database(self, commit=None):
        """Clear all data (backward-compatible API)."""
        ...

    def clear(self):
        """Convenience alias for delete_database()."""
        return self.delete_database()


    @abstractmethod
    def close(self):
        """Close the database connection."""
        ...

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __repr__(self):
        return f"{self.__class__.__name__}()"


from .sqlite import SQLiteBackend
from .postgresql import PostgreSQLBackend
