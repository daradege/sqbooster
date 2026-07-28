"""
Database backends for sqbooster.

All backends implement the DatabaseBackend interface, making them
fully interchangeable. Switch backends by changing only the constructor.

Table-capable backends (recommended):
    - SQLiteBackend       (sqbooster.backends)
    - PostgreSQLBackend   (sqbooster.backends)
    - JSONFileDatabase    (sqbooster.databases)
    - PickleFileDatabase  (sqbooster.databases)
    - RedisDatabase       (sqbooster.databases)
    - MongoDatabase       (sqbooster.databases)

Legacy wrappers (backward compatible key-value only):
    - SQLiteDatabase      (delegates to SQLiteBackend)
    - PostgreSQLDatabase  (delegates to PostgreSQLBackend)
"""

from ..backends import DatabaseBackend
from ..backends.sqlite import SQLiteBackend
from ..backends.postgresql import PostgreSQLBackend
from .sqlite import SQLiteDatabase
from .postgresql import PostgreSQLDatabase
from .jsonfile import JSONFileDatabase
from .picklefile import PickleFileDatabase

try:
    from .redis import RedisDatabase
except ImportError:
    pass

try:
    from .mongo import MongoDatabase
except ImportError:
    pass
