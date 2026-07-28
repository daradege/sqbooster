"""
SimpleClient Todo App

A minimal to-do application using auto-created tables.
"""

import sqbooster


def main():
    with sqbooster.sqlite() as db:

        print("=== Todo App ===\n")

        db.add("todos", [
            {"title": "Buy groceries", "done": False, "priority": 1},
            {"title": "Write docs", "done": False, "priority": 2},
            {"title": "Fix bug #42", "done": True, "priority": 3},
            {"title": "Review PR", "done": False, "priority": 2},
            {"title": "Deploy v2.0", "done": False, "priority": 3},
        ])

        print("--- Pending Tasks ---")
        pending = db.find("todos", done=False, order_by="-priority")
        for t in pending:
            print(f"  [P{t['priority']}] {t['title']}")

        db.update("todos", {"done": True}, title="Write docs")
        print("\nCompleted: Write docs")

        total = db.count("todos")
        done = db.count("todos", done=True)
        print(f"\nProgress: {done}/{total} done")

        bug = db.get("todos", title__contains="bug")
        if bug:
            print(f"Found bug task: {bug['title']} (priority={bug['priority']})")

        removed = db.remove("todos", done=True)
        print(f"\nCleaned up {removed} completed tasks")

        print("\n--- Remaining Tasks ---")
        for t in db.find("todos", order_by="-priority"):
            status = "done" if t["done"] else "todo"
            print(f"  [{status}] [P{t['priority']}] {t['title']}")

    print("\nDone!")


if __name__ == "__main__":
    main()
