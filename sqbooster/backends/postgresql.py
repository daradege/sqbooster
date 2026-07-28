"""
PostgreSQL database backend for sqbooster.

Supports real typed tables, JSON/pickle serialization, and the
full query builder API.
"""

import json
import pickle
from typing import Any, Dict, List, Optional

from ..exceptions import DatabaseError, DatabaseConnectionError as SQBConnectionError
from ..schema import Column, TableSchema
from ..query import Query
from ..types import Blob, Pickle
from . import DatabaseBackend

try:
    import psycopg2
    from psycopg2.extras import Json as PsycopgJson, RealDictCursor

    _HAS_PSYCOPG2 = True
except ImportError:
    _HAS_PSYCOPG2 = False


class PostgreSQLBackend(DatabaseBackend):
    """PostgreSQL database backend with real tables and optional pickle support.

    Args:
        host: Database host.
        port: Database port.
        name: Database name.
        user: Database user.
        password: Database password.
        auto_commit: Whether to auto-commit after each write operation.
        serialization: Serialization mode for key-value storage: 'json' or 'pickle'.

    Example:
        db = PostgreSQLBackend(host="localhost", name="mydb", user="postgres")
        db.create_table("users", [
            Column("id", Integer(), primary_key=True),
            Column("name", Text(), nullable=False),
            Column("age", Integer()),
        ])
        db.insert("users", {"name": "Ali", "age": 30})
    """

    placeholder = "%s"

    def __init__(self, host="localhost", port=5432, name="postgres",
                 user="postgres", password="", auto_commit=True,
                 serialization="json"):
        if not _HAS_PSYCOPG2:
            raise ImportError(
                "psycopg2 is required for PostgreSQL. "
                "Install with: pip install psycopg2-binary"
            )
        if serialization not in ("json", "pickle"):
            raise ValueError("serialization must be 'json' or 'pickle'")

        self.name = name
        self.auto_commit = auto_commit
        self.serialization = serialization
        self._tables = {}

        try:
            self.conn = psycopg2.connect(
                host=host, port=port, database=name, user=user, password=password
            )
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            self._ensure_kv_store()
            self._discover_tables()
        except psycopg2.Error as e:
            raise SQBConnectionError(f"Failed to connect to PostgreSQL: {e}")

    def _ensure_kv_store(self):
        """Create the internal key-value store table if it doesn't exist."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS _kv_store (
                key VARCHAR PRIMARY KEY,
                value BYTEA,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def _discover_tables(self):
        """Discover existing user tables."""
        self.cursor.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name != '_kv_store'"
        )
        for row in self.cursor.fetchall():
            table_name = row["table_name"]
            self._tables[table_name] = self._reflect_schema(table_name)

    def _reflect_schema(self, table_name):
        """Reflect a table's schema from PostgreSQL information_schema.

        Args:
            table_name: Name of the table.

        Returns:
            TableSchema instance.
        """
        self.cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default,
                   character_maximum_length
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table_name,))

        from ..types import Integer, Text, Float

        columns = []
        for row in self.cursor.fetchall():
            col_name = row["column_name"]
            col_type_str = row["data_type"].upper()
            nullable = row["is_nullable"] == "YES"
            default = row["column_default"]
            max_length = row["character_maximum_length"]

            is_pk = False
            if default and "nextval" in str(default).lower():
                is_pk = True

            if "INT" in col_type_str:
                col_type = Integer()
            elif "REAL" in col_type_str or "FLOAT" in col_type_str or "DOUBLE" in col_type_str or "NUMERIC" in col_type_str:
                col_type = Float()
            elif "BYTEA" in col_type_str:
                col_type = Blob()
            elif "JSON" in col_type_str:
                from ..types import JSON as JSONType
                col_type = JSONType()
            elif "TEXT" in col_type_str or "VARCHAR" in col_type_str or "CHAR" in col_type_str:
                col_type = Text(max_length=max_length)
            else:
                col_type = Text()

            columns.append(Column(
                col_name, col_type,
                primary_key=is_pk,
                nullable=nullable if not is_pk else False,
            ))

        return TableSchema(table_name, columns)

    def _serialize(self, value):
        """Serialize a value for storage in the _kv_store table."""
        if self.serialization == "pickle":
            return pickle.dumps(value)
        return json.dumps(value, ensure_ascii=False).encode("utf-8")

    def _deserialize(self, raw):
        """Deserialize a value from the _kv_store table."""
        if raw is None:
            return None
        if isinstance(raw, memoryview):
            raw = bytes(raw)
        if self.serialization == "pickle":
            try:
                return pickle.loads(raw)
            except Exception:
                return raw
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            try:
                return json.loads(raw)
            except Exception:
                return raw


    def create_table(self, name, columns):
        """Create a new table with typed columns.

        Args:
            name: Table name.
            columns: List of Column instances or a TableSchema.

        Returns:
            True on success.
        """
        if isinstance(columns, TableSchema):
            schema = columns
        else:
            schema = TableSchema(name, columns)

        sql = schema.to_sql_create(backend="postgresql")
        try:
            self.cursor.execute(sql)
            if self.auto_commit:
                self.conn.commit()
            self._tables[name] = schema
            return True
        except psycopg2.Error as e:
            raise DatabaseError(f"Failed to create table '{name}': {e}")

    def drop_table(self, name, if_exists=True):
        """Drop a table.

        Args:
            name: Table name.
            if_exists: Suppress error if table doesn't exist.

        Returns:
            True on success.
        """
        clause = "IF EXISTS " if if_exists else ""
        try:
            self.cursor.execute(f"DROP TABLE {clause}{name}")
            if self.auto_commit:
                self.conn.commit()
            self._tables.pop(name, None)
            return True
        except psycopg2.Error as e:
            raise DatabaseError(f"Failed to drop table '{name}': {e}")

    def table_exists(self, name):
        """Check if a table exists."""
        self.cursor.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name=%s)",
            (name,),
        )
        result = self.cursor.fetchone()
        return result["exists"] if isinstance(result, dict) else list(result.values())[0]

    def get_tables(self):
        """List all user-defined table names."""
        self.cursor.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name != '_kv_store'"
        )
        return [row["table_name"] for row in self.cursor.fetchall()]

    def get_schema(self, table_name):
        """Get the schema for a table."""
        if table_name in self._tables:
            return self._tables[table_name]
        if not self.table_exists(table_name):
            raise DatabaseError(f"Table '{table_name}' does not exist")
        schema = self._reflect_schema(table_name)
        self._tables[table_name] = schema
        return schema

    

    def insert(self, table, data):
        """Insert a single row.

        Args:
            table: Table name.
            data: Dict of column_name -> value.

        Returns:
            True on success.
        """
        schema = self._get_schema_or_raise(table)
        cols, vals = schema.prepare_insert(data)
        placeholders = ", ".join([self.placeholder] * len(cols))
        col_names = ", ".join(cols)
        sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"

        try:
            self.cursor.execute(sql, vals)
            if self.auto_commit:
                self.conn.commit()
            return True
        except psycopg2.IntegrityError as e:
            raise DatabaseError(f"Integrity error inserting into '{table}': {e}")
        except psycopg2.Error as e:
            raise DatabaseError(f"Failed to insert into '{table}': {e}")

    def insert_many(self, table, data_list):
        """Insert multiple rows at once.

        Args:
            table: Table name.
            data_list: List of dicts.

        Returns:
            True on success.
        """
        if not data_list:
            return True

        schema = self._get_schema_or_raise(table)
        cols, _ = schema.prepare_insert(data_list[0])
        placeholders = ", ".join([self.placeholder] * len(cols))
        col_names = ", ".join(cols)
        sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"

        try:
            all_vals = []
            for data in data_list:
                _, vals = schema.prepare_insert(dict(data))
                all_vals.append(vals)
            self.cursor.executemany(sql, all_vals)
            if self.auto_commit:
                self.conn.commit()
            return True
        except psycopg2.IntegrityError as e:
            raise DatabaseError(f"Integrity error in bulk insert into '{table}': {e}")
        except psycopg2.Error as e:
            raise DatabaseError(f"Failed to bulk insert into '{table}': {e}")

    def update(self, table, data, **filters):
        """Update rows matching filters.

        Args:
            table: Table name.
            data: Dict of column_name -> new_value.
            **filters: Filter conditions.

        Returns:
            Number of rows updated.
        """
        schema = self._get_schema_or_raise(table)
        set_parts = []
        set_params = []
        for col_name, value in data.items():
            col = schema.get_column(col_name)
            set_parts.append(f"{col_name} = {self.placeholder}")
            set_params.append(col.to_sql(value))

        where_clause, where_params = Query(self, table)._build_where_from_filters(filters)
        sql = f"UPDATE {table} SET {', '.join(set_parts)}{where_clause}"
        params = set_params + where_params

        try:
            self.cursor.execute(sql, params)
            if self.auto_commit:
                self.conn.commit()
            return self.cursor.rowcount
        except psycopg2.Error as e:
            raise DatabaseError(f"Failed to update '{table}': {e}")

    def delete(self, table, **filters):
        """Delete rows matching filters.

        Args:
            table: Table name.
            **filters: Filter conditions.

        Returns:
            Number of rows deleted.
        """
        where_clause, params = Query(self, table)._build_where_from_filters(filters)
        sql = f"DELETE FROM {table}{where_clause}"

        try:
            self.cursor.execute(sql, params)
            if self.auto_commit:
                self.conn.commit()
            return self.cursor.rowcount
        except psycopg2.Error as e:
            raise DatabaseError(f"Failed to delete from '{table}': {e}")

    def query(self, table):
        """Create a Query builder for the given table.

        Args:
            table: Table name.

        Returns:
            Query instance.
        """
        return Query(self, table)

    def execute(self, sql, params=None, fetch=False):
        """Execute raw SQL.

        Args:
            sql: SQL string.
            params: Query parameters.
            fetch: If True, return results as list of dicts.

        Returns:
            List of dicts if fetch=True, else None.
        """
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)

            if fetch:
                rows = self.cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                if self.auto_commit:
                    self.conn.commit()
                return None
        except psycopg2.Error as e:
            raise DatabaseError(f"Failed to execute SQL: {e}")

    def count(self, table, **filters):
        """Count rows matching filters."""
        q = Query(self, table).filter(**filters) if filters else Query(self, table)
        return q.count()

    

    def write(self, key, value, commit=None):
        """Write a key-value pair using JSON or pickle serialization."""
        try:
            serialized = self._serialize(value)
            self.cursor.execute(
                "INSERT INTO _kv_store (key, value) VALUES (%s, %s) "
                "ON CONFLICT (key) DO UPDATE SET value = %s",
                (key, serialized, serialized),
            )
            if commit or (commit is None and self.auto_commit):
                self.conn.commit()
            return True
        except psycopg2.Error as e:
            raise DatabaseError(f"Failed to write key '{key}': {e}")

    def read(self, key, default=None):
        """Read a value by key."""
        try:
            self.cursor.execute("SELECT value FROM _kv_store WHERE key=%s", (key,))
            result = self.cursor.fetchone()
            if result:
                return self._deserialize(result["value"] if isinstance(result, dict) else result[0])
            return default
        except psycopg2.Error as e:
            raise DatabaseError(f"Failed to read key '{key}': {e}")

    def delete_key(self, key, commit=None):
        """Delete a key-value pair."""
        try:
            self.cursor.execute("DELETE FROM _kv_store WHERE key=%s", (key,))
            if commit or (commit is None and self.auto_commit):
                self.conn.commit()
            return True
        except psycopg2.Error as e:
            raise DatabaseError(f"Failed to delete key '{key}': {e}")

    def keys(self, pattern=None):
        """Get all keys, optionally filtered by pattern."""
        try:
            if pattern:
                self.cursor.execute(
                    "SELECT key FROM _kv_store WHERE key LIKE %s", (f"%{pattern}%",)
                )
            else:
                self.cursor.execute("SELECT key FROM _kv_store")
            rows = self.cursor.fetchall()
            return [row["key"] if isinstance(row, dict) else row[0] for row in rows]
        except psycopg2.Error as e:
            raise DatabaseError(f"Failed to fetch keys: {e}")

    def exists(self, key):
        """Check if a key exists."""
        try:
            self.cursor.execute("SELECT 1 FROM _kv_store WHERE key=%s", (key,))
            result = self.cursor.fetchone()
            return result is not None
        except psycopg2.Error as e:
            raise DatabaseError(f"Failed to check key existence: {e}")

    def get_size(self):
        """Get number of key-value pairs."""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM _kv_store")
            result = self.cursor.fetchone()
            return result["count"] if isinstance(result, dict) else list(result.values())[0]
        except psycopg2.Error as e:
            raise DatabaseError(f"Failed to get size: {e}")

    def delete_database(self, commit=None):
        """Clear all data from all tables including key-value store."""
        try:
            self.cursor.execute("DELETE FROM _kv_store")
            for table_name in self.get_tables():
                self.cursor.execute(f"DELETE FROM {table_name}")
            if commit or (commit is None and self.auto_commit):
                self.conn.commit()
            return True
        except psycopg2.Error as e:
            raise DatabaseError(f"Failed to delete database: {e}")

    

    def close(self):
        """Close the database connection."""
        try:
            self.conn.close()
        except psycopg2.Error as e:
            raise SQBConnectionError(f"Failed to close connection: {e}")

    def commit(self):
        """Manually commit pending changes."""
        self.conn.commit()

    def rollback(self):
        """Roll back pending changes."""
        self.conn.rollback()

    

    def _get_schema_or_raise(self, table_name):
        """Get a cached schema or raise if table doesn't exist."""
        if table_name in self._tables:
            return self._tables[table_name]
        if not self.table_exists(table_name):
            raise DatabaseError(f"Table '{table_name}' does not exist")
        schema = self._reflect_schema(table_name)
        self._tables[table_name] = schema
        return schema

    def __repr__(self):
        return (
            f"PostgreSQLBackend(name={self.name!r}, "
            f"serialization={self.serialization!r})"
        )


if not _HAS_PSYCOPG2:
    class PostgreSQLBackend:
        """Fallback when psycopg2 is not installed."""
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "psycopg2 is required for PostgreSQL. "
                "Install with: pip install psycopg2-binary"
            )
