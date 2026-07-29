SimpleClient Key-Value + Tables
================================

Combines the simple key-value API with auto-created tables in one client.
Ideal for applications that need both structured data and fast key lookups.

Full Source
-----------

.. literalinclude:: ../../examples/simple_keyvalue.py
   :language: python
   :linenos:

What It Demonstrates
--------------------

- **Key-value store** for config, cache, and simple lookups
- **Auto-created tables** for structured data with queries
- **Using both in a single workflow** - read config from KV, write logs to a table
- **keys()** with pattern matching for namespaced lookups
- **delete_key()** for KV cleanup

Running the Example
-------------------

.. code-block:: bash

   python examples/simple_keyvalue.py
