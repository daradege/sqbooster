"""
Backend Migration Example - sqbooster

Migrating data between SQLite and PostgreSQL with zero query changes.
"""

import sqbooster
from sqbooster.schema import Column
from sqbooster.types import Integer, Text, Float, Boolean


USERS_SCHEMA = [
    Column("id", Integer(), primary_key=True, autoincrement=True),
    Column("name", Text(), nullable=False),
    Column("email", Text(), unique=True, nullable=False),
    Column("age", Integer()),
    Column("active", Boolean(), default=True),
]

PRODUCTS_SCHEMA = [
    Column("id", Integer(), primary_key=True, autoincrement=True),
    Column("name", Text(), nullable=False),
    Column("price", Float(), nullable=False),
    Column("stock", Integer(), default=0),
]


def setup_database(db):
    db.create_table("users", USERS_SCHEMA)
    db.create_table("products", PRODUCTS_SCHEMA)


def seed_database(db):
    db.insert_many("users", [
        {"name": "Alice", "email": "alice@example.com", "age": 30},
        {"name": "Bob", "email": "bob@example.com", "age": 25},
        {"name": "Charlie", "email": "charlie@example.com", "age": 35},
    ])
    db.insert_many("products", [
        {"name": "Widget", "price": 9.99, "stock": 100},
        {"name": "Gadget", "price": 24.99, "stock": 50},
    ])


def migrate(source, target):
    for table_name in source.get_tables():
        print(f"  Migrating table: {table_name}")
        schema = source.get_schema(table_name)
        target.create_table(table_name, schema)

        rows = source.query(table_name).all()
        if rows:
            target.insert_many(table_name, rows)
            print(f"    -> {len(rows)} rows copied")


def verify(db, label):
    print(f"\n--- {label} ---")
    for table in db.get_tables():
        rows = db.query(table).all()
        print(f"  {table}: {len(rows)} rows")
        for row in rows:
            print(f"    {row}")


def main():
    print("=== Backend Migration Example ===\n")

    print("1. Creating SQLite database...")
    sqlite_db = sqbooster.sqlite()
    setup_database(sqlite_db)
    seed_database(sqlite_db)
    verify(sqlite_db, "SQLite (source)")

    print("\n2. Creating target database...")
    target_db = sqbooster.sqlite()

    print("\n3. Migrating data...")
    migrate(sqlite_db, target_db)

    verify(target_db, "Target (after migration)")

    print("\n4. Querying migrated data...")
    active_users = target_db.query("users").filter(active=True).order_by("name").all()
    print(f"  Active users: {[u['name'] for u in active_users]}")

    expensive = target_db.query("products").filter(price__gt=15).all()
    print(f"  Products > $15: {[p['name'] for p in expensive]}")

    sqlite_db.close()
    target_db.close()

    print("\n--- PostgreSQL Migration ---")
    print("To migrate to PostgreSQL, simply replace:")
    print("  target_db = sqbooster.sqlite()")
    print("  target_db = sqbooster.postgresql(host='...', name='...', user='...')")
    print("Everything else stays exactly the same!")

    print("\nDone!")


if __name__ == "__main__":
    main()
