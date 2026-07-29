Getting Started
===============

Installation
------------

Install sqbooster from PyPI:

.. code-block:: bash

   pip install sqbooster

Optional backends:

.. code-block:: bash

   pip install sqbooster[postgresql]   # PostgreSQL support
   pip install sqbooster[redis]        # Redis support
   pip install sqbooster[mongodb]      # MongoDB support
   pip install sqbooster[all]          # Everything

Quick Example
-------------

.. code-block:: python

   import sqbooster

   # Create a database
   db = sqbooster.sqlite("app.db")

   # Tables are created automatically from the data you insert
   db.add("users", {"name": "Alice", "age": 30, "email": "alice@example.com"})
   db.add("users", {"name": "Bob", "age": 25, "email": "bob@example.com"})

   # Query with filters
   adults = db.find("users", age__gte=28, order_by="name")
   # Returns: [{'id': 1, 'name': 'Alice', 'age': 30, ...}]

Concepts
--------

**Backends** are the database drivers. sqbooster supports:

- :class:`~sqbooster.backends.sqlite.SQLiteBackend` -- local file-based, zero config
- :class:`~sqbooster.backends.postgresql.PostgreSQLBackend` -- production SQL
- :class:`~sqbooster.databases.jsonfile.JSONFileDatabase` -- JSON file
- :class:`~sqbooster.databases.picklefile.PickleFileDatabase` -- pickle file
- :class:`~sqbooster.databases.redis.RedisDatabase` -- Redis server
- :class:`~sqbooster.databases.mongo.MongoDatabase` -- MongoDB server

**Columns** define table structure with typed columns:

.. code-block:: python

   from sqbooster.schema import Column
   from sqbooster.types import Integer, Text, Float, Boolean, Blob, JSON

**Queries** are chainable builders:

.. code-block:: python

   results = (db.query("users")
       .filter(age__gte=18, name__contains="a")
       .order_by("-age")
       .limit(10)
       .offset(0)
       .all())

Context Manager
---------------

All clients support the ``with`` statement:

.. code-block:: python

   import sqbooster

   with sqbooster.sqlite("app.db") as db:
       db.add("items", {"name": "Widget"})
   # Connection is automatically closed
