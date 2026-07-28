"""
Column type definitions for sqbooster table schemas.

Each type maps to SQL column types and handles serialization/deserialization.
"""


class ColumnType:
    """Base class for all column types."""
    sql_type = ""
    python_type = object

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    def to_sql(self, value):
        """Convert a Python value to SQL-compatible format."""
        if value is None:
            return None
        return value

    def from_sql(self, value):
        """Convert a SQL value back to Python format."""
        return value

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class Integer(ColumnType):
    """Integer column type. Maps to INTEGER in SQL."""
    sql_type = "INTEGER"
    python_type = int

    def to_sql(self, value):
        if value is None:
            return None
        return int(value)

    def from_sql(self, value):
        if value is None:
            return None
        return int(value)


class Text(ColumnType):
    """Text/string column type. Maps to TEXT/VARCHAR in SQL."""
    sql_type = "TEXT"
    python_type = str

    def __init__(self, max_length=None):
        self.max_length = max_length

    def to_sql(self, value):
        if value is None:
            return None
        return str(value)

    def from_sql(self, value):
        if value is None:
            return None
        return str(value)

    def __repr__(self):
        if self.max_length:
            return f"Text(max_length={self.max_length})"
        return "Text()"


class Float(ColumnType):
    """Floating-point column type. Maps to REAL/FLOAT in SQL."""
    sql_type = "REAL"
    python_type = float

    def to_sql(self, value):
        if value is None:
            return None
        return float(value)

    def from_sql(self, value):
        if value is None:
            return None
        return float(value)


class Boolean(ColumnType):
    """Boolean column type. Maps to INTEGER (0/1) in SQLite or BOOLEAN in PostgreSQL."""
    sql_type = "INTEGER"
    python_type = bool

    def to_sql(self, value):
        if value is None:
            return None
        return int(bool(value))

    def from_sql(self, value):
        if value is None:
            return None
        return bool(value)


class Blob(ColumnType):
    """Binary large object column type. Maps to BLOB in SQL.
    Used for storing pickled Python objects or raw bytes.
    Non-bytes values are automatically pickled on write."""
    sql_type = "BLOB"
    python_type = bytes

    def to_sql(self, value):
        if value is None:
            return None
        if isinstance(value, bytes):
            return value
        import pickle as _pickle
        return _pickle.dumps(value)

    def from_sql(self, value):
        if value is None:
            return None
        if isinstance(value, (dict, list, int, float, str, bool)):
            return value
        import pickle as _pickle
        try:
            return _pickle.loads(value)
        except Exception:
            return value


class Timestamp(ColumnType):
    """Timestamp column type. Maps to TIMESTAMP in SQL."""
    sql_type = "TIMESTAMP"
    python_type = str

    def to_sql(self, value):
        if value is None:
            return None
        return str(value)

    def from_sql(self, value):
        if value is None:
            return None
        return str(value)


class Real(ColumnType):
    """Alias for Float. Maps to REAL in SQL."""
    sql_type = "REAL"
    python_type = float

    def to_sql(self, value):
        if value is None:
            return None
        return float(value)

    def from_sql(self, value):
        if value is None:
            return None
        return float(value)


class VARCHAR(ColumnType):
    """VARCHAR column type with optional max length."""
    sql_type = "VARCHAR"
    python_type = str

    def __init__(self, max_length=255):
        self.max_length = max_length

    @property
    def sql_type_with_length(self):
        return f"VARCHAR({self.max_length})"

    def to_sql(self, value):
        if value is None:
            return None
        return str(value)

    def from_sql(self, value):
        if value is None:
            return None
        return str(value)

    def __repr__(self):
        return f"VARCHAR(max_length={self.max_length})"


class JSON(ColumnType):
    """JSON column type. Stores JSON-serialized data as TEXT in SQLite,
    native JSONB in PostgreSQL."""
    sql_type = "TEXT"
    python_type = dict

    def to_sql(self, value):
        import json as _json
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return _json.dumps(value, ensure_ascii=False)

    def from_sql(self, value):
        import json as _json
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return value
        try:
            return _json.loads(value)
        except (ValueError, TypeError):
            return value


class Pickle(ColumnType):
    """Pickle column type. Stores arbitrary Python objects as pickled BLOBs.
    Use with caution - not portable across Python versions."""
    sql_type = "BLOB"
    python_type = object

    def to_sql(self, value):
        import pickle as _pickle
        if value is None:
            return None
        return _pickle.dumps(value)

    def from_sql(self, value):
        import pickle as _pickle
        if value is None:
            return None
        if isinstance(value, dict):
            return value
        try:
            return _pickle.loads(value)
        except Exception:
            return value
