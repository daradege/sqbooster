"""
This module defines exceptions used in the sqbooster package.
"""


class DatabaseError(Exception):
    """Base exception for all database operations."""
    pass


class KeyNotFoundError(DatabaseError):
    """Raised when a key is not found in the database."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when there is an issue with the database connection."""
    pass



ConnectionError = DatabaseConnectionError


class SerializationError(DatabaseError):
    """Raised when there is an issue with serialization/deserialization."""
    pass


class TableNotFoundError(DatabaseError):
    """Raised when a referenced table does not exist."""
    pass


class SchemaError(DatabaseError):
    """Raised when there is a schema definition or validation error."""
    pass
