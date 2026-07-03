"""SQLite-based resource tracking and management.

Provides full CRUD operations plus search/filter and input validation.
"""

import sqlite3
from contextlib import contextmanager

DEFAULT_DB = "resources.db"

VALID_STATUSES = {"available", "in_use", "depleted", "reserved"}


@contextmanager
def _connect(db_name=DEFAULT_DB):
    """Context manager that yields a connection and closes it afterwards."""
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
def create_database(db_name=DEFAULT_DB):
    """Create the resources table if it does not exist."""
    with _connect(db_name) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                quantity INTEGER DEFAULT 0,
                location TEXT,
                status TEXT DEFAULT 'available',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    return db_name


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
def _validate_name(name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string")


def _validate_quantity(quantity):
    if not isinstance(quantity, int) or quantity < 0:
        raise ValueError("quantity must be a non-negative integer")


def _validate_status(status):
    if status is not None and status not in VALID_STATUSES:
        raise ValueError(f"status must be one of {VALID_STATUSES}")


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------
def add_resource(name, category, quantity, location, db_name=DEFAULT_DB):
    """Add a new resource row and return its id."""
    _validate_name(name)
    _validate_quantity(quantity)
    with _connect(db_name) as conn:
        cursor = conn.execute(
            """
            INSERT INTO resources (name, category, quantity, location)
            VALUES (?, ?, ?, ?)
            """,
            (name, category, quantity, location),
        )
        return cursor.lastrowid


def view_resources(db_name=DEFAULT_DB):
    """Return all resource rows as a list of dicts."""
    with _connect(db_name) as conn:
        rows = conn.execute("SELECT * FROM resources ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def get_resource(resource_id, db_name=DEFAULT_DB):
    """Return a single resource dict by id, or None."""
    with _connect(db_name) as conn:
        row = conn.execute(
            "SELECT * FROM resources WHERE id = ?", (resource_id,)
        ).fetchone()
    return dict(row) if row else None


def update_resource(resource_id, db_name=DEFAULT_DB, **fields):
    """Update one or more fields of a resource.

    Accepted keyword args: name, category, quantity, location, status.
    Returns the number of rows updated (0 if id not found).
    """
    allowed = {"name", "category", "quantity", "location", "status"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        raise ValueError("No updatable fields provided")

    if "name" in updates:
        _validate_name(updates["name"])
    if "quantity" in updates:
        _validate_quantity(updates["quantity"])
    if "status" in updates:
        _validate_status(updates["status"])

    set_clause = ", ".join(f"{col} = ?" for col in updates)
    values = list(updates.values()) + [resource_id]

    with _connect(db_name) as conn:
        cursor = conn.execute(
            f"UPDATE resources SET {set_clause} WHERE id = ?", values
        )
        return cursor.rowcount


def delete_resource(resource_id, db_name=DEFAULT_DB):
    """Delete a resource by id.  Returns the number of rows deleted."""
    with _connect(db_name) as conn:
        cursor = conn.execute(
            "DELETE FROM resources WHERE id = ?", (resource_id,))
        return cursor.rowcount


# ---------------------------------------------------------------------------
# Search / filter
# ---------------------------------------------------------------------------
def search_resources(
    name=None, category=None, location=None, status=None, db_name=DEFAULT_DB
):
    """Search resources by any combination of filters (AND logic)."""
    clauses = []
    values = []
    if name is not None:
        clauses.append("name LIKE ?")
        values.append(f"%{name}%")
    if category is not None:
        clauses.append("category LIKE ?")
        values.append(f"%{category}%")
    if location is not None:
        clauses.append("location LIKE ?")
        values.append(f"%{location}%")
    if status is not None:
        _validate_status(status)
        clauses.append("status = ?")
        values.append(status)

    where = " AND ".join(clauses) if clauses else "1=1"
    with _connect(db_name) as conn:
        rows = conn.execute(
            f"SELECT * FROM resources WHERE {where} ORDER BY id", values
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    create_database()
    # add_resource("Water Filters", "Humanitarian", 500, "Warehouse A")
    # view_resources()
