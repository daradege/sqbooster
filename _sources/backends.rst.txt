Backends
========

All backends implement the :class:`~sqbooster.backends.DatabaseBackend` interface,
so you can switch between them by changing only the constructor call.

SQLite (zero config)
---------------------

.. code-block:: python

   from sqbooster.backends import SQLiteBackend

   # In-memory database
   db = SQLiteBackend()

   # File-based database
   db = SQLiteBackend("app.db")

   # With pickle serialization
   db = SQLiteBackend("app.db", serialization="pickle")

PostgreSQL
----------

Requires ``psycopg2-binary``:

.. code-block:: bash

   pip install sqbooster[postgresql]

.. code-block:: python

   from sqbooster.backends import PostgreSQLBackend

   db = PostgreSQLBackend(
       host="localhost",
       port=5432,
       name="mydb",
       user="postgres",
       password="secret",
   )

JSON File
---------

.. code-block:: python

   from sqbooster.databases import JSONFileDatabase

   db = JSONFileDatabase("data.json")
   db.create_table("users", [Column("id", Integer()), Column("name", Text())])
   db.insert("users", {"name": "Alice"})

Pickle File
-----------

Stores any Python object (not just JSON-serializable):

.. code-block:: python

   from sqbooster.databases import PickleFileDatabase

   db = PickleFileDatabase("cache.pkl")
   db.write("complex_obj", {frozenset([1, 2]): [3, 4]})

Redis
-----

Requires ``redis``:

.. code-block:: bash

   pip install sqbooster[redis]

.. code-block:: python

   from sqbooster.databases import RedisDatabase

   db = RedisDatabase(host="localhost", port=6379)
   db.create_table("sessions", [
       Column("id", Integer()),
       Column("user_id", Integer()),
       Column("token", Text()),
   ])

MongoDB
-------

Requires ``pymongo``:

.. code-block:: bash

   pip install sqbooster[mongodb]

.. code-block:: python

   from sqbooster.databases import MongoDatabase

   db = MongoDatabase(host="localhost", name="myapp")
   db.create_table("products", [
       Column("name", Text()),
       Column("price", Float()),
   ])

Backend Comparison
------------------

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 15 15 15 15

   * - Feature
     - SQLite
     - PostgreSQL
     - JSON
     - Pickle
     - Redis
     - MongoDB
   * - Zero config
     - Yes
     - No
     - Yes
     - Yes
     - No
     - No
   * - File-based
     - Yes
     - No
     - Yes
     - Yes
     - No
     - No
   * - Raw SQL
     - Yes
     - Yes
     - No
     - No
     - No
     - No
   * - In-memory
     - Yes
     - No
     - Yes
     - Yes
     - No
     - No
   * - Complex objects
     - Pickle col
     - Pickle col
     - Yes
     - Yes
     - Limited
     - Yes
   * - Concurrency
     - Limited
     - Excellent
     - None
     - None
     - Excellent
     - Excellent

Switching Backends
------------------

All backends share the same interface. To migrate:

.. code-block:: python

   # Before: SQLite
   db = SQLiteBackend("local.db")

   # After: PostgreSQL (same API, same queries)
   db = PostgreSQLBackend(host="prod-db", name="app", user="admin", password="x")

   # Everything else stays exactly the same:
   db.create_table("users", [Column("id", Integer()), ...])
   results = db.query("users").filter(active=True).all()

Context Manager
---------------

All backends support ``with`` for automatic cleanup:

.. code-block:: python

   with SQLiteBackend("app.db") as db:
       db.create_table("items", [Column("id", Integer())])
       # Connection auto-closes on exit
