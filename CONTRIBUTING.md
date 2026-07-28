# Contributing to sqbooster

Thanks for your interest in contributing to sqbooster!

## Development Setup

```bash
git clone https://github.com/daradege/sqbooster.git
cd sqbooster
pip install -e ".[dev]"
```

## Running Tests

```bash
python tests/test_real_tables.py
python tests/test_backward_compat.py
```

## Building Documentation

```bash
make docs
open docs/_build/html/index.html
```

## Project Structure

```
sqbooster/
├── sqbooster/
│   ├── __init__.py          # Package exports
│   ├── types.py             # Column types (Integer, Text, Float, Boolean, Blob, etc.)
│   ├── schema.py            # Column + TableSchema
│   ├── query.py             # Query (SQL) + InMemoryQuery (non-SQL)
│   ├── exceptions/          # Custom exceptions
│   ├── backends/
│   │   ├── __init__.py      # DatabaseBackend ABC
│   │   ├── sqlite.py        # SQLiteBackend
│   │   └── postgresql.py    # PostgreSQLBackend
│   └── databases/
│       ├── __init__.py      # Re-exports
│       ├── jsonfile/        # JSONFileDatabase
│       ├── picklefile/      # PickleFileDatabase
│       ├── redis/           # RedisDatabase
│       └── mongo/           # MongoDatabase
├── docs/                    # Sphinx documentation
├── examples/                # Full example applications
└── tests/                   # Test suite
```

## Adding a New Backend

1. Create a new directory under `sqbooster/databases/<name>/` with `__init__.py`
2. Implement the `DatabaseBackend` ABC from `sqbooster.backends`
3. Add optional dependency in `pyproject.toml` under `[project.optional-dependencies]`
4. Update safe imports in `sqbooster/databases/__init__.py` and `sqbooster/__init__.py`
5. Add tests in `tests/`

## Code Style

- Type hints on all public methods
- Docstrings in Google style for Sphinx autodoc
- No unnecessary comments — let the code speak

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
