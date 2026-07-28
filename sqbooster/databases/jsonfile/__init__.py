"""
JSON file database backend for sqbooster.

Stores key-value pairs and table data in a single JSON file.
Supports the full DatabaseBackend interface with in-memory querying.
"""

import json
import os
from typing import Any, Dict, List

from ...exceptions import DatabaseError, DatabaseConnectionError
from ...schema import Column, TableSchema
from ...query import InMemoryQuery
from ...types import Integer, Text, Float, Boolean, Blob, Timestamp
from ...backends import DatabaseBackend


class JSONFileDatabase(DatabaseBackend):
    """A file-based JSON database implementing the full DatabaseBackend interface.

    Data is stored in-memory and persisted to a JSON file on commit.
    Supports both key-value operations and real typed tables.

    Args:
        name: Filename for the JSON database.
        auto_commit: Whether to automatically save changes to file.

    Example:
        db = JSONFileDatabase("app.json")
        db.create_table("users", [Column("id", Integer()), Column("name", Text())])
        db.insert("users", {"name": "Ali"})
        results = db.query("users").filter(name="Ali").all()
    """

    placeholder = ":ph"

    def __init__(self, name="database.json", auto_commit=True, serialization="json"):
        self.name = name
        self.auto_commit = auto_commit
        self.serialization = serialization
        self._kv_data = {}
        self._tables = {}
        self._schemas = {}
        self._table_rows = {}

        try:
            if os.path.exists(name):
                with open(name, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        file_data = json.loads(content)
                        self._kv_data = file_data.get("_kv_data", {})
                        self._schemas = file_data.get("_schemas", {})
                        self._table_rows = file_data.get("_tables", {})
                        for tname, sdata in self._schemas.items():
                            if isinstance(sdata, dict) and "columns" in sdata:
                                self._tables[tname] = self._deserialize_schema(sdata)
                            else:
                                self._tables[tname] = sdata
        except (json.JSONDecodeError, IOError) as e:
            raise DatabaseConnectionError(f"Failed to initialize JSON database: {e}")

    def _save_to_file(self):
        try:
            serializable_schemas = {}
            for tname, schema in self._schemas.items():
                if isinstance(schema, TableSchema):
                    serializable_schemas[tname] = self._serialize_schema(schema)
                else:
                    serializable_schemas[tname] = schema

            with open(self.name, "w", encoding="utf-8") as f:
                json.dump({
                    "_kv_data": self._kv_data,
                    "_schemas": serializable_schemas,
                    "_tables": self._table_rows,
                }, f, indent=2, ensure_ascii=False, default=str)
        except IOError as e:
            raise DatabaseError(f"Failed to save to file: {e}")

    def _serialize_schema(self, schema):
        cols = []
        for col in schema.columns:
            cols.append({
                "name": col.name,
                "type": type(col.col_type).__name__,
                "primary_key": col.primary_key,
                "nullable": col.nullable,
                "unique": col.unique,
                "default": col.default,
                "autoincrement": col.autoincrement,
            })
        return {"name": schema.name, "columns": cols}

    def _deserialize_schema(self, data):
        from ...types import Integer, Text, Float, Boolean, Blob, Timestamp, Real, VARCHAR, JSON as JSONType, Pickle
        type_map = {
            "Integer": Integer, "Text": Text, "Float": Float, "Real": Real,
            "Boolean": Boolean, "Blob": Blob, "Timestamp": Timestamp,
            "VARCHAR": VARCHAR, "JSON": JSONType, "Pickle": Pickle,
        }
        columns = []
        for col_data in data["columns"]:
            type_class = type_map.get(col_data["type"], Text)
            col_type = type_class()
            columns.append(Column(
                col_data["name"], col_type,
                primary_key=col_data.get("primary_key", False),
                nullable=col_data.get("nullable", True),
                unique=col_data.get("unique", False),
                default=col_data.get("default"),
                autoincrement=col_data.get("autoincrement", False),
            ))
        return TableSchema(data["name"], columns)

    

    def create_table(self, name, columns):
        if isinstance(columns, TableSchema):
            schema = columns
        else:
            schema = TableSchema(name, columns)
        self._tables[name] = schema
        self._schemas[name] = schema
        if name not in self._table_rows:
            self._table_rows[name] = []
        if self.auto_commit:
            self._save_to_file()
        return True

    def drop_table(self, name, if_exists=True):
        if name not in self._tables:
            if not if_exists:
                raise DatabaseError(f"Table '{name}' does not exist")
            return True
        del self._tables[name]
        self._schemas.pop(name, None)
        self._table_rows.pop(name, None)
        if self.auto_commit:
            self._save_to_file()
        return True

    def table_exists(self, name):
        return name in self._tables

    def get_tables(self):
        return list(self._tables.keys())

    def get_schema(self, table_name):
        if table_name in self._tables:
            return self._tables[table_name]
        raise DatabaseError(f"Table '{table_name}' does not exist")

    

    def insert(self, table, data):
        schema = self._get_schema_or_raise(table)
        validated = schema.validate_row(dict(data))

        if schema.primary_key and schema.primary_key.autoincrement:
            pk_name = schema.primary_key.name
            if pk_name not in validated or validated[pk_name] is None:
                existing = self._table_rows.get(table, [])
                max_id = max((r.get(pk_name, 0) for r in existing), default=0)
                validated[pk_name] = max_id + 1

        self._table_rows.setdefault(table, []).append(validated)
        if self.auto_commit:
            self._save_to_file()
        return True

    def insert_many(self, table, data_list):
        for data in data_list:
            self.insert(table, data)
        return True

    def update(self, table, data, **filters):
        schema = self._get_schema_or_raise(table)
        rows = self._table_rows.get(table, [])
        query = InMemoryQuery(rows, schema).filter(**filters)
        matching = query.all()
        count = 0
        for match in matching:
            for row in rows:
                if all(row.get(k) == v for k, v in match.items() if k in row):
                    row.update(data)
                    count += 1
                    break
        if self.auto_commit and count > 0:
            self._save_to_file()
        return count

    def delete(self, table, **filters):
        schema = self._get_schema_or_raise(table)
        rows = self._table_rows.get(table, [])
        if not filters:
            count = len(rows)
            self._table_rows[table] = []
            if self.auto_commit and count > 0:
                self._save_to_file()
            return count

        query = InMemoryQuery(rows, schema).filter(**filters)
        matching = query.all()
        match_set = [id(m) for m in matching]

        new_rows = []
        deleted = 0
        for row in rows:
            is_match = False
            for match in matching:
                if all(row.get(k) == v for k, v in match.items() if k in row):
                    is_match = True
                    break
            if not is_match:
                new_rows.append(row)
            else:
                deleted += 1

        self._table_rows[table] = new_rows
        if self.auto_commit and deleted > 0:
            self._save_to_file()
        return deleted

    def query(self, table):
        schema = self._get_schema_or_raise(table)
        rows = self._table_rows.get(table, [])
        return InMemoryQuery(rows, schema)

    def execute(self, sql, params=None, fetch=False):
        raise NotImplementedError(
            "Raw SQL execution is not supported by JSONFileDatabase. "
            "Use query() for in-memory querying instead."
        )

    def count(self, table, **filters):
        q = self.query(table)
        if filters:
            q = q.filter(**filters)
        return q.count()

    

    def write(self, key, value, commit=None):
        self._kv_data[key] = value
        if commit or (commit is None and self.auto_commit):
            self._save_to_file()
        return True

    def read(self, key, default=None):
        return self._kv_data.get(key, default)

    def delete_key(self, key, commit=None):
        self._kv_data.pop(key, None)
        if commit or (commit is None and self.auto_commit):
            self._save_to_file()
        return True

    def keys(self, pattern=None):
        if pattern:
            return [k for k in self._kv_data.keys() if pattern in k]
        return list(self._kv_data.keys())

    def exists(self, key):
        return key in self._kv_data

    def get_size(self):
        return len(self._kv_data)

    def delete_database(self, commit=None):
        self._kv_data.clear()
        self._tables.clear()
        self._schemas.clear()
        self._table_rows.clear()
        if commit or (commit is None and self.auto_commit):
            self._save_to_file()
        return True

    

    def close(self):
        if self.auto_commit:
            self._save_to_file()

    def remove_database(self):
        try:
            self.close()
            if os.path.exists(self.name):
                os.remove(self.name)
            return True
        except OSError as e:
            raise DatabaseError(f"Failed to remove database file: {e}")

    def _get_schema_or_raise(self, table_name):
        if table_name in self._tables:
            return self._tables[table_name]
        raise DatabaseError(f"Table '{table_name}' does not exist")

    def __repr__(self):
        return f"JSONFileDatabase(name={self.name!r})"
