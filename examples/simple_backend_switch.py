"""
SimpleClient Backend Switch Example

The same code runs against SQLite, JSON, and Pickle backends.
Switching databases requires changing only one line.
"""

import tempfile
import os
import sqbooster


def run_app(db, label):
    print(f"\n--- {label} ---")

    db.add("users", [
        {"name": "Alice", "age": 30, "active": True},
        {"name": "Bob", "age": 25, "active": True},
        {"name": "Charlie", "age": 35, "active": False},
    ])

    adults = db.find("users", age__gte=18, order_by="name")
    print(f"  Adults: {[u['name'] for u in adults]}")

    active = db.find("users", active=True)
    print(f"  Active: {len(active)}")

    db.update("users", {"age": 31}, name="Alice")
    alice = db.get("users", name="Alice")
    print(f"  Alice's new age: {alice['age']}")

    db.remove("users", name="Charlie")
    print(f"  Remaining: {db.count('users')}")


def main():
    print("=== Backend Switch Example ===")

    with sqbooster.sqlite() as db:
        run_app(db, "SQLite")

    tmp_json = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp_json.close()
    with sqbooster.json(tmp_json.name) as db:
        run_app(db, "JSON File")
    os.unlink(tmp_json.name)

    tmp_pkl = tempfile.NamedTemporaryFile(suffix=".pkl", delete=False)
    tmp_pkl.close()
    with sqbooster.pickle(tmp_pkl.name) as db:
        run_app(db, "Pickle File")
    os.unlink(tmp_pkl.name)

    print("\nDone! All backends produce identical results.")


if __name__ == "__main__":
    main()
