"""
Tests for the SimpleClient high-level wrapper.
"""

import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqbooster.simple import SimpleClient
from sqbooster.backends.sqlite import SQLiteBackend
from sqbooster.schema import Column
from sqbooster.types import Integer, Text, Float

PASS = 0
FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}")


def run_tests():
    global PASS, FAIL
    PASS = 0
    FAIL = 0

    print("--- Construction ---")
    client = SimpleClient(SQLiteBackend(":memory:"))
    check("wrap backend", client is not None)
    check("backend property", isinstance(client.backend, SQLiteBackend))

    print("\n--- Define (Python types) ---")
    client.define("users", [
        ("name", str),
        ("email", str),
        ("age", int),
        ("balance", float),
        ("active", bool),
    ])
    check("define table", client.has("users"))
    check("tables list", "users" in client.tables())

    schema = client.backend.get_schema("users")
    name_col = schema.get_column("name")
    check("str -> NOT NULL", not name_col.nullable)
    active_col = schema.get_column("active")
    check("bool -> default True", active_col.default is True)

    print("\n--- Define (Column objects) ---")
    client.define("products", [
        Column("sku", Text(), unique=True, nullable=False),
        Column("price", Float()),
        Column("stock", Integer(), default=0),
    ])
    check("define with Column", client.has("products"))
    schema_p = client.backend.get_schema("products")
    check("auto id PK", schema_p.primary_key.name == "id")

    print("\n--- Add (single) ---")
    client.add("users", {"name": "Alice", "email": "alice@test.com", "age": 30, "balance": 100.0})
    check("add single", client.count("users") == 1)

    print("\n--- Add (bulk) ---")
    client.add("users", [
        {"name": "Bob", "email": "bob@test.com", "age": 25, "balance": 50.0},
        {"name": "Charlie", "email": "charlie@test.com", "age": 35, "balance": 200.0},
        {"name": "Diana", "email": "diana@test.com", "age": 28, "active": False},
    ])
    check("add bulk", client.count("users") == 4)

    print("\n--- Get ---")
    alice = client.get("users", name="Alice")
    check("get single", alice is not None and alice["name"] == "Alice")
    check("get not found", client.get("users", name="Zara") is None)

    print("\n--- Find ---")
    adults = client.find("users", age__gte=30)
    check("find filtered", len(adults) == 2)

    ordered = client.find("users", order_by="age")
    check("find ordered", ordered[0]["age"] <= ordered[-1]["age"])

    desc = client.find("users", order_by="-age")
    check("find ordered desc", desc[0]["age"] >= desc[-1]["age"])

    paged = client.find("users", order_by="name", limit=2, offset=1)
    check("find limit+offset", len(paged) == 2)

    print("\n--- Count ---")
    check("count all", client.count("users") == 4)
    check("count filtered", client.count("users", age__gt=30) == 1)

    print("\n--- Exists ---")
    check("exists true", client.exists("users", name="Alice"))
    check("exists false", not client.exists("users", name="Zara"))

    print("\n--- Update ---")
    updated = client.update("users", {"balance": 999.0}, name="Alice")
    check("update returns count", updated == 1)
    alice = client.get("users", name="Alice")
    check("update applied", alice["balance"] == 999.0)

    print("\n--- Remove ---")
    deleted = client.remove("users", name="Diana")
    check("remove returns count", deleted == 1)
    check("remove applied", client.count("users") == 3)

    print("\n--- Key-Value API ---")
    client.write("config:theme", {"dark": True})
    check("write", client.read("config:theme") == {"dark": True})
    check("read default", client.read("missing") is None)
    check("keys", "config:theme" in client.keys())
    client.delete_key("config:theme")
    check("delete_key", client.read("config:theme") is None)

    print("\n--- Table Management ---")
    client.drop("products")
    check("drop", not client.has("products"))

    print("\n--- Context Manager ---")
    with SimpleClient(SQLiteBackend(":memory:")) as c:
        c.define("tmp", [("x", int)])
        c.add("tmp", {"x": 42})
        check("context manager", c.get("tmp", x=42)["x"] == 42)

    print("\n--- Type Mapping ---")
    client2 = SimpleClient(SQLiteBackend(":memory:"))
    client2.define("misc", [
        ("data", bytes),
        ("info", dict),
    ])
    schema_m = client2.backend.get_schema("misc")
    check("bytes -> Blob", schema_m.get_column("data").col_type.__class__.__name__ == "Blob")
    check("dict -> JSON", schema_m.get_column("info").col_type.__class__.__name__ == "JSON")

    client2.close()

    print("\n--- Error Handling ---")
    try:
        SimpleClient("not_a_backend")
        check("type error", False)
    except TypeError:
        check("type error", True)

    try:
        client.define("bad", [("x", object)])
        check("bad type error", False)
    except TypeError:
        check("bad type error", True)

    client.close()

    print("\n--- Convenience Constructors ---")
    c = SimpleClient.sqlite(":memory:")
    c.define("t", [("v", int)])
    c.add("t", {"v": 1})
    check("SimpleClient.sqlite", c.get("t", v=1)["v"] == 1)
    c.close()

    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    c = SimpleClient.json(tmp.name)
    c.define("t", [("v", str)])
    c.add("t", {"v": "hello"})
    check("SimpleClient.json", c.get("t", v="hello")["v"] == "hello")
    c.close()
    os.unlink(tmp.name)

    tmp = tempfile.NamedTemporaryFile(suffix=".pkl", delete=False)
    tmp.close()
    c = SimpleClient.pickle(tmp.name)
    c.define("t", [("v", int)])
    c.add("t", {"v": 99})
    check("SimpleClient.pickle", c.get("t", v=99)["v"] == 99)
    c.close()
    os.unlink(tmp.name)

    print("\n--- Top-level Factories ---")
    import sqbooster
    db1 = sqbooster.sqlite()
    db1.define("t", [("v", int)])
    db1.add("t", {"v": 1})
    check("sqbooster.sqlite", db1.get("t", v=1)["v"] == 1)
    db1.close()

    db2 = sqbooster.sqlite(":memory:")
    db2.define("t", [("v", str)])
    db2.add("t", {"v": "hi"})
    check("sqbooster.sqlite with name", db2.get("t", v="hi")["v"] == "hi")
    db2.close()

    tmpf = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmpf.close()
    db3 = sqbooster.json(tmpf.name)
    db3.define("t", [("v", int)])
    db3.add("t", {"v": 7})
    check("sqbooster.json", db3.get("t", v=7)["v"] == 7)
    db3.close()
    os.unlink(tmpf.name)

    tmpf2 = tempfile.NamedTemporaryFile(suffix=".pkl", delete=False)
    tmpf2.close()
    db4 = sqbooster.pickle(tmpf2.name)
    db4.define("t", [("v", int)])
    db4.add("t", {"v": 9})
    check("sqbooster.pickle", db4.get("t", v=9)["v"] == 9)
    db4.close()
    os.unlink(tmpf2.name)

    print("\n--- Dict-Based Define ---")
    client3 = SimpleClient(SQLiteBackend(":memory:"))
    client3.define("products", {"name": str, "price": float, "stock": int})
    check("dict define", client3.has("products"))
    schema_d = client3.backend.get_schema("products")
    check("dict name NOT NULL", not schema_d.get_column("name").nullable)
    check("dict price is Float", schema_d.get_column("price").col_type.__class__.__name__ == "Float")
    check("dict stock is Integer", schema_d.get_column("stock").col_type.__class__.__name__ == "Integer")
    client3.add("products", {"name": "Widget", "price": 9.99, "stock": 100})
    check("dict add/get", client3.get("products", name="Widget")["price"] == 9.99)
    client3.close()

    print("\n--- Auto-Create Tables ---")
    client4 = SimpleClient(SQLiteBackend(":memory:"))
    client4.add("auto_table", {"name": "Alice", "age": 30, "active": True})
    check("auto-create single", client4.get("auto_table", name="Alice")["age"] == 30)
    client4.add("auto_bulk", [
        {"x": 1, "y": 2.5},
        {"x": 3, "y": 4.5},
    ])
    check("auto-create bulk", client4.count("auto_bulk") == 2)
    client4.add("auto_table", {"name": "Bob", "age": 25, "active": False})
    check("auto-add to existing", client4.count("auto_table") == 2)
    client4.close()

    print(f"\n{'='*40}")
    print(f"Results: {PASS} passed, {FAIL} failed")
    return FAIL == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
