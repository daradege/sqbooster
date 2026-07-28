Querying
========

The query builder provides a chainable, database-agnostic API for filtering,
sorting, and paginating results.

Basic Queries
-------------

.. code-block:: python

   # Get all rows
   all_users = db.query("users").all()

   # Get first row
   first = db.query("users").first()

   # Get exactly one row (raises ValueError if != 1)
   alice = db.query("users").filter(name="Alice").one()

   # Count rows
   total = db.query("users").count()

   # Check existence
   has_admins = db.query("users").filter(role="admin").exists()

Filter Operators
----------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Filter
     - Description
   * - ``field=value``
     - Exact match
   * - ``field__ne=value``
     - Not equal
   * - ``field__gt=value``
     - Greater than
   * - ``field__gte=value``
     - Greater than or equal
   * - ``field__lt=value``
     - Less than
   * - ``field__lte=value``
     - Less than or equal
   * - ``field__like=pattern``
     - SQL LIKE pattern (% and \_)
   * - ``field__contains=text``
     - Contains substring
   * - ``field__startswith=text``
     - Starts with
   * - ``field__endswith=text``
     - Ends with
   * - ``field__in=[list]``
     - Matches any in list
   * - ``field__notin=[list]``
     - Matches none in list
   * - ``field__isnull=True``
     - IS NULL
   * - ``field__isnull=False``
     - IS NOT NULL

Examples
--------

.. code-block:: python

   # Combine multiple filters
   results = db.query("users").filter(
       age__gte=18,
       age__lte=65,
       name__contains="a",
   ).all()

   # Range queries
   expensive = db.query("products").filter(price__gt=100).all()

   # IN queries
   specific = db.query("users").filter(name__in=["Alice", "Bob"]).all()

   # LIKE patterns
   emails = db.query("users").filter(email__endswith="@example.com").all()

   # Null checks
   unnamed = db.query("users").filter(name__isnull=True).all()

Ordering
--------

.. code-block:: python

   # Ascending (default)
   db.query("users").order_by("name").all()

   # Descending (prefix with -)
   db.query("users").order_by("-age").all()

   # Multiple sort keys
   db.query("users").order_by("department", "-salary").all()

Selecting Columns
-----------------

.. code-block:: python

   # Only return specific columns
   names_emails = db.query("users").select("name", "email").all()
   # Returns: [{'name': 'Alice', 'email': '...'}, ...]

Pagination
----------

.. code-block:: python

   # Limit results
   first_10 = db.query("users").limit(10).all()

   # Offset + limit (page 2, 10 per page)
   page_2 = db.query("users").offset(10).limit(10).all()

   # Count-based pagination
   total = db.query("users").count()
   page_size = 20
   for offset in range(0, total, page_size):
       page = db.query("users").offset(offset).limit(page_size).all()

Chaining
--------

.. code-block:: python

   results = (db.query("users")
       .filter(age__gte=18)
       .filter(role="active")
       .order_by("-created_at")
       .select("name", "email", "age")
       .offset(0)
       .limit(25)
       .all())
