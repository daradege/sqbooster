SimpleClient Backend Switch
===========================

The same application logic runs against SQLite, JSON, and Pickle backends.
Switching databases requires changing only the constructor call.

Full Source
-----------

.. literalinclude:: ../../examples/simple_backend_switch.py
   :language: python
   :linenos:

What It Demonstrates
--------------------

- **One-line backend switch** - same ``SimpleClient`` API everywhere
- **Top-level functions**: ``sqbooster.sqlite()``, ``sqbooster.json()``, etc.
- **Auto-created tables** work identically across all backends
- **Context manager** for automatic resource cleanup

Running the Example
-------------------

.. code-block:: bash

   python examples/simple_backend_switch.py
