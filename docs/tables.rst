Tables
======

Creating Tables
---------------

Define tables with typed columns:

.. code-block:: python

   from sqbooster.backends import SQLiteBackend
   from sqbooster.schema import Column
   from sqbooster.types import Integer, Text, Float, Boolean, JSON, Blob

   db = SQLiteBackend("app.db")

   db.create_table("users", [
       Column("id", Integer(), primary_key=True, autoincrement=True),
       Column("name", Text(), nullable=False),
       Column("age", Integer()),
       Column("email", Text(), unique=True),
       Column("balance", Float(), default=0.0),
       Column("active", Boolean(), default=True),
       Column("metadata", JSON()),
       Column("avatar", Blob()),
   ])

Column Types
------------

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Type
     - Python Type
     - SQL Type
   * - ``Integer()``
     - ``int``
     - ``INTEGER``
   * - ``Text()``
     - ``str``
     - ``TEXT``
   * - ``Float()``
     - ``float``
     - ``REAL``
   * - ``Boolean()``
     - ``bool``
     - ``INTEGER`` (0/1)
   * - ``Blob()``
     - ``bytes`` / any (auto-pickled)
     - ``BLOB``
   * - ``JSON()``
     - ``dict`` / ``list``
     - ``TEXT`` (JSON string)
   * - ``Pickle()``
     - any Python object
     - ``BLOB``
   * - ``Timestamp()``
     - ``str``
     - ``TIMESTAMP``
   * - ``VARCHAR(max_length)``
     - ``str``
     - ``VARCHAR(n)``

Column Constraints
------------------

.. code-block:: python

   Column("id", Integer(), primary_key=True, autoincrement=True)
   Column("name", Text(), nullable=False)
   Column("email", Text(), unique=True)
   Column("status", Text(), default="active")
   Column("score", Float(), nullable=True)

Inserting Data
--------------

Single row:

.. code-block:: python

   db.insert("users", {
       "name": "Alice",
       "age": 30,
       "email": "alice@example.com",
   })

Multiple rows at once:

.. code-block:: python

   db.insert_many("users", [
       {"name": "Bob", "age": 25, "email": "bob@example.com"},
       {"name": "Charlie", "age": 35, "email": "charlie@example.com"},
   ])

Auto-increment primary keys are generated automatically:

.. code-block:: python

   # id is auto-generated
   db.insert("users", {"name": "Diana", "email": "diana@example.com"})

Updating Data
-------------

.. code-block:: python

   # Update all users older than 60
   db.update("users", {"active": False}, age__gte=60)

   # Update a specific user
   db.update("users", {"age": 31}, name="Alice")

Deleting Data
-------------

.. code-block:: python

   # Delete by filter
   db.delete("users", name="Bob")

   # Delete all rows
   db.delete("users")

Table Management
----------------

.. code-block:: python

   # List all tables
   db.get_tables()  # ['users', 'posts']

   # Check if table exists
   db.table_exists("users")  # True

   # Get schema for a table
   schema = db.get_schema("users")

   # Drop a table
   db.drop_table("old_table")

   # Drop only if exists
   db.drop_table("old_table", if_exists=True)

Raw SQL (SQLite/PostgreSQL only)
---------------------------------

.. code-block:: python

   # Execute raw SQL
   results = db.execute(
       "SELECT name, age FROM users WHERE age > ?",
       params=[25],
       fetch=True,
   )
