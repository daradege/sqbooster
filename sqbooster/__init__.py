"""
sqbooster - A flexible Python library for database access with real tables and easy querying.

sqbooster provides a consistent interface across SQLite, PostgreSQL, and more.
It supports both a key-value API (for backward compatibility) and a full
relational table API with schema definitions, typed columns, and a chainable
query builder.

Key Features:

- Real typed tables (not JSON blobs in a value column)
- Chainable query builder with filters, ordering, pagination
- JSON and pickle serialization (configurable per-backend)
- Backend switching (SQLite to PostgreSQL)
- Backward-compatible key-value API
- Optional support for Redis, MongoDB
"""

from .backends import DatabaseBackend
from .backends.sqlite import SQLiteBackend
from .backends.postgresql import PostgreSQLBackend
from .schema import Column, TableSchema
from .types import (
    Integer, Text, Float, Boolean, Blob, Timestamp,
    Real, VARCHAR, JSON, Pickle, ColumnType,
)
from .query import Query
from .simple import SimpleClient
from .exceptions import (
    DatabaseError, DatabaseConnectionError,
    KeyNotFoundError, SerializationError,
    TableNotFoundError, SchemaError,
)


def sqlite(name=":memory:", **kwargs):
    """Create a SimpleClient backed by SQLite.

    Example::

        import sqbooster
        db = sqbooster.sqlite("mydb.db")
    """
    return SimpleClient.sqlite(name=name, **kwargs)


def postgresql(**kwargs):
    """Create a SimpleClient backed by PostgreSQL.

    Example::

        import sqbooster
        db = sqbooster.postgresql(host="localhost", name="mydb")
    """
    return SimpleClient.postgresql(**kwargs)


def json(path, **kwargs):
    """Create a SimpleClient backed by a JSON file.

    Example::

        import sqbooster
        db = sqbooster.json("data.json")
    """
    return SimpleClient.json(path=path, **kwargs)


def pickle(path, **kwargs):
    """Create a SimpleClient backed by a Pickle file.

    Example::

        import sqbooster
        db = sqbooster.pickle("data.pkl")
    """
    return SimpleClient.pickle(path=path, **kwargs)


def redis(**kwargs):
    """Create a SimpleClient backed by Redis.

    Example::

        import sqbooster
        db = sqbooster.redis(host="localhost")
    """
    return SimpleClient.redis(**kwargs)


def mongo(**kwargs):
    """Create a SimpleClient backed by MongoDB.

    Example::

        import sqbooster
        db = sqbooster.mongo(uri="mongodb://localhost:27017")
    """
    return SimpleClient.mongo(**kwargs)
