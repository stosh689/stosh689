"""Tests for scripts/resource_manager.py."""

import pytest

from scripts import resource_manager as rm


def test_create_database(tmp_db):
    result = rm.create_database(tmp_db)
    assert result == tmp_db
    # table should exist
    rows = rm.view_resources(tmp_db)
    assert rows == []


def test_add_and_view_resource(tmp_db):
    rm.create_database(tmp_db)
    rid = rm.add_resource("Water Filters", "Humanitarian",
                          500, "Warehouse A", tmp_db)
    assert isinstance(rid, int)
    rows = rm.view_resources(tmp_db)
    assert len(rows) == 1
    assert rows[0]["name"] == "Water Filters"
    assert rows[0]["quantity"] == 500


def test_get_resource(tmp_db):
    rm.create_database(tmp_db)
    rid = rm.add_resource("Tents", "Shelter", 10, "Warehouse B", tmp_db)
    row = rm.get_resource(rid, tmp_db)
    assert row["name"] == "Tents"
    assert rm.get_resource(9999, tmp_db) is None


def test_update_resource(tmp_db):
    rm.create_database(tmp_db)
    rid = rm.add_resource("Blankets", "Shelter", 100, "Warehouse A", tmp_db)
    count = rm.update_resource(rid, tmp_db, quantity=200, status="in_use")
    assert count == 1
    row = rm.get_resource(rid, tmp_db)
    assert row["quantity"] == 200
    assert row["status"] == "in_use"


def test_update_resource_not_found(tmp_db):
    rm.create_database(tmp_db)
    count = rm.update_resource(9999, tmp_db, quantity=5)
    assert count == 0


def test_update_resource_no_fields(tmp_db):
    rm.create_database(tmp_db)
    rid = rm.add_resource("X", "Y", 1, "Z", tmp_db)
    with pytest.raises(ValueError, match="No updatable fields"):
        rm.update_resource(rid, tmp_db)


def test_delete_resource(tmp_db):
    rm.create_database(tmp_db)
    rid = rm.add_resource("Food", "Humanitarian", 50, "Warehouse C", tmp_db)
    count = rm.delete_resource(rid, tmp_db)
    assert count == 1
    assert rm.get_resource(rid, tmp_db) is None
    # second delete -> 0 rows
    assert rm.delete_resource(rid, tmp_db) == 0


def test_search_by_name(tmp_db):
    rm.create_database(tmp_db)
    rm.add_resource("Water Filters", "Humanitarian", 10, "A", tmp_db)
    rm.add_resource("Water Pumps", "Equipment", 5, "B", tmp_db)
    rm.add_resource("Tents", "Shelter", 20, "C", tmp_db)
    results = rm.search_resources(name="Water", db_name=tmp_db)
    assert len(results) == 2


def test_search_by_category_and_status(tmp_db):
    rm.create_database(tmp_db)
    rm.add_resource("A", "Humanitarian", 1, "X", tmp_db)
    rm.add_resource("B", "Shelter", 2, "Y", tmp_db)
    rm.update_resource(2, tmp_db, status="in_use")
    results = rm.search_resources(
        category="Shelter", status="in_use", db_name=tmp_db)
    assert len(results) == 1
    assert results[0]["name"] == "B"


def test_search_no_filters_returns_all(tmp_db):
    rm.create_database(tmp_db)
    rm.add_resource("A", "X", 1, "Y", tmp_db)
    rm.add_resource("B", "X", 2, "Y", tmp_db)
    results = rm.search_resources(db_name=tmp_db)
    assert len(results) == 2


# --- validation ---
def test_add_resource_invalid_name(tmp_db):
    rm.create_database(tmp_db)
    with pytest.raises(ValueError, match="name"):
        rm.add_resource("", "X", 1, "Y", tmp_db)
    with pytest.raises(ValueError, match="name"):
        rm.add_resource(123, "X", 1, "Y", tmp_db)


def test_add_resource_invalid_quantity(tmp_db):
    rm.create_database(tmp_db)
    with pytest.raises(ValueError, match="quantity"):
        rm.add_resource("X", "Y", -5, "Z", tmp_db)
    with pytest.raises(ValueError, match="quantity"):
        rm.add_resource("X", "Y", "ten", "Z", tmp_db)


def test_update_resource_invalid_status(tmp_db):
    rm.create_database(tmp_db)
    rid = rm.add_resource("X", "Y", 1, "Z", tmp_db)
    with pytest.raises(ValueError, match="status"):
        rm.update_resource(rid, tmp_db, status="bogus")


def test_search_invalid_status(tmp_db):
    rm.create_database(tmp_db)
    with pytest.raises(ValueError, match="status"):
        rm.search_resources(status="bogus", db_name=tmp_db)
