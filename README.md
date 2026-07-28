# sqbooster

[![PyPI version](https://badge.fury.io/py/sqbooster.svg)](https://badge.fury.io/py/sqbooster)
[![Python Version](https://img.shields.io/pypi/pyversions/sqbooster.svg)](https://pypi.org/project/sqbooster/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A flexible Python library for database access with real typed tables, a chainable query builder, and easy backend switching.

## Features

- **6 backends, same API** - SQLite, PostgreSQL, JSON files, Pickle files, Redis, MongoDB
- **Real typed tables** - `Integer`, `Text`, `Float`, `Boolean`, `Blob`, `JSON`, and more
- **Chainable query builder** - filter, order, select, paginate, chain
- **Django-style filter operators** - `__gt`, `__lt`, `__contains`, `__in`, `__like`, and more
- **Pickle serialization** - `serialization="pickle"` at the backend level
- **Key-value API** - the v1 key-value interface still works for simple use cases
- **Zero config** - SQLite in-memory is the default

## Installation

```bash
pip install sqbooster

# Optional backends
pip install sqbooster[postgresql]   # PostgreSQL support
pip install sqbooster[redis]        # Redis support
pip install sqbooster[mongodb]      # MongoDB support
pip install sqbooster[all]          # Everything
```

## Quick Start

```python
import sqbooster

# One line to get a database
db = sqbooster.sqlite()

# Tables are created automatically from the data you insert
db.add("users", {"name": "Alice", "email": "alice@example.com", "age": 30})
db.add("users", {"name": "Bob", "email": "bob@example.com", "age": 25})

# Query with filter operators
active_users = db.find("users", age__gte=18, order_by="name")

# Chained filters
rich_active = db.find("users", age__gte=18, order_by="-age", limit=10)

# Get a single row
alice = db.get("users", name="Alice")

# Update and delete
db.update("users", {"age": 31}, name="Alice")
db.remove("users", name="Bob")
```

## Switching Backends

Switch between backends by changing only the constructor:

```python
import sqbooster

# SQLite
db = sqbooster.sqlite("myapp.db")

# JSON file
db = sqbooster.json("data.json")

# PostgreSQL (requires sqbooster[postgresql])
db = sqbooster.postgresql(host="localhost", name="mydb", user="me")

# Everything else stays the same
db.add("users", {"name": "Alice", "age": 30})
db.find("users", age__gte=18)
```

## Explicit Table Definitions

When you need constraints like `unique`, `nullable=False`, or custom defaults:

```python
from sqbooster.schema import Column
from sqbooster.types import Integer, Text, Float, Boolean

db.create_table("products", [
    Column("id", Integer(), primary_key=True, autoincrement=True),
    Column("name", Text(), nullable=False),
    Column("sku", Text(), unique=True, nullable=False),
    Column("price", Float(), nullable=False),
    Column("stock", Integer(), default=0),
    Column("active", Boolean(), default=True),
])

db.insert("products", {"name": "Widget", "sku": "W-001", "price": 9.99})
```

## Query Builder

```python
results = (db.query("users")
    .filter(age__gte=18, name__contains="a")
    .order_by("-age")
    .limit(10)
    .offset(0)
    .all())

count = db.query("users").filter(active=True).count()
first = db.query("users").filter(name="Alice").first()
```

## Key-Value API

```python
db = sqbooster.sqlite()

db.write("config:theme", {"dark": True, "font_size": 14})
print(db.read("config:theme"))

for key in db.keys("config:"):
    print(key, db.read(key))
```

## Pickle Serialization

```python
db = sqbooster.sqlite(serialization="pickle")

db.write("cache:results", [1, 2, {"nested": True}])
data = db.read("cache:results")
```

## Documentation

Full documentation: **https://sqbooster.github.io/sqbooster/**

## API Reference

### SimpleClient Methods

| Method | Description |
|---|---|
| `add(table, data)` | Insert one or more rows (auto-creates table) |
| `get(table, **filters)` | Get a single row |
| `find(table, **filters)` | Find rows matching filters |
| `update(table, data, **filters)` | Update rows |
| `remove(table, **filters)` | Delete rows |
| `count(table, **filters)` | Count rows |
| `exists(table, **filters)` | Check if rows exist |
| `define(table, columns)` | Explicitly define a table |

### Filter Operators

| Operator | Meaning |
|---|---|
| `__gt` / `__lt` | Greater/less than |
| `__gte` / `__lte` | Greater/less than or equal |
| `__ne` | Not equal |
| `__contains` | LIKE `%value%` |
| `__startswith` | LIKE `value%` |
| `__endswith` | LIKE `%value` |
| `__like` | Raw LIKE pattern |
| `__in` | Value in list |
| `__notin` | Value not in list |
| `__isnull` | IS NULL / IS NOT NULL |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License - see [LICENSE](LICENSE).

## Author

Ali Safamanesh (daradege@proton.me)
