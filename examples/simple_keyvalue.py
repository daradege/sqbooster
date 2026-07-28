"""
SimpleClient Key-Value Example

Combines the simple key-value API with auto-created tables.
"""

import sqbooster


def main():
    with sqbooster.sqlite() as db:

        print("=== Key-Value + Tables ===\n")

        db.write("app:name", "MyApp")
        db.write("app:version", "2.0.0")
        db.write("app:config", {"theme": "dark", "lang": "en"})

        print("--- Key-Value Store ---")
        print(f"  App name: {db.read('app:name')}")
        print(f"  Version: {db.read('app:version')}")
        print(f"  Config: {db.read('app:config')}")
        print(f"  All keys: {db.keys('app:')}")

        db.add("users", [
            {"name": "Alice", "email": "alice@app.com", "role": "admin"},
            {"name": "Bob", "email": "bob@app.com", "role": "user"},
        ])

        db.add("logs", [
            {"level": "INFO", "message": "App started"},
            {"level": "ERROR", "message": "Connection failed"},
            {"level": "INFO", "message": "User logged in"},
        ])

        print("\n--- Structured Tables ---")
        admins = db.find("users", role="admin")
        print(f"  Admins: {[u['name'] for u in admins]}")

        errors = db.find("logs", level="ERROR")
        print(f"  Errors: {[l['message'] for l in errors]}")

        print(f"  Total logs: {db.count('logs')}")

        print("\n--- Combined Workflow ---")
        config = db.read("app:config")
        if config.get("theme") == "dark":
            db.add("logs", {"level": "INFO", "message": "Dark theme active"})

        db.update("users", {"role": "superadmin"}, name="Alice")
        alice = db.get("users", name="Alice")
        print(f"  Alice is now: {alice['role']}")

        db.delete_key("app:version")
        print(f"  Version after delete: {db.read('app:version')}")

        print(f"\n  Tables: {db.tables()}")
        print(f"  KV keys: {db.keys()}")

    print("\nDone!")


if __name__ == "__main__":
    main()
