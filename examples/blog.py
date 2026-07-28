"""
Blog Engine Example - sqbooster

A complete blog engine with multiple related tables,
complex queries, pagination, and JSON metadata.
"""

import sqbooster
from sqbooster.schema import Column
from sqbooster.types import Integer, Text, JSON


def create_schema(db):
    db.create_table("posts", [
        Column("id", Integer(), primary_key=True, autoincrement=True),
        Column("title", Text(), nullable=False),
        Column("slug", Text(), unique=True, nullable=False),
        Column("body", Text()),
        Column("author", Text(), nullable=False),
        Column("status", Text(), default="draft"),
        Column("tags", JSON(), default=[]),
        Column("views", Integer(), default=0),
    ])

    db.create_table("comments", [
        Column("id", Integer(), primary_key=True, autoincrement=True),
        Column("post_id", Integer()),
        Column("author", Text(), nullable=False),
        Column("email", Text()),
        Column("body", Text(), nullable=False),
    ])


def seed_data(db):
    db.insert_many("posts", [
        {
            "title": "Getting Started with sqbooster",
            "slug": "getting-started-sqbooster",
            "body": "sqbooster makes database access easy...",
            "author": "Alice",
            "status": "published",
            "tags": ["python", "database", "tutorial"],
            "views": 150,
        },
        {
            "title": "Advanced Query Techniques",
            "slug": "advanced-query-techniques",
            "body": "Learn how to chain filters, sort, and paginate...",
            "author": "Bob",
            "status": "published",
            "tags": ["python", "advanced"],
            "views": 89,
        },
        {
            "title": "Draft: Future Features",
            "slug": "draft-future-features",
            "body": "Coming soon...",
            "author": "Alice",
            "status": "draft",
            "tags": ["roadmap"],
            "views": 0,
        },
    ])

    db.insert_many("comments", [
        {"post_id": 1, "author": "Charlie", "email": "c@test.com",
         "body": "Great tutorial!"},
        {"post_id": 1, "author": "Diana", "email": "d@test.com",
         "body": "Very helpful, thanks!"},
        {"post_id": 2, "author": "Eve", "email": "e@test.com",
         "body": "The filter chaining is really clean."},
    ])


def main():
    db = sqbooster.sqlite()

    print("=== Blog Engine Example ===\n")

    create_schema(db)
    seed_data(db)

    print("--- Published Posts ---")
    published = (db.query("posts")
        .filter(status="published")
        .order_by("-views")
        .all())
    for post in published:
        tags = ", ".join(post["tags"]) if post["tags"] else "none"
        print(f"  [{post['views']} views] {post['title']} ({tags})")

    print("\n--- Search: 'query' in title ---")
    results = db.query("posts").filter(title__contains="query").all()
    for post in results:
        print(f"  {post['title']} by {post['author']}")

    print("\n--- All Posts (page 1, limit 2) ---")
    page = db.query("posts").order_by("id").limit(2).all()
    for post in page:
        print(f"  #{post['id']}: {post['title']}")

    print(f"\nPublished: {db.query('posts').filter(status='published').count()}")
    print(f"Drafts: {db.query('posts').filter(status='draft').count()}")

    print("\n--- Comments for Post #1 ---")
    comments = db.query("comments").filter(post_id=1).all()
    for c in comments:
        print(f"  {c['author']}: {c['body']}")

    db.update("posts", {"views": 151}, slug="getting-started-sqbooster")
    updated = db.query("posts").filter(slug="getting-started-sqbooster").one()
    print(f"\nUpdated views: {updated['views']}")

    deleted = db.delete("posts", status="draft")
    print(f"\nDeleted {deleted} draft(s)")
    print(f"Remaining posts: {db.query('posts').count()}")

    post = db.query("posts").filter(slug="getting-started-sqbooster").one()
    new_tags = post["tags"] + ["beginner"]
    db.update("posts", {"tags": new_tags}, slug="getting-started-sqbooster")
    post = db.query("posts").filter(slug="getting-started-sqbooster").one()
    print(f"\nUpdated tags: {post['tags']}")

    db.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
