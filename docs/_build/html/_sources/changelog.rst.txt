Changelog
=========

v2.0.0
------

**Major release** - Full database abstraction layer.

New features:

- ``DatabaseBackend`` ABC - all 6 backends implement the same interface
- Real typed tables with ``create_table()``, ``get_tables()``, ``get_schema()``
- Column types: ``Integer``, ``Text``, ``Float``, ``Boolean``, ``Blob``, ``Timestamp``, ``JSON``, ``Pickle``
- Chainable ``Query`` class with ``filter()``, ``order_by()``, ``select()``, ``limit()``, ``offset()``
- Django-style filter operators: ``__gt``, ``__gte``, ``__lt``, ``__lte``, ``__ne``, ``__contains``, ``__startswith``, ``__endswith``, ``__like``, ``__in``, ``__notin``, ``__isnull``
- ``first()``, ``one()``, ``count()``, ``exists()`` query methods
- Backend-level pickle serialization via ``serialization="pickle"``
- ``InMemoryQuery`` for non-SQL backends (JSON, Pickle, Redis, Mongo)
- ``Blob`` column type auto-pickles non-bytes values
- ``TableSchema`` with constraints, validation, and SQL generation
- Sphinx documentation with Furo theme

Backward compatibility:

- ``SQLiteDatabase``, ``JSONFileDatabase``, ``PickleFileDatabase`` still support the key-value API
- ``ConnectionError`` renamed to ``DatabaseConnectionError`` (alias kept)

v1.0.0
------

Initial release:

- Key-value store API (``write``, ``read``, ``delete``, ``exists``, ``clear``, ``keys``)
- SQLite, PostgreSQL, JSON file, Pickle file, Redis, MongoDB backends
- JSON serialization with binary fallback
