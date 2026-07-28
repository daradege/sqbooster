"""
SimpleClient - A high-level wrapper for easy sqbooster usage.

Provides a simplified API for common database operations while still
exposing the full backend for advanced use cases.
"""

from .types import Integer, Text, Float, Boolean, Blob, JSON, Pickle
from .schema import Column

_TYPE_MAP = {
    int: Integer,
    float: Float,
    str: Text,
    bool: Boolean,
    bytes: Blob,
    dict: JSON,
    list: JSON,
}


class SimpleClient:
    """High-level wrapper around any sqbooster backend.

    Simplifies table creation, CRUD operations, and querying.

    Args:
        backend: A DatabaseBackend instance to wrap.

    Example::

        import sqbooster

        db = sqbooster.sqlite()
        db.define("users", {"name": str, "email": str, "age": int})
        db.add("users", {"name": "Alice", "email": "a@t.co", "age": 30})
        user = db.get("users", name="Alice")
        adults = db.find("users", age__gte=18)
        db.update("users", {"age": 31}, name="Alice")
        db.remove("users", name="Alice")
    """

    def __init__(self, backend):
        from .backends import DatabaseBackend
        if not isinstance(backend, DatabaseBackend):
            raise TypeError(
                f"backend must be a DatabaseBackend instance, got {type(backend).__name__}. "
                f"Use SimpleClient.sqlite(), SimpleClient.postgresql(), etc. for convenience."
            )
        self._backend = backend

    @classmethod
    def sqlite(cls, name=":memory:", auto_commit=True, serialization="json"):
        """Create a SimpleClient backed by SQLite.

        Args:
            name: Database file path or ':memory:' for in-memory.
            auto_commit: Auto-commit after each write.
            serialization: 'json' or 'pickle' for the key-value store.
        """
        from .backends.sqlite import SQLiteBackend
        return cls(SQLiteBackend(name, auto_commit=auto_commit, serialization=serialization))

    @classmethod
    def postgresql(cls, host="localhost", port=5432, name="postgres",
                   user="postgres", password="", auto_commit=True,
                   serialization="json"):
        """Create a SimpleClient backed by PostgreSQL.

        Args:
            host: Database host.
            port: Database port.
            name: Database name.
            user: Database user.
            password: Database password.
            auto_commit: Auto-commit after each write.
            serialization: 'json' or 'pickle' for the key-value store.
        """
        from .backends.postgresql import PostgreSQLBackend
        return cls(PostgreSQLBackend(
            host=host, port=port, name=name, user=user,
            password=password, auto_commit=auto_commit,
            serialization=serialization,
        ))

    @classmethod
    def json(cls, path, auto_commit=True):
        """Create a SimpleClient backed by a JSON file.

        Args:
            path: Path to the JSON file.
            auto_commit: Auto-commit after each write.
        """
        from .databases.jsonfile import JSONFileDatabase
        return cls(JSONFileDatabase(path, auto_commit=auto_commit))

    @classmethod
    def pickle(cls, path, auto_commit=True):
        """Create a SimpleClient backed by a Pickle file.

        Args:
            path: Path to the pickle file.
            auto_commit: Auto-commit after each write.
        """
        from .databases.picklefile import PickleFileDatabase
        return cls(PickleFileDatabase(path, auto_commit=auto_commit))

    @classmethod
    def redis(cls, host="localhost", port=6379, db=0, password=None,
              prefix="", serialization="json"):
        """Create a SimpleClient backed by Redis.

        Args:
            host: Redis host.
            port: Redis port.
            db: Redis database number.
            password: Redis password.
            prefix: Key prefix for namespacing.
            serialization: 'json' or 'pickle'.
        """
        from .databases.redis import RedisDatabase
        return cls(RedisDatabase(
            host=host, port=port, db=db, password=password,
            prefix=prefix, serialization=serialization,
        ))

    @classmethod
    def mongo(cls, uri="mongodb://localhost:27017", database="sqbooster"):
        """Create a SimpleClient backed by MongoDB.

        Args:
            uri: MongoDB connection URI.
            database: Database name.
        """
        from .databases.mongo import MongoDatabase
        return cls(MongoDatabase(uri=uri, database=database))

    def define(self, table_name, columns):
        """Define and create a table.

        Args:
            table_name: Name for the new table.
            columns: One of:

                - A dict of ``{name: type}`` for quick definition.
                - A list of ``(name, type)`` tuples.
                - A list of :class:`~sqbooster.schema.Column` objects for full control.

        Returns:
            True on success.

        Example::

            # Dict (simplest)
            client.define("users", {"name": str, "age": int})

            # Tuples
            client.define("users", [("name", str), ("age", int)])
        """
        if isinstance(columns, dict):
            columns = list(columns.items())

        schema_columns = []
        for item in columns:
            if isinstance(item, Column):
                schema_columns.append(item)
            elif isinstance(item, (tuple, list)) and len(item) == 2:
                name, col_type = item
                col_obj = _build_column(name, col_type)
                schema_columns.append(col_obj)
            else:
                raise ValueError(
                    f"Each column must be a Column object or (name, type) tuple, got {item!r}"
                )

        if not any(c.primary_key for c in schema_columns):
            schema_columns.insert(0, Column("id", Integer(), primary_key=True, autoincrement=True))

        self._backend.create_table(table_name, schema_columns)
        return True

    def add(self, table, data):
        """Insert one or more rows.

        If the table doesn't exist yet, it is created automatically from the
        column types in the data.

        Args:
            table: Table name.
            data: A dict (single row) or list of dicts (bulk insert).

        Returns:
            True on success.
        """
        if not self._backend.table_exists(table):
            sample = data[0] if isinstance(data, list) else data
            self.define(table, {k: type(v) for k, v in sample.items()})

        if isinstance(data, list):
            self._backend.insert_many(table, data)
        else:
            self._backend.insert(table, data)
        return True

    def get(self, table, **filters):
        """Get a single row matching filters.

        Args:
            table: Table name.
            **filters: Filter conditions.

        Returns:
            Dict for the row, or None if not found.

        Raises:
            ValueError: If more than one row matches.
        """
        results = self._backend.query(table).filter(**filters).all()
        if len(results) == 0:
            return None
        if len(results) > 1:
            raise ValueError(f"Expected 1 row, got {len(results)}")
        return results[0]

    def find(self, table, order_by=None, limit=None, offset=None, **filters):
        """Find rows matching filters.

        Args:
            table: Table name.
            order_by: Column name to sort by. Prefix with '-' for descending.
            limit: Maximum rows to return.
            offset: Number of rows to skip.
            **filters: Filter conditions (supports ``__gt``, ``__lt``, ``__contains``, etc.).

        Returns:
            List of row dicts.
        """
        q = self._backend.query(table).filter(**filters)
        if order_by:
            if isinstance(order_by, str):
                q = q.order_by(order_by)
            else:
                q = q.order_by(*order_by)
        if offset is not None:
            q = q.offset(offset)
        if limit is not None:
            q = q.limit(limit)
        return q.all()

    def update(self, table, data, **filters):
        """Update rows matching filters.

        Args:
            table: Table name.
            data: Dict of column_name -> new_value.
            **filters: Filter conditions.

        Returns:
            Number of rows updated.
        """
        return self._backend.update(table, data, **filters)

    def remove(self, table, **filters):
        """Delete rows matching filters."""
        return self._backend.delete(table, **filters)

    def delete(self, table, **filters):
        """Delete rows matching filters (alias for remove)."""
        return self._backend.delete(table, **filters)

    def count(self, table, **filters):
        """Count rows matching filters.

        Args:
            table: Table name.
            **filters: Filter conditions.

        Returns:
            Row count.
        """
        return self._backend.query(table).filter(**filters).count() if filters else self._backend.query(table).count()

    def exists(self, table, **filters):
        """Check if any rows match filters.

        Args:
            table: Table name.
            **filters: Filter conditions.

        Returns:
            True if matching rows exist.
        """
        return self._backend.query(table).filter(**filters).exists() if filters else self._backend.query(table).exists()

    def tables(self):
        """List all table names.

        Returns:
            List of table name strings.
        """
        return self._backend.get_tables()

    def drop(self, table_name):
        """Drop a table.

        Args:
            table_name: Table to drop.
        """
        self._backend.drop_table(table_name)

    def has(self, table_name):
        """Check if a table exists."""
        return self._backend.table_exists(table_name)

    def create_table(self, table_name, columns):
        """Create a table with explicit Column definitions.

        Use this when you need constraints like ``unique``, ``nullable=False``,
        or custom defaults. For simple cases, use ``add()`` to auto-create.
        """
        self._backend.create_table(table_name, columns)

    def insert_many(self, table, rows):
        """Insert multiple rows (alias for add with a list)."""
        self._backend.insert_many(table, rows)

    def query(self, table):
        """Access the query builder directly."""
        return self._backend.query(table)

    def get_tables(self):
        """List all table names (alias for tables())."""
        return self._backend.get_tables()

    def get_schema(self, table):
        """Get the schema for a table."""
        return self._backend.get_schema(table)

    def write(self, key, value):
        """Store a key-value pair."""
        return self._backend.write(key, value)

    def read(self, key, default=None):
        """Read a value by key."""
        return self._backend.read(key, default=default)

    def delete_key(self, key):
        """Delete a key-value pair."""
        return self._backend.delete_key(key)

    def keys(self, pattern=None):
        """List keys, optionally filtered by pattern."""
        return self._backend.keys(pattern)

    @property
    def backend(self):
        """Access the underlying DatabaseBackend directly."""
        return self._backend

    def close(self):
        """Close the database connection."""
        self._backend.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __repr__(self):
        return f"SimpleClient({self._backend!r})"


def _build_column(name, python_type):
    """Build a Column from a Python type.

    Args:
        name: Column name.
        python_type: A Python type (str, int, float, bool, bytes, dict, list).

    Returns:
        Column instance.
    """
    if python_type not in _TYPE_MAP:
        raise TypeError(
            f"Unsupported type {python_type.__name__}. "
            f"Supported: {', '.join(t.__name__ for t in _TYPE_MAP)}"
        )

    col_type_cls = _TYPE_MAP[python_type]
    kwargs = {}

    if python_type is str:
        kwargs["nullable"] = False
    elif python_type is bool:
        kwargs["default"] = True

    return Column(name, col_type_cls(), **kwargs)
