SimpleClient
============

The ``SimpleClient`` is a high-level wrapper that makes sqbooster easy to use.

Quick Start
-----------

.. code-block:: python

    import sqbooster

    # One line to get started
    db = sqbooster.sqlite()

    # Tables are created automatically from the data you insert
    db.add("users", {"name": "Alice", "email": "alice@test.com", "age": 30})
    db.add("users", [
        {"name": "Bob", "email": "bob@test.com", "age": 25},
        {"name": "Charlie", "email": "charlie@test.com", "age": 35},
    ])

    # Query
    user = db.get("users", name="Alice")
    adults = db.find("users", age__gte=18, order_by="name")

    # Update and delete
    db.update("users", {"age": 31}, name="Alice")
    db.remove("users", name="Bob")

Convenience Constructors
------------------------

Top-level functions for quick access:

.. code-block:: python

    import sqbooster

    db = sqbooster.sqlite(":memory:")
    db = sqbooster.json("data.json")
    db = sqbooster.pickle("data.pkl")
    db = sqbooster.postgresql(host="localhost", name="mydb")
    db = sqbooster.redis(host="localhost")
    db = sqbooster.mongo(uri="mongodb://localhost:27017")

Or use ``SimpleClient`` directly:

.. code-block:: python

    from sqbooster.simple import SimpleClient
    from sqbooster.backends import SQLiteBackend

    client = SimpleClient(SQLiteBackend(":memory:"))
    client = SimpleClient.sqlite(":memory:")

Type Mapping
------------

When using dicts or ``(name, type)`` tuples, Python types map to sqbooster column types:

.. list-table::
   :header-rows: 1

   * - Python type
     - sqbooster type
     - Constraints
   * - ``str``
     - ``Text``
     - NOT NULL
   * - ``int``
     - ``Integer``
     - --
   * - ``float``
     - ``Float``
     - --
   * - ``bool``
     - ``Boolean``
     - default ``True``
   * - ``bytes``
     - ``Blob``
     - --
   * - ``dict`` / ``list``
     - ``JSON``
     - --

For full control, pass ``Column`` objects instead of tuples.

Full API
--------

See :doc:`api/simple` for the complete class reference.
