"""
Schema definition classes for sqbooster table system.

Provides Column and TableSchema classes for defining database table structure.
"""

from .types import ColumnType, Integer, Text


class Column:
    """Defines a database column with type and constraints.

    Args:
        name: Column name.
        col_type: Column type instance (e.g., Integer(), Text(), Float()).
        primary_key: Whether this column is the primary key.
        nullable: Whether NULL values are allowed.
        unique: Whether values must be unique.
        default: Default value for the column.
        autoincrement: Whether the value auto-increments (primary key only).

    Example:
        Column("id", Integer(), primary_key=True, autoincrement=True)
        Column("name", Text(), nullable=False)
        Column("age", Integer(), default=0)
    """

    def __init__(self, name, col_type, primary_key=False, nullable=True,
                 unique=False, default=None, autoincrement=False):
        if not isinstance(col_type, ColumnType):
            raise TypeError(
                f"col_type must be a ColumnType instance, got {type(col_type).__name__}. "
                f"Example: Column('name', Text())"
            )
        self.name = name
        self.col_type = col_type
        self.primary_key = primary_key
        self.nullable = nullable
        self.unique = unique
        self.default = default
        self.autoincrement = autoincrement

        if primary_key:
            self.nullable = False

    @property
    def sql_type(self):
        """Return the SQL type string, accounting for VARCHAR length."""
        from .types import VARCHAR
        if isinstance(self.col_type, VARCHAR):
            return self.col_type.sql_type_with_length
        return self.col_type.sql_type

    def to_sql_definition(self, backend="sqlite"):
        """Generate the SQL column definition fragment.

        Args:
            backend: 'sqlite' or 'postgresql' to handle dialect differences.
        """
        parts = [self.name, self.sql_type]

        if self.primary_key:
            parts.append("PRIMARY KEY")
            if self.autoincrement:
                if backend == "sqlite":
                    parts.append("AUTOINCREMENT")
                elif backend == "postgresql":
                    pass

        if not self.nullable and not self.primary_key:
            parts.append("NOT NULL")

        if self.unique and not self.primary_key:
            parts.append("UNIQUE")

        if self.default is not None and not self.autoincrement:
            parts.append(f"DEFAULT {self._format_default()}")

        return " ".join(parts)

    def _format_default(self):
        """Format the default value for SQL insertion."""
        if isinstance(self.default, bool):
            return "1" if self.default else "0"
        if isinstance(self.default, (int, float)):
            return str(self.default)
        if isinstance(self.default, str):
            return f"'{self.default}'"
        return str(self.default)

    def to_python(self, value):
        """Convert a SQL value to Python type using the column's type."""
        return self.col_type.from_sql(value)

    def to_sql(self, value):
        """Convert a Python value to SQL format using the column's type."""
        return self.col_type.to_sql(value)

    def __repr__(self):
        flags = []
        if self.primary_key:
            flags.append("PK")
        if self.autoincrement:
            flags.append("AI")
        if not self.nullable:
            flags.append("NOT NULL")
        if self.unique:
            flags.append("UNIQUE")
        if self.default is not None:
            flags.append(f"DEFAULT={self.default}")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        return f"Column({self.name}, {self.col_type}{flag_str})"


class TableSchema:
    """Defines a complete table schema with columns and metadata.

    Args:
        name: Table name.
        columns: List of Column instances.
    """

    def __init__(self, name, columns):
        if not columns:
            raise ValueError("Table must have at least one column")

        self.name = name
        self.columns = list(columns)
        self._column_map = {col.name: col for col in self.columns}
        self._pk = next((col for col in self.columns if col.primary_key), None)

    @property
    def primary_key(self):
        """Return the primary key column, or None."""
        return self._pk

    def get_column(self, name):
        """Get a column by name.

        Raises:
            KeyError: If column doesn't exist.
        """
        if name not in self._column_map:
            raise KeyError(f"Column '{name}' not found in table '{self.name}'")
        return self._column_map[name]

    def has_column(self, name):
        """Check if a column exists."""
        return name in self._column_map

    def to_sql_create(self, backend="sqlite"):
        """Generate the CREATE TABLE SQL statement.

        Args:
            backend: 'sqlite' or 'postgresql'.
        """
        col_defs = [col.to_sql_definition(backend) for col in self.columns]
        cols_str = ",\n    ".join(col_defs)
        return f"CREATE TABLE IF NOT EXISTS {self.name} (\n    {cols_str}\n)"

    def validate_row(self, data):
        """Validate a data dict against this schema.

        Args:
            data: Dictionary of column_name -> value.

        Raises:
            ValueError: If validation fails.
        """
        for col in self.columns:
            if col.name not in data:
                if col.primary_key and col.autoincrement:
                    continue
                if col.default is not None:
                    data[col.name] = col.default
                elif col.nullable:
                    data[col.name] = None
                else:
                    raise ValueError(
                        f"Column '{col.name}' is NOT NULL but not provided in data"
                    )

        unknown = set(data.keys()) - set(self._column_map.keys())
        if unknown:
            raise ValueError(
                f"Unknown columns for table '{self.name}': {unknown}"
            )

        return data

    def prepare_insert(self, data):
        """Prepare data for INSERT: validate and convert Python values to SQL.

        Returns:
            Tuple of (column_names, sql_values).
        """
        validated = self.validate_row(dict(data))
        sql_cols = []
        sql_vals = []
        for col_name, value in validated.items():
            col = self._column_map[col_name]
            sql_cols.append(col_name)
            sql_vals.append(col.to_sql(value))
        return sql_cols, sql_vals

    def row_to_dict(self, row, column_names=None):
        """Convert a SQL row (tuple) back to a Python dict.

        Args:
            row: Tuple of values.
            column_names: List of column names matching the row values.
        """
        if column_names is None:
            column_names = [col.name for col in self.columns]
        result = {}
        for name, value in zip(column_names, row):
            col = self._column_map.get(name)
            if col:
                result[name] = col.to_python(value)
            else:
                result[name] = value
        return result

    def __repr__(self):
        col_str = ", ".join(repr(c) for c in self.columns)
        return f"TableSchema({self.name}, [{col_str}])"
