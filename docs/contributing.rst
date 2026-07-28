Contributing
============

Thanks for your interest in contributing to sqbooster!

Development Setup
-----------------

.. code-block:: bash

   git clone https://github.com/daradege/sqbooster.git
   cd sqbooster
   pip install -e ".[dev]"

Running Tests
-------------

.. code-block:: bash

   python tests/test_real_tables.py
   python tests/test_backward_compat.py

Building Documentation
----------------------

.. code-block:: bash

   make docs
   open docs/_build/html/index.html

Project Structure
-----------------

.. code-block:: text

   sqbooster/
   ├── sqbooster/
   │   ├── types.py           # Column types
   │   ├── schema.py          # Column + TableSchema
   │   ├── query.py           # Query + InMemoryQuery
   │   ├── backends/          # DatabaseBackend ABC + SQL backends
   │   └── databases/         # JSON, Pickle, Redis, Mongo backends
   ├── docs/                  # Sphinx documentation
   ├── examples/              # Full example applications
   └── tests/                 # Test suite

Adding a New Backend
--------------------

1. Create ``sqbooster/databases/<name>/__init__.py``
2. Implement ``DatabaseBackend`` from ``sqbooster.backends``
3. Add optional dependency in ``pyproject.toml``
4. Update safe imports in ``sqbooster/databases/__init__.py``
5. Add tests in ``tests/``

Code Style
----------

- Type hints on all public methods
- Docstrings in Google style for Sphinx autodoc
- No unnecessary comments

License
-------

By contributing, you agree that your contributions will be licensed under the MIT License.
