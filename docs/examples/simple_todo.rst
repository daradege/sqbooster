SimpleClient Todo App
=====================

A minimal to-do application using auto-created tables.

Full Source
-----------

.. literalinclude:: ../../examples/simple_todo.py
   :language: python
   :linenos:

What It Demonstrates
--------------------

- **Auto-created tables** from the data you insert
- **Top-level factory** - ``sqbooster.sqlite()``
- **Filter operators** like ``__contains`` for partial matching
- **Ordering** with ``-priority`` for descending sort
- **Update** specific rows by filter
- **Count** with and without filters
- **Remove** rows matching a condition

Running the Example
-------------------

.. code-block:: bash

   python examples/simple_todo.py
