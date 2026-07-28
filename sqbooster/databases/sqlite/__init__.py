"""
The `sqbooster.databases.sqlite` module provides backward-compatible SQLite access.

For new code, prefer using `sqbooster.backends.sqlite.SQLiteBackend` directly.
"""

from ...backends.sqlite import SQLiteBackend
from ...backends import DatabaseBackend


class SQLiteDatabase(SQLiteBackend):
    """Backward-compatible SQLite key-value database.

    This class delegates everything to SQLiteBackend. It inherits the full
    DatabaseBackend interface including table operations.

    Args:
        name: The name/path of the SQLite database file.
        auto_commit: Whether to automatically commit changes. Defaults to True.

    Example:
        # Old key-value API
        db = SQLiteDatabase("test.db")
        db.write("key1", {"name": "test"})
        print(db.read("key1"))

        # New table API also works (inherited from SQLiteBackend)
        from sqbooster.schema import Column
        from sqbooster.types import Integer, Text
        db.create_table("users", [Column("id", Integer()), Column("name", Text())])
        db.insert("users", {"name": "Ali"})
    """

    def __init__(self, name=":memory:", auto_commit=True):
        super().__init__(name=name, auto_commit=auto_commit, serialization="json")
