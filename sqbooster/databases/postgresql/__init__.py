"""
The `sqbooster.databases.postgresql` module provides backward-compatible PostgreSQL access.

For new code, prefer using `sqbooster.backends.postgresql.PostgreSQLBackend` directly.
"""

from ...backends.postgresql import PostgreSQLBackend
from ...backends import DatabaseBackend

try:
    import psycopg2

    class PostgreSQLDatabase(PostgreSQLBackend):
        """Backward-compatible PostgreSQL key-value database.

        Delegates everything to PostgreSQLBackend. Inherits the full
        DatabaseBackend interface including table operations.

        Args:
            name: Database name. Defaults to "testdb".
            host: Database host. Defaults to "localhost".
            port: Database port. Defaults to 5432.
            user: Database user. Defaults to "postgres".
            password: Database password. Defaults to "".
            auto_commit: Auto commit flag. Defaults to True.
        """

        def __init__(self, name="testdb", host="localhost", port=5432,
                     user="postgres", password="", auto_commit=True):
            super().__init__(
                host=host, port=port, name=name, user=user,
                password=password, auto_commit=auto_commit, serialization="json"
            )

except ImportError:
    class PostgreSQLDatabase:
        def __init__(self, *args, **kwargs):
            raise ImportError("Psycopg2 library not installed. Install with: pip install psycopg2-binary")
