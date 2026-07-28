"""
Query builders for sqbooster database backends.

Provides a chainable, database-agnostic query interface for both SQL
and in-memory (non-SQL) backends.

Supported filter operators:
    field=value          WHERE field = value
    field__ne=value      WHERE field != value
    field__gt=value      WHERE field > value
    field__gte=value     WHERE field >= value
    field__lt=value      WHERE field < value
    field__lte=value     WHERE field <= value
    field__like=value    WHERE field LIKE value
    field__contains=v    WHERE field LIKE '%value%'
    field__startswith=v  WHERE field LIKE 'value%'
    field__endswith=v    WHERE field LIKE '%value'
    field__in=value      WHERE field IN (value)  (value must be list/tuple)
    field__notin=value   WHERE field NOT IN (value)
    field__isnull=True   WHERE field IS NULL
    field__isnull=False  WHERE field IS NOT NULL
"""

import re
from typing import Any, Dict, List, Optional, Tuple


OPERATORS = {
    "ne": "!=",
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
    "like": "LIKE",
    "contains": "LIKE",
    "startswith": "LIKE",
    "endswith": "LIKE",
    "in": "IN",
    "notin": "NOT IN",
    "isnull": "IS NULL",
}


class Query:
    """Chainable query builder for database operations.

    Args:
        backend: A DatabaseBackend instance.
        table: Table name to query.

    Example:
        results = (db.query("users")
            .filter(age__gte=25)
            .filter(name__like="%Ali%")
            .order_by("-age")
            .limit(10)
            .all())
    """

    def __init__(self, backend, table):
        self._backend = backend
        self._table = table
        self._filters = []
        self._order_by_cols = []
        self._limit_val = None
        self._offset_val = None
        self._select_cols = None

    @property
    def placeholder(self):
        """Return the placeholder character for this backend."""
        return self._backend.placeholder

    def filter(self, **kwargs):
        """Add filter conditions to the query.

        Uses double-underscore notation for operators:
            filter(age__gt=25, name__like="%Ali%")
        """
        for key, value in kwargs.items():
            self._filters.append((key, value))
        return self

    def order_by(self, *columns):
        """Set ordering. Prefix with '-' for descending.

        Example:
            order_by("name")        -> ORDER BY name ASC
            order_by("-age", "name") -> ORDER BY age DESC, name ASC
        """
        self._order_by_cols = list(columns)
        return self

    def limit(self, n):
        """Limit the number of results."""
        self._limit_val = int(n)
        return self

    def offset(self, n):
        """Offset the results (for pagination)."""
        self._offset_val = int(n)
        return self

    def select(self, *columns):
        """Select specific columns instead of all.

        Example:
            select("name", "email")
        """
        self._select_cols = list(columns)
        return self

    def _parse_filter(self, key, value):
        """Parse a filter key/value into SQL fragment and params.

        Returns:
            Tuple of (sql_fragment, params_list).
        """
        ph = self.placeholder

        if "__" in key:
            field, op = key.rsplit("__", 1)

            if op == "ne":
                return f"{field} != {ph}", [value]
            elif op == "gt":
                return f"{field} > {ph}", [value]
            elif op == "gte":
                return f"{field} >= {ph}", [value]
            elif op == "lt":
                return f"{field} < {ph}", [value]
            elif op == "lte":
                return f"{field} <= {ph}", [value]
            elif op == "like":
                return f"{field} LIKE {ph}", [value]
            elif op == "contains":
                return f"{field} LIKE {ph}", [f"%{value}%"]
            elif op == "startswith":
                return f"{field} LIKE {ph}", [f"{value}%"]
            elif op == "endswith":
                return f"{field} LIKE {ph}", [f"%{value}"]
            elif op == "in":
                if not isinstance(value, (list, tuple)):
                    value = [value]
                placeholders = ", ".join([ph] * len(value))
                return f"{field} IN ({placeholders})", list(value)
            elif op == "notin":
                if not isinstance(value, (list, tuple)):
                    value = [value]
                placeholders = ", ".join([ph] * len(value))
                return f"{field} NOT IN ({placeholders})", list(value)
            elif op == "isnull":
                if value:
                    return f"{field} IS NULL", []
                else:
                    return f"{field} IS NOT NULL", []
            else:
                raise ValueError(f"Unknown filter operator: {op}")
        else:
            if value is None:
                return f"{key} IS NULL", []
            return f"{key} = {ph}", [value]

    def _build_where(self):
        """Build the WHERE clause from filters.

        Returns:
            Tuple of (where_sql, params).
        """
        if not self._filters:
            return "", []

        clauses = []
        params = []
        for key, value in self._filters:
            clause, clause_params = self._parse_filter(key, value)
            clauses.append(clause)
            params.extend(clause_params)

        return " WHERE " + " AND ".join(clauses), params

    def _build_where_from_filters(self, filters):
        """Build a WHERE clause from a dict of filters.

        Used internally by backends for update/delete operations.

        Args:
            filters: Dict of filter_key -> value (e.g. {'age__gt': 25, 'name': 'Ali'}).

        Returns:
            Tuple of (where_sql, params).
        """
        if not filters:
            return "", []

        clauses = []
        params = []
        for key, value in filters.items():
            clause, clause_params = self._parse_filter(key, value)
            clauses.append(clause)
            params.extend(clause_params)

        return " WHERE " + " AND ".join(clauses), params

    def _build_order_by(self):
        """Build the ORDER BY clause.

        Returns:
            SQL string fragment.
        """
        if not self._order_by_cols:
            return ""

        parts = []
        for col in self._order_by_cols:
            if col.startswith("-"):
                parts.append(f"{col[1:]} DESC")
            else:
                parts.append(f"{col} ASC")

        return " ORDER BY " + ", ".join(parts)

    def _build_limit_offset(self):
        """Build LIMIT and OFFSET clauses.

        Returns:
            SQL string fragment.
        """
        parts = []
        if self._limit_val is not None:
            parts.append(f"LIMIT {self._limit_val}")
        if self._offset_val is not None:
            parts.append(f"OFFSET {self._offset_val}")
        return " " + " ".join(parts) if parts else ""

    def _build_select(self):
        """Build the SELECT column list.

        Returns:
            Column names string.
        """
        if self._select_cols:
            return ", ".join(self._select_cols)
        return "*"

    def build(self):
        """Build the complete SQL query.

        Returns:
            Tuple of (sql_string, params_list).
        """
        select_cols = self._build_select()
        where_sql, params = self._build_where()
        order_sql = self._build_order_by()
        limit_sql = self._build_limit_offset()

        sql = f"SELECT {select_cols} FROM {self._table}{where_sql}{order_sql}{limit_sql}"
        return sql, params

    def build_count(self):
        """Build a COUNT query.

        Returns:
            Tuple of (sql_string, params_list).
        """
        where_sql, params = self._build_where()
        sql = f"SELECT COUNT(*) FROM {self._table}{where_sql}"
        return sql, params

    def all(self):
        """Execute the query and return all results as list of dicts.

        Results are type-converted using the table schema when available.

        Returns:
            List of dictionaries, one per row.
        """
        sql, params = self.build()
        rows = self._backend.execute(sql, params, fetch=True)
        return self._convert_rows(rows)

    def first(self):
        """Execute the query and return only the first result.

        Returns:
            Dictionary for the first row, or None if no results.
        """
        self._limit_val = 1
        results = self.all()
        return results[0] if results else None

    def one(self):
        """Execute the query and return exactly one result.

        Returns:
            Dictionary for the single row.

        Raises:
            ValueError: If zero or more than one row is returned.
        """
        results = self.all()
        if len(results) == 0:
            raise ValueError("Query returned no results")
        if len(results) > 1:
            raise ValueError(f"Query returned {len(results)} results, expected 1")
        return results[0]

    def count(self):
        """Execute a COUNT query and return the number of matching rows.

        Returns:
            Integer count.
        """
        sql, params = self.build_count()
        result = self._backend.execute(sql, params, fetch=True)
        if result:
            return result[0].get("COUNT(*)", 0) if isinstance(result[0], dict) else list(result[0].values())[0]
        return 0

    def exists(self):
        """Check if any matching rows exist.

        Returns:
            Boolean.
        """
        return self.count() > 0

    def _convert_rows(self, rows):
        """Apply schema type conversion to query result rows.

        Converts raw SQL values back to Python types using column definitions.
        """
        if not rows:
            return rows
        try:
            schema = self._backend.get_schema(self._table)
        except Exception:
            return rows
        result = []
        for row in rows:
            converted = {}
            for key, value in row.items():
                col = schema._column_map.get(key)
                if col:
                    converted[key] = col.to_python(value)
                else:
                    converted[key] = value
            result.append(converted)
        return result

    def __repr__(self):
        sql, params = self.build()
        return f"Query({sql!r}, params={params})"


class InMemoryQuery:
    """Chainable query builder that operates on in-memory Python data.

    Used by non-SQL backends (JSON, Pickle, Redis, Mongo) to provide
    the same query API as the SQL Query class without generating SQL.

    Args:
        rows: List of dicts representing table rows.
        schema: Optional TableSchema for type-aware operations.

    Example:
        query = InMemoryQuery(rows, schema)
        results = query.filter(age__gte=25).order_by("-name").all()
    """

    def __init__(self, rows, schema=None):
        self._rows = rows
        self._schema = schema
        self._filters = []
        self._order_by_cols = []
        self._limit_val = None
        self._offset_val = None
        self._select_cols = None

    def filter(self, **kwargs):
        """Add filter conditions (same operators as Query)."""
        for key, value in kwargs.items():
            self._filters.append((key, value))
        return self

    def order_by(self, *columns):
        """Set ordering. Prefix with '-' for descending."""
        self._order_by_cols = list(columns)
        return self

    def limit(self, n):
        self._limit_val = int(n)
        return self

    def offset(self, n):
        self._offset_val = int(n)
        return self

    def select(self, *columns):
        self._select_cols = list(columns)
        return self

    @staticmethod
    def _like_match(value, pattern):
        """Check if value matches a SQL LIKE pattern (% and _)."""
        if value is None:
            return False
        value = str(value)
        regex_parts = []
        for char in pattern:
            if char == '%':
                regex_parts.append('.*')
            elif char == '_':
                regex_parts.append('.')
            else:
                regex_parts.append(re.escape(char))
        regex = '^' + ''.join(regex_parts) + '$'
        return bool(re.fullmatch(regex, value))

    def _matches_filter(self, row, key, value):
        """Check if a single row matches a single filter condition."""
        if "__" in key:
            field, op = key.rsplit("__", 1)
        else:
            field = key
            op = "eq"

        row_val = row.get(field)

        if op == "eq":
            if value is None:
                return row_val is None
            return row_val == value
        elif op == "ne":
            if value is None:
                return row_val is not None
            return row_val != value
        elif op == "gt":
            return row_val is not None and row_val > value
        elif op == "gte":
            return row_val is not None and row_val >= value
        elif op == "lt":
            return row_val is not None and row_val < value
        elif op == "lte":
            return row_val is not None and row_val <= value
        elif op == "like":
            return self._like_match(row_val, value)
        elif op == "contains":
            return self._like_match(row_val, f"%{value}%")
        elif op == "startswith":
            return self._like_match(row_val, f"{value}%")
        elif op == "endswith":
            return self._like_match(row_val, f"%{value}")
        elif op == "in":
            if not isinstance(value, (list, tuple)):
                value = [value]
            return row_val in value
        elif op == "notin":
            if not isinstance(value, (list, tuple)):
                value = [value]
            return row_val not in value
        elif op == "isnull":
            if value:
                return row_val is None
            else:
                return row_val is not None
        else:
            raise ValueError(f"Unknown filter operator: {op}")

    def _apply_filters(self, rows):
        if not self._filters:
            return list(rows)
        result = []
        for row in rows:
            if all(self._matches_filter(row, key, val) for key, val in self._filters):
                result.append(row)
        return result

    def _apply_order(self, rows):
        if not self._order_by_cols:
            return rows

        def sort_key(row):
            keys = []
            for col in self._order_by_cols:
                if col.startswith("-"):
                    actual = col[1:]
                    val = row.get(actual)
                    
                    keys.append((0, _SortWrapper(val, reverse=True)))
                else:
                    val = row.get(col)
                    keys.append((0, _SortWrapper(val, reverse=False)))
            return keys

        return sorted(rows, key=sort_key)

    def _apply_limit_offset(self, rows):
        start = self._offset_val or 0
        end = start + self._limit_val if self._limit_val is not None else None
        return rows[start:end]

    def _apply_select(self, rows):
        if not self._select_cols:
            return rows
        return [{k: row[k] for k in self._select_cols if k in row} for row in rows]

    def _execute(self):
        rows = self._apply_filters(self._rows)
        rows = self._apply_order(rows)
        rows = self._apply_limit_offset(rows)
        rows = self._apply_select(rows)
        return rows

    def all(self):
        """Return all matching rows."""
        return self._execute()

    def first(self):
        """Return the first matching row, or None."""
        self._limit_val = 1
        results = self._execute()
        return results[0] if results else None

    def one(self):
        """Return exactly one matching row. Raises ValueError otherwise."""
        results = self._execute()
        if len(results) == 0:
            raise ValueError("Query returned no results")
        if len(results) > 1:
            raise ValueError(f"Query returned {len(results)} results, expected 1")
        return results[0]

    def count(self):
        """Return the count of matching rows."""
        return len(self._apply_filters(self._rows))

    def exists(self):
        """Return True if any matching rows exist."""
        return self.count() > 0

    def __repr__(self):
        return f"InMemoryQuery(rows={len(self._rows)}, filters={len(self._filters)})"


class _SortWrapper:
    """Helper for sorting mixed types in InMemoryQuery."""

    def __init__(self, value, reverse=False):
        self.value = value
        self.reverse = reverse

    def __lt__(self, other):
        if self.value is None:
            return True
        if other.value is None:
            return False
        if self.reverse:
            return other.value < self.value
        return self.value < other.value

    def __eq__(self, other):
        return self.value == other.value
