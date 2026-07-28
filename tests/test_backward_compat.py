"""
Backward compatibility tests for the legacy API.
"""

import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqbooster.backends import DatabaseBackend
from sqbooster.databases import (
    SQLiteDatabase, JSONFileDatabase, PickleFileDatabase
)

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

    print("--- SQLite ---")
    db = SQLiteDatabase(":memory:")
    check("SQLiteDatabase is DatabaseBackend", isinstance(db, DatabaseBackend))

    db.write("greeting", "hello world")
    check("write", db.read("greeting") == "hello world")
    check("exists", db.exists("greeting"))
    check("keys", db.keys() == ["greeting"])

    db.write("num", 42)
    check("read int", db.read("num") == 42)

    db.write("nested", {"a": [1, 2, 3]})
    check("read dict", db.read("nested") == {"a": [1, 2, 3]})

    db.delete_key("greeting")
    check("delete", not db.exists("greeting"))

    db.write("x", 1)
    db.write("y", 2)
    check("count", len(db.keys()) == 4)

    db.clear()
    check("clear", len(db.keys()) == 0)

    from sqbooster.schema import Column
    from sqbooster.types import Integer, Text
    db.create_table("items", [
        Column("id", Integer(), primary_key=True),
        Column("name", Text()),
    ])
    db.insert("items", {"id": 1, "name": "Widget"})
    row = db.query("items").filter(name="Widget").one()
    check("table API", row["name"] == "Widget")

    db.close()

    print("\n--- JSONFile ---")
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    jdb = JSONFileDatabase(tmp.name)
    check("JSONFileDatabase is DatabaseBackend", isinstance(jdb, DatabaseBackend))

    jdb.write("key1", {"hello": "world"})
    check("json write", jdb.read("key1") == {"hello": "world"})
    check("json exists", jdb.exists("key1"))

    jdb.delete_key("key1")
    check("json delete", not jdb.exists("key1"))

    jdb.create_table("logs", [
        Column("id", Integer(), primary_key=True),
        Column("message", Text()),
    ])
    jdb.insert("logs", {"id": 1, "message": "test"})
    check("json table", jdb.query("logs").one()["message"] == "test")

    jdb.close()
    os.unlink(tmp.name)

    print("\n--- PickleFile ---")
    tmp = tempfile.NamedTemporaryFile(suffix=".pkl", delete=False)
    tmp.close()
    pdb = PickleFileDatabase(tmp.name)
    check("PickleFileDatabase is DatabaseBackend", isinstance(pdb, DatabaseBackend))

    obj = [1, 2, {"nested": True}]
    pdb.write("complex", obj)
    check("pickle write", pdb.read("complex") == obj)

    pdb.delete_key("complex")
    check("pickle delete", not pdb.exists("complex"))

    pdb.close()
    os.unlink(tmp.name)

    print(f"\n{'='*40}")
    print(f"Results: {PASS} passed, {FAIL} failed")
    return FAIL == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
