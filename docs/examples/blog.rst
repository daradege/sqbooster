Blog Engine Example
===================

A complete blog engine using sqbooster with posts, tags, and comments.

Full Source
-----------

.. literalinclude:: ../../examples/blog.py
   :language: python
   :linenos:

What It Demonstrates
--------------------

- **Multiple related tables** with foreign-key-like references
- **Complex filtering** across columns
- **Pagination** for listing posts
- **Updating** and **deleting** records
- **JSON columns** for flexible metadata

Running the Example
-------------------

.. code-block:: bash

   python examples/blog.py
