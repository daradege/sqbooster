"""
MongoDB database backend for sqbooster.

Stores key-value pairs and table data in MongoDB collections.
Supports the full DatabaseBackend interface with native MongoDB querying.
"""

from typing import Any, Dict, List
from datetime import datetime

from ...exceptions import DatabaseError, DatabaseConnectionError
from ...schema import Column, TableSchema
from ...query import InMemoryQuery
from ...types import Integer, Text, Float, Boolean, Blob, Timestamp
from ...backends import DatabaseBackend

try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError

    class MongoDatabase(DatabaseBackend):
        """A MongoDB database implementing the full DatabaseBackend interface.

        Key-value pairs are stored in a '_kv_store' collection.
        Each table maps to a MongoDB collection.

        Args:
            name: Database name.
            host: MongoDB server host.
            port: MongoDB server port.
            collection: Default collection name for KV store.
            auto_commit: Whether to auto-commit.

        Example:
            db = MongoDatabase()
            db.create_table("users", [Column("id", Integer()), Column("name", Text())])
            db.insert("users", {"name": "Ali"})
            results = db.query("users").filter(name="Ali").all()
        """

        placeholder = ":ph"

        def __init__(self, name="testdb", host="localhost", port=27017,
                     collection="data", auto_commit=True, serialization="json"):
            self.name = name
            self.collection_name = collection
            self.auto_commit = auto_commit
            self.serialization = serialization

            try:
                self.client = MongoClient(host, port)
                self.db = self.client[name]
                self._kv_collection = self.db["_kv_store"]
                self._schema_collection = self.db["_schemas"]
            except PyMongoError as e:
                raise DatabaseConnectionError(f"Failed to connect to MongoDB: {e}")

        def _get_collection(self, table):
            return self.db[table]

        

        def create_table(self, name, columns):
            if isinstance(columns, TableSchema):
                schema = columns
            else:
                schema = TableSchema(name, columns)

            schema_doc = {
                "_id": name,
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
            }
            self._schema_collection.replace_one(
                {"_id": name}, schema_doc, upsert=True
            )

            self.db.command("collStats", name)
            return True

        def drop_table(self, name, if_exists=True):
            if not self.table_exists(name):
                if not if_exists:
                    raise DatabaseError(f"Table '{name}' does not exist")
                return True
            self._get_collection(name).drop()
            self._schema_collection.delete_one({"_id": name})
            return True

        def table_exists(self, name):
            collections = self.db.list_collection_names()
            return name in collections and name not in ("_kv_store", "_schemas")

        def get_tables(self):
            collections = self.db.list_collection_names()
            return [c for c in collections if c not in ("_kv_store", "_schemas")]

        def get_schema(self, table_name):
            doc = self._schema_collection.find_one({"_id": table_name})
            if not doc:
                raise DatabaseError(f"Table '{table_name}' does not exist")

            from ...types import Integer, Text, Float, Boolean, Blob, Timestamp, Real, VARCHAR, JSON as JSONType, Pickle
            type_map = {
                "Integer": Integer, "Text": Text, "Float": Float, "Real": Real,
                "Boolean": Boolean, "Blob": Blob, "Timestamp": Timestamp,
                "VARCHAR": VARCHAR, "JSON": JSONType, "Pickle": Pickle,
            }
            columns = []
            for col_data in doc["columns"]:
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
            return TableSchema(table_name, columns)

        

        def insert(self, table, data):
            schema = self._get_schema_or_raise(table)
            validated = schema.validate_row(dict(data))

            if schema.primary_key and schema.primary_key.autoincrement:
                pk_name = schema.primary_key.name
                if pk_name not in validated or validated[pk_name] is None:
                    collection = self._get_collection(table)
                    max_doc = collection.find_one(
                        sort=[(pk_name, -1)]
                    )
                    max_id = max_doc.get(pk_name, 0) if max_doc else 0
                    validated[pk_name] = max_id + 1

            try:
                self._get_collection(table).replace_one(
                    {"_sqb_id": validated.get(schema.primary_key.name)} if schema.primary_key
                    else {"_sqb_data_hash": str(sorted(validated.items()))},
                    {"_sqb_data": validated},
                    upsert=True
                )
                return True
            except PyMongoError as e:
                raise DatabaseError(f"Failed to insert into '{table}': {e}")

        def insert_many(self, table, data_list):
            if not data_list:
                return True
            schema = self._get_schema_or_raise(table)
            docs = []
            for data in data_list:
                validated = schema.validate_row(dict(data))
                docs.append({"_sqb_data": validated})
            try:
                self._get_collection(table).insert_many(docs)
                return True
            except PyMongoError as e:
                raise DatabaseError(f"Failed to bulk insert into '{table}': {e}")

        def update(self, table, data, **filters):
            schema = self._get_schema_or_raise(table)
            collection = self._get_collection(table)
            all_rows = [doc.get("_sqb_data", doc) for doc in collection.find({})]
            query = InMemoryQuery(all_rows, schema).filter(**filters)
            matching = query.all()

            count = 0
            for match in matching:
                filter_query = {f"_sqb_data.{k}": v for k, v in match.items()}
                update_data = {f"_sqb_data.{k}": v for k, v in data.items()}
                result = collection.update_one(filter_query, {"$set": update_data})
                count += result.modified_count
            return count

        def delete(self, table, **filters):
            schema = self._get_schema_or_raise(table)
            collection = self._get_collection(table)
            all_rows = [doc.get("_sqb_data", doc) for doc in collection.find({})]

            if not filters:
                result = collection.delete_many({})
                return result.deleted_count

            query = InMemoryQuery(all_rows, schema).filter(**filters)
            matching = query.all()

            count = 0
            for match in matching:
                filter_query = {f"_sqb_data.{k}": v for k, v in match.items()}
                result = collection.delete_one(filter_query)
                count += result.deleted_count
            return count

        def query(self, table):
            schema = self._get_schema_or_raise(table)
            collection = self._get_collection(table)
            rows = [doc.get("_sqb_data", doc) for doc in collection.find({})]
            return InMemoryQuery(rows, schema)

        def execute(self, sql, params=None, fetch=False):
            raise NotImplementedError(
                "Raw SQL execution is not supported by MongoDatabase. "
                "Use query() for in-memory querying instead."
            )

        def count(self, table, **filters):
            q = self.query(table)
            if filters:
                q = q.filter(**filters)
            return q.count()

        

        def write(self, key, value, commit=None):
            try:
                self._kv_collection.replace_one(
                    {"_id": key},
                    {"_id": key, "value": value, "created_at": datetime.now().isoformat()},
                    upsert=True
                )
                return True
            except PyMongoError as e:
                raise DatabaseError(f"Failed to write key '{key}': {e}")

        def read(self, key, default=None):
            try:
                result = self._kv_collection.find_one({"_id": key})
                return result["value"] if result else default
            except PyMongoError as e:
                raise DatabaseError(f"Failed to read key '{key}': {e}")

        def delete_key(self, key, commit=None):
            try:
                self._kv_collection.delete_one({"_id": key})
                return True
            except PyMongoError as e:
                raise DatabaseError(f"Failed to delete key '{key}': {e}")

        def keys(self, pattern=None):
            try:
                if pattern:
                    cursor = self._kv_collection.find(
                        {"_id": {"$regex": pattern}}, {"_id": 1}
                    )
                else:
                    cursor = self._kv_collection.find({}, {"_id": 1})
                return [doc["_id"] for doc in cursor]
            except PyMongoError as e:
                raise DatabaseError(f"Failed to fetch keys: {e}")

        def exists(self, key):
            try:
                return self._kv_collection.find_one({"_id": key}) is not None
            except PyMongoError as e:
                raise DatabaseError(f"Failed to check key existence: {e}")

        def get_size(self):
            try:
                return self._kv_collection.count_documents({})
            except PyMongoError as e:
                raise DatabaseError(f"Failed to get size: {e}")

        def delete_database(self, commit=None):
            try:
                self._kv_collection.delete_many({})
                for table in self.get_tables():
                    self._get_collection(table).drop()
                self._schema_collection.delete_many({})
                return True
            except PyMongoError as e:
                raise DatabaseError(f"Failed to delete database: {e}")

        

        def close(self):
            try:
                self.client.close()
            except PyMongoError as e:
                raise DatabaseConnectionError(f"Failed to close connection: {e}")

        def _get_schema_or_raise(self, table_name):
            try:
                return self.get_schema(table_name)
            except DatabaseError:
                raise DatabaseError(f"Table '{table_name}' does not exist")

        def __repr__(self):
            return f"MongoDatabase(name={self.name!r})"

except ImportError:
    class MongoDatabase:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyMongo library not installed. Install with: pip install pymongo")
