"""
Integration tests using real tables and typed columns.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqbooster.backends import SQLiteBackend
from sqbooster.schema import Column
from sqbooster.types import Integer, Text, Float, Boolean, JSON, Blob

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

    db = SQLiteBackend(":memory:")

    db.create_table("users", [
        Column("id", Integer(), primary_key=True, autoincrement=True),
        Column("name", Text(), nullable=False),
        Column("email", Text(), unique=True),
        Column("age", Integer()),
        Column("active", Boolean(), default=True),
        Column("balance", Float(), default=0.0),
    ])

    db.create_table("posts", [
        Column("id", Integer(), primary_key=True, autoincrement=True),
        Column("user_id", Integer()),
        Column("title", Text(), nullable=False),
        Column("body", Text()),
        Column("tags", JSON(), default=[]),
    ])

    db.create_table("blobs", [
        Column("id", Integer(), primary_key=True, autoincrement=True),
        Column("data", Blob()),
    ])

    tables = db.get_tables()
    check("get_tables", set(tables) == {"users", "posts", "blobs"})

    schema = db.get_schema("users")
    check("get_schema", any(c.name == "name" for c in schema.columns))

    db.insert("users", {"name": "Alice", "email": "a@test.com", "age": 30, "balance": 100.0})
    db.insert("users", {"name": "Bob", "email": "b@test.com", "age": 25, "balance": 50.0})
    db.insert("users", {"name": "Charlie", "email": "c@test.com", "age": 35, "balance": 200.0})
    db.insert("users", {"name": "Diana", "email": "d@test.com", "age": 28, "active": False})

    db.insert("posts", {"user_id": 1, "title": "First Post", "body": "Hello", "tags": ["intro"]})
    db.insert("posts", {"user_id": 1, "title": "Second Post", "body": "World", "tags": ["python"]})
    db.insert("posts", {"user_id": 2, "title": "Bob's Post", "body": "Hi", "tags": []})

    check("insert", db.query("users").count() == 4)

    db.insert_many("users", [
        {"name": "Eve", "email": "e@test.com", "age": 22},
        {"name": "Frank", "email": "f@test.com", "age": 40},
    ])
    check("insert_many", db.query("users").count() == 6)

    check("filter exact", db.query("users").filter(name="Alice").count() == 1)
    check("filter __gt", db.query("users").filter(age__gt=30).count() == 2)
    check("filter __gte", db.query("users").filter(age__gte=30).count() == 3)
    check("filter __lt", db.query("users").filter(age__lt=28).count() == 2)
    check("filter __lte", db.query("users").filter(age__lte=25).count() == 2)
    check("filter __ne", db.query("users").filter(name__ne="Alice").count() == 5)
    check("filter __contains", db.query("users").filter(name__contains="li").count() == 2)
    check("filter __startswith", db.query("users").filter(name__startswith="A").count() == 1)
    check("filter __endswith", db.query("users").filter(name__endswith="e").count() == 3)
    check("filter __in", db.query("users").filter(name__in=["Alice", "Bob"]).count() == 2)
    check("filter __notin", db.query("users").filter(name__notin=["Alice", "Bob"]).count() == 4)
    check("filter __isnull", db.query("users").filter(active__isnull=False).count() == 6)

    chained = db.query("users").filter(active=True, age__gt=25).all()
    check("chained filters", len(chained) == 3)

    asc = db.query("users").order_by("age").all()
    check("order_by asc", asc[0]["age"] <= asc[-1]["age"])

    desc = db.query("users").order_by("-age").all()
    check("order_by desc", desc[0]["age"] >= desc[-1]["age"])

    row = db.query("users").filter(name="Alice").select("name", "email").one()
    check("select", set(row.keys()) == {"name", "email"})

    limited = db.query("users").order_by("id").limit(2).all()
    check("limit", len(limited) == 2)

    offset = db.query("users").order_by("id").limit(2).offset(1).all()
    check("offset", len(offset) == 2 and offset[0]["name"] == "Bob")

    first = db.query("users").filter(name="Alice").first()
    check("first", first["name"] == "Alice")

    one = db.query("users").filter(name="Bob").one()
    check("one", one["name"] == "Bob")

    check("count", db.query("users").count() == 6)
    check("exists true", db.query("users").filter(name="Alice").exists())
    check("exists false", not db.query("users").filter(name="Zara").exists())

    db.update("users", {"balance": 999.0}, name="Alice")
    updated = db.query("users").filter(name="Alice").one()
    check("update", updated["balance"] == 999.0)

    deleted = db.delete("users", name="Frank")
    check("delete", deleted == 1 and db.query("users").count() == 5)

    post = db.query("posts").filter(title="First Post").one()
    check("JSON column", post["tags"] == ["intro"])

    import pickle
    obj = {"nested": [1, 2, 3]}
    db.insert("blobs", {"data": obj})
    blob = db.query("blobs").one()
    check("Blob column auto-pickle", blob["data"] == obj)

    raw = db.execute("SELECT name FROM users WHERE age > 30 ORDER BY name", fetch=True)
    check("raw SQL", raw == [{"name": "Charlie"}])

    db.drop_table("blobs")
    check("drop_table", "blobs" not in db.get_tables())

    with SQLiteBackend(":memory:") as ctx_db:
        ctx_db.create_table("t", [Column("id", Integer(), primary_key=True)])
        check("context manager", "t" in ctx_db.get_tables())

    pickledb = SQLiteBackend(":memory:", serialization="pickle")
    pickledb.write("cache:data", [1, 2, {"complex": True}])
    result = pickledb.read("cache:data")
    check("pickle serialization", result == [1, 2, {"complex": True}])
    pickledb.close()

    db.close()

    print(f"\n{'='*40}")
    print(f"Results: {PASS} passed, {FAIL} failed")
    return FAIL == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
