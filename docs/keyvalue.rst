Key-Value API
=============

sqbooster maintains backward-compatible key-value operations alongside the
new table API. Every backend supports both.

Basic Operations
----------------

.. code-block:: python

   from sqbooster.backends import SQLiteBackend

   db = SQLiteBackend("kv.db")

   # Write
   db.write("user:1", {"name": "Alice", "role": "admin"})
   db.write("config:theme", "dark")
   db.write("counter:visits", 42)

   # Read
   user = db.read("user:1")               # {'name': 'Alice', 'role': 'admin'}
   theme = db.read("config:theme")         # 'dark'
   missing = db.read("config:missing", "default")  # 'default'

   # Check existence
   if db.exists("user:1"):
       print("User found")

   # Get all keys
   all_keys = db.keys()                    # ['user:1', 'config:theme', ...]
   user_keys = db.keys("user")             # ['user:1']

   # Delete
   db.delete_key("config:theme")

   # Count
   db.get_size()  # number of key-value pairs

   # Clear everything
   db.delete_database()

Auto-Commit
-----------

By default, each write operation is committed immediately. Disable for
batch operations:

.. code-block:: python

   db = SQLiteBackend("app.db", auto_commit=False)

   db.write("key1", "value1", commit=False)
   db.write("key2", "value2", commit=False)
   db.commit()  # Commit both at once

   # Or use auto_commit=False and commit manually
   db.write("key1", "value1")
   db.write("key2", "value2")
   db.commit()

Pickle Mode
-----------

Store any Python object:

.. code-block:: python

   db = SQLiteBackend("app.db", serialization="pickle")

   db.write("my_set", {1, 2, 3})
   db.write("my_counter", collections.Counter(a=3, b=1))
   data = db.read("my_set")
   print(type(data))  # <class 'set'>

File-based Backends
-------------------

For file-based backends, data persists to disk:

.. code-block:: python

   from sqbooster.databases import JSONFileDatabase, PickleFileDatabase

   # JSON file
   db = JSONFileDatabase("config.json")
   db.write("settings", {"debug": True})

   # Pickle file
   db = PickleFileDatabase("cache.pkl")
   db.write("computed_data", expensive_result)

   # Remove the file
   db.remove_database()

KV + Tables Together
--------------------

Both APIs coexist in the same database:

.. code-block:: python

   db = SQLiteBackend("app.db")

   # Table data
   db.create_table("users", [
       Column("id", Integer(), primary_key=True),
       Column("name", Text()),
   ])
   db.insert("users", {"name": "Alice"})

   # Key-value data (stored in internal _kv_store table)
   db.write("session:abc123", {"user_id": 1, "expires": "2025-12-31"})

   # Both work independently
   users = db.query("users").all()
   session = db.read("session:abc123")
