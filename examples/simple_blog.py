"""
SimpleClient Blog Example

A blog engine using the SimpleClient wrapper with auto-created tables.
"""

import sqbooster


def main():
    with sqbooster.sqlite() as db:

        print("=== SimpleClient Blog ===\n")

        db.add("posts", [
            {"title": "Getting Started with sqbooster",
             "slug": "getting-started",
             "body": "sqbooster makes database access easy...",
             "author": "Alice", "status": "published", "views": 150},
            {"title": "Advanced Querying",
             "slug": "advanced-querying",
             "body": "Filters, ordering, pagination...",
             "author": "Bob", "status": "published", "views": 89},
            {"title": "Draft: Future Plans",
             "slug": "future-plans",
             "body": "Coming soon...",
             "author": "Alice", "status": "draft", "views": 0},
        ])

        db.add("comments", [
            {"post_id": 1, "author": "Charlie", "body": "Great tutorial!"},
            {"post_id": 1, "author": "Diana", "body": "Very helpful!"},
            {"post_id": 2, "author": "Eve", "body": "Clean API."},
        ])

        print("--- Published Posts ---")
        published = db.find("posts", status="published", order_by="-views")
        for post in published:
            print(f"  [{post['views']} views] {post['title']} by {post['author']}")

        print("\n--- Search: 'query' in title ---")
        for post in db.find("posts", title__contains="query"):
            print(f"  {post['title']}")

        print("\n--- Page 1 (limit 2) ---")
        for post in db.find("posts", order_by="title", limit=2):
            print(f"  {post['title']}")

        print(f"\nPublished: {db.count('posts', status='published')}")
        print(f"Drafts: {db.count('posts', status='draft')}")

        print("\n--- Comments for Post #1 ---")
        for c in db.find("comments", post_id=1):
            print(f"  {c['author']}: {c['body']}")

        db.update("posts", {"views": 151}, slug="getting-started")
        post = db.get("posts", slug="getting-started")
        print(f"\nUpdated views: {post['views']}")

        deleted = db.remove("posts", status="draft")
        print(f"Deleted {deleted} draft(s)")
        print(f"Remaining posts: {db.count('posts')}")

    print("\nDone!")


if __name__ == "__main__":
    main()
