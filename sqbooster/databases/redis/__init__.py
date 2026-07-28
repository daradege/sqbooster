"""
Redis database backend for sqbooster.

Stores key-value pairs and table data using Redis hashes and sets.
Supports the full DatabaseBackend interface with in-memory querying.
"""

import json
from typing import Any, Dict, List

from ...exceptions import DatabaseError, DatabaseConnectionError
from ...schema import Column, TableSchema
from ...query import InMemoryQuery
from ...types import Integer, Text, Float, Boolean, Blob, Timestamp
from ...backends import DatabaseBackend

try:
    import redis

    class RedisDatabase(DatabaseBackend):
        """A Redis database implementing the full DatabaseBackend interface.

        Key-value pairs are stored as regular Redis keys.
        Table data is stored in Redis hashes with JSON-serialized rows.

        Args:
            name: Redis database number or name.
            host: Redis server host.
            port: Redis server port.
            password: Redis server password.
            auto_commit: Whether to auto-commit (Redis is always committed).

        Example:
            db = RedisDatabase()
            db.create_table("sessions", [Column("id", Integer()), Column("user", Text())])
            db.insert("sessions", {"user": "ali"})
            results = db.query("sessions").filter(user="ali").all()
        """

        placeholder = ":ph"

        def __init__(self, name="db", host="localhost", port=6379,
                     password=None, auto_commit=True, serialization="json"):
            self.name = name
            self.auto_commit = auto_commit
            self.serialization = serialization
            self._prefix = "sqb"

            try:
                db_num = int(name) if name.isdigit() else 0
                self.conn = redis.Redis(
                    host=host, port=port, password=password,
                    decode_responses=True, db=db_num
                )
                self.conn.ping()
            except redis.RedisError as e:
                raise DatabaseConnectionError(f"Failed to connect to Redis: {e}")

        def _key(self, *parts):
            return ":".join([self._prefix] + list(parts))

        def _table_schema_key(self, table):
            return self._key("schema", table)

        def _table_ids_key(self, table):
            return self._key("ids", table)

        def _table_row_key(self, table, row_id):
            return self._key("row", table, str(row_id))

        

        def create_table(self, name, columns):
            if isinstance(columns, TableSchema):
                schema = columns
            else:
                schema = TableSchema(name, columns)

            import pickle as _pickle
            if self.serialization == "pickle":
                schema_data = _pickle.dumps(schema)
            else:
                schema_data = json.dumps({
                    "name": schema.name,
                    "columns": [
                        {
                            "name": c.name,
                            "type": type(c.col_type).__name__,
                            "primary_key": c.primary_key,
                            "nullable": c.nullable,
                            "unique": c.unique,
                            "default": c.default,
                            "autoincrement": c.autoincrement,
                        } for c in schema.columns
                    ]
                })

            self.conn.set(self._table_schema_key(name), schema_data)
            return True

        def drop_table(self, name, if_exists=True):
            if not self.table_exists(name):
                if not if_exists:
                    raise DatabaseError(f"Table '{name}' does not exist")
                return True

            row_ids = self.conn.smembers(self._table_ids_key(name))
            if row_ids:
                pipe = self.conn.pipeline()
                for rid in row_ids:
                    pipe.delete(self._table_row_key(name, rid))
                pipe.delete(self._table_ids_key(name))
                pipe.delete(self._table_schema_key(name))
                pipe.execute()
            else:
                self.conn.delete(self._table_ids_key(name))
                self.conn.delete(self._table_schema_key(name))
            return True

        def table_exists(self, name):
            return self.conn.exists(self._table_schema_key(name)) > 0

        def get_tables(self):
            pattern = self._key("schema", "*")
            keys = self.conn.keys(pattern)
            prefix = self._key("schema", "")
            return [k[len(prefix):] for k in keys]

        def get_schema(self, table_name):
            raw = self.conn.get(self._table_schema_key(table_name))
            if not raw:
                raise DatabaseError(f"Table '{table_name}' does not exist")

            import pickle as _pickle
            if self.serialization == "pickle":
                return _pickle.loads(raw)

            data = json.loads(raw)
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

        

        def insert(self, table, data):
            schema = self._get_schema_or_raise(table)
            validated = schema.validate_row(dict(data))

            pk_name = None
            if schema.primary_key:
                pk_name = schema.primary_key.name
                if schema.primary_key.autoincrement and (pk_name not in validated or validated[pk_name] is None):
                    current_ids = self.conn.smembers(self._table_ids_key(table))
                    max_id = 0
                    for rid in current_ids:
                        try:
                            max_id = max(max_id, int(rid))
                        except (ValueError, TypeError):
                            pass
                    validated[pk_name] = max_id + 1

            if pk_name and pk_name in validated:
                row_id = str(validated[pk_name])
            else:
                import uuid
                row_id = str(uuid.uuid4().int)[:12]

            row_json = json.dumps(validated, default=str)
            pipe = self.conn.pipeline()
            pipe.set(self._table_row_key(table, row_id), row_json)
            pipe.sadd(self._table_ids_key(table), row_id)
            pipe.execute()
            return True

        def insert_many(self, table, data_list):
            for data in data_list:
                self.insert(table, data)
            return True

        def update(self, table, data, **filters):
            schema = self._get_schema_or_raise(table)
            rows = self._load_all_rows(table)
            query = InMemoryQuery(rows, schema).filter(**filters)
            matching = query.all()

            count = 0
            pipe = self.conn.pipeline()
            for match in matching:
                for row in rows:
                    if all(row.get(k) == v for k, v in match.items() if k in row):
                        row.update(data)
                        row_id = str(row.get(schema.primary_key.name, "")) if schema.primary_key else None
                        if row_id:
                            pipe.set(self._table_row_key(table, row_id), json.dumps(row, default=str))
                            count += 1
                        break
            pipe.execute()
            return count

        def delete(self, table, **filters):
            schema = self._get_schema_or_raise(table)
            rows = self._load_all_rows(table)

            if not filters:
                count = len(rows)
                row_ids = self.conn.smembers(self._table_ids_key(table))
                if row_ids:
                    pipe = self.conn.pipeline()
                    for rid in row_ids:
                        pipe.delete(self._table_row_key(table, rid))
                    pipe.delete(self._table_ids_key(table))
                    pipe.execute()
                return count

            query = InMemoryQuery(rows, schema).filter(**filters)
            matching = query.all()

            pipe = self.conn.pipeline()
            deleted = 0
            for match in matching:
                for row in rows:
                    if all(row.get(k) == v for k, v in match.items() if k in row):
                        row_id = str(row.get(schema.primary_key.name, "")) if schema.primary_key else None
                        if row_id:
                            pipe.delete(self._table_row_key(table, row_id))
                            pipe.srem(self._table_ids_key(table), row_id)
                            deleted += 1
                        break
            pipe.execute()
            return deleted

        def query(self, table):
            schema = self._get_schema_or_raise(table)
            rows = self._load_all_rows(table)
            return InMemoryQuery(rows, schema)

        def execute(self, sql, params=None, fetch=False):
            raise NotImplementedError(
                "Raw SQL execution is not supported by RedisDatabase. "
                "Use query() for in-memory querying instead."
            )

        def count(self, table, **filters):
            q = self.query(table)
            if filters:
                q = q.filter(**filters)
            return q.count()

        def _load_all_rows(self, table):
            row_ids = self.conn.smembers(self._table_ids_key(table))
            rows = []
            for rid in row_ids:
                raw = self.conn.get(self._table_row_key(table, rid))
                if raw:
                    rows.append(json.loads(raw))
            return rows

        

        def write(self, key, value, commit=None):
            try:
                self.conn.set(key, json.dumps(value, default=str))
                return True
            except (TypeError, ValueError) as e:
                raise DatabaseError(f"Failed to serialize value: {e}")

        def read(self, key, default=None):
            try:
                result = self.conn.get(key)
                if result:
                    try:
                        return json.loads(result)
                    except json.JSONDecodeError:
                        return result
                return default
            except redis.RedisError as e:
                raise DatabaseError(f"Failed to read from Redis: {e}")

        def delete_key(self, key, commit=None):
            try:
                self.conn.delete(key)
                return True
            except redis.RedisError as e:
                raise DatabaseError(f"Failed to delete key: {e}")

        def keys(self, pattern=None):
            try:
                if pattern:
                    all_keys = self.conn.keys(f"*{pattern}*")
                else:
                    all_keys = self.conn.keys("*")
                kv_prefix = self._prefix + ":"
                return [k for k in all_keys if not k.startswith(kv_prefix)]
            except redis.RedisError as e:
                raise DatabaseError(f"Failed to fetch keys: {e}")

        def exists(self, key):
            try:
                return self.conn.exists(key) > 0
            except redis.RedisError as e:
                raise DatabaseError(f"Failed to check key existence: {e}")

        def get_size(self):
            try:
                all_keys = self.conn.keys("*")
                kv_prefix = self._prefix + ":"
                return len([k for k in all_keys if not k.startswith(kv_prefix)])
            except redis.RedisError as e:
                raise DatabaseError(f"Failed to get size: {e}")

        def delete_database(self, commit=None):
            try:
                self.conn.flushdb()
                return True
            except redis.RedisError as e:
                raise DatabaseError(f"Failed to delete database: {e}")

        

        def close(self):
            try:
                self.conn.close()
            except redis.RedisError as e:
                raise DatabaseConnectionError(f"Failed to close connection: {e}")

        def _get_schema_or_raise(self, table_name):
            if self.table_exists(table_name):
                return self.get_schema(table_name)
            raise DatabaseError(f"Table '{table_name}' does not exist")

        def __repr__(self):
            return f"RedisDatabase(name={self.name!r})"

except ImportError:
    class RedisDatabase:
        def __init__(self, *args, **kwargs):
            raise ImportError("Redis library not installed. Install with: pip install redis")
