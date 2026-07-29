SimpleClient Blog
=================

Same blog engine as the low-level ``blog.py`` example, but rewritten
using the ``SimpleClient`` wrapper with auto-created tables.

Full Source
-----------

.. literalinclude:: ../../examples/simple_blog.py
   :language: python
   :linenos:

What It Demonstrates
--------------------

- **Auto-created tables** - no ``define()`` needed, tables created from the data
- **Top-level factory** - ``sqbooster.sqlite()`` with no backend imports
- **Bulk insert** with a single ``add()`` call
- **Find with filters, ordering, and pagination** in one line
- **Count, get, update, remove** - all as simple method calls
- **Context manager** for automatic cleanup

Running the Example
-------------------

.. code-block:: bash

   python examples/simple_blog.py
