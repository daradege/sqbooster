"""
Inventory System Example - sqbooster

A product inventory with categories, stock tracking, and search.
Uses auto-created tables for simple data, explicit schemas for constraints.
"""

import sqbooster
from sqbooster.schema import Column
from sqbooster.types import Integer, Text, Float, Boolean


def create_schema(db):
    db.create_table("categories", [
        Column("id", Integer(), primary_key=True, autoincrement=True),
        Column("name", Text(), unique=True, nullable=False),
    ])

    db.create_table("products", [
        Column("id", Integer(), primary_key=True, autoincrement=True),
        Column("name", Text(), nullable=False),
        Column("sku", Text(), unique=True, nullable=False),
        Column("price", Float(), nullable=False),
        Column("stock", Integer(), default=0),
        Column("category_id", Integer()),
        Column("active", Boolean(), default=True),
    ])


def seed_data(db):
    db.insert_many("categories", [
        {"name": "Electronics"},
        {"name": "Books"},
        {"name": "Clothing"},
    ])

    db.insert_many("products", [
        {"name": "Laptop", "sku": "ELEC-001", "price": 999.99, "stock": 15, "category_id": 1},
        {"name": "Mouse", "sku": "ELEC-002", "price": 29.99, "stock": 200, "category_id": 1},
        {"name": "Keyboard", "sku": "ELEC-003", "price": 79.99, "stock": 50, "category_id": 1},
        {"name": "Python Cookbook", "sku": "BOOK-001", "price": 45.00, "stock": 30, "category_id": 2},
        {"name": "Clean Code", "sku": "BOOK-002", "price": 35.00, "stock": 25, "category_id": 2},
        {"name": "T-Shirt", "sku": "CLO-001", "price": 19.99, "stock": 100, "category_id": 3},
    ])


def main():
    db = sqbooster.sqlite()

    print("=== Inventory System Example ===\n")

    create_schema(db)
    seed_data(db)

    print("--- All Products ---")
    for p in db.query("products").order_by("name").all():
        print(f"  {p['sku']:12s}  {p['name']:15s}  ${p['price']:>8.2f}  stock={p['stock']}")

    print("\n--- Electronics Under $100 ---")
    cheap = db.query("products").filter(
        category_id=1,
        price__lt=100.0,
    ).order_by("price").all()
    for p in cheap:
        print(f"  {p['name']:15s}  ${p['price']:.2f}")

    print("\n--- Low Stock (< 30 units) ---")
    low = db.query("products").filter(stock__lt=30).all()
    for p in low:
        print(f"  {p['name']:15s}  stock={p['stock']}")

    print("\n--- Search: 'book' in name ---")
    books = db.query("products").filter(name__contains="ook").all()
    for p in books:
        print(f"  {p['name']}")

    print("\n--- Products $20 - $50 ---")
    mid = db.query("products").filter(
        price__gte=20, price__lte=50
    ).all()
    for p in mid:
        print(f"  {p['name']:15s}  ${p['price']:.2f}")

    all_products = db.query("products").all()
    total_value = sum(p["price"] * p["stock"] for p in all_products)
    print(f"\n--- Total Inventory Value: ${total_value:,.2f} ---")

    db.update("products", {"stock": 14}, sku="ELEC-001")
    laptop = db.query("products").filter(sku="ELEC-001").one()
    print(f"\nLaptop stock after sale: {laptop['stock']}")

    db.update("products", {"active": False}, stock=0)
    active_count = db.query("products").filter(active=True).count()
    print(f"Active products: {active_count}")

    db.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
