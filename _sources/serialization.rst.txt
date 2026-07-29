Serialization
=============

sqbooster supports two serialization modes for the key-value API and
configurable column types for table data.

Backend-level Serialization
---------------------------

When initializing a backend, choose between JSON and pickle:

.. code-block:: python

   # JSON (default) -- safe, portable, human-readable
   db = SQLiteBackend("app.db", serialization="json")

   # Pickle -- supports any Python object, not portable across versions
   db = SQLiteBackend("app.db", serialization="pickle")

This affects the key-value API:

.. code-block:: python

   # JSON mode: only JSON-serializable values
   db.write("config", {"theme": "dark"})       # OK
   db.write("set_data", {1, 2, 3})             # SerializationError!

   # Pickle mode: any Python object
   db.write("set_data", {1, 2, 3})             # OK
   db.write("anything", object())              # OK

Column-level Serialization
--------------------------

Use column types to control how table data is stored:

JSON Column
^^^^^^^^^^^

Stores Python dicts/lists as JSON text:

.. code-block:: python

   from sqbooster.types import JSON

   db.create_table("events", [
       Column("id", Integer(), primary_key=True),
       Column("data", JSON()),
   ])

   db.insert("events", {"data": {"action": "click", "x": 100, "y": 200}})
   event = db.query("events").one()
   print(type(event["data"]))  # <class 'dict'>

Blob Column (auto-pickle)
^^^^^^^^^^^^^^^^^^^^^^^^^

Stores raw bytes or auto-pickles any Python object:

.. code-block:: python

   from sqbooster.types import Blob

   db.create_table("cache", [
       Column("id", Integer(), primary_key=True),
       Column("data", Blob()),
   ])

   # Stored as pickled bytes, retrieved as the original object
   db.insert("cache", {"data": {1, 2, 3}})       # set
   db.insert("cache", {"data": [1, "two", 3.0]}) # list
   db.insert("cache", {"data": b"raw bytes"})    # bytes

Pickle Column
^^^^^^^^^^^^^

Explicit pickle storage:

.. code-block:: python

   from sqbooster.types import Pickle

   db.create_table("objects", [
       Column("id", Integer(), primary_key=True),
       Column("obj", Pickle()),
   ])

   db.insert("objects", {"obj": frozenset([1, 2, 3])})

Migration Tips
--------------

When moving between backends:

- **JSON to Pickle**: Change ``serialization="pickle"`` -- existing JSON data
  remains readable (JSON is a subset of what pickle supports).
- **SQLite to PostgreSQL**: Schema and queries are identical.
  Only the constructor changes.
- **Any to Redis/Mongo**: The table API works identically; key-value
  ``write()``/``read()`` use the backend's native format.
