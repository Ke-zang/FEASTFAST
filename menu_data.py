"""The canteen menu, stored in the `menu_items` table of feastfast.db.

MENU_ITEMS is a cache list that every screen reads. It is refreshed *in place*
(reload()), so modules that did `from menu_data import MENU_ITEMS` always see
the latest rows. All changes go through the functions below, which write to
SQLite first and then reload the cache.
"""
import sqlite3

import db

CATEGORIES = ("Veg", "Non-Veg", "Beverage")

# category -> (tile tint, dot colour) for the dashboard dish cards
LOOK = {"Veg": ("#EAF3DF", "#6FAE5B"),
        "Non-Veg": ("#FBE6DA", "#C8501A"),
        "Beverage": ("#FDF1D8", "#D9A95A")}


def _item(row):
    tint, dot = LOOK.get(row["category"], LOOK["Veg"])
    price = row["price"]
    return {"id": row["id"], "name": row["name"], "category": row["category"],
            "price": int(price) if price == int(price) else price,
            "available": bool(row["available"]), "tint": tint, "dot": dot}


MENU_ITEMS = []


def reload():
    """Re-read the menu from the database (call when a screen is shown)."""
    rows = db.conn().execute("SELECT * FROM menu_items ORDER BY id").fetchall()
    MENU_ITEMS[:] = [_item(r) for r in rows]


def find(name):
    """Fresh lookup straight from the database (never a stale copy)."""
    row = db.conn().execute("SELECT * FROM menu_items WHERE name = ?", (name,)).fetchone()
    return _item(row) if row else None


def add_item(name, category, price):
    """Returns None on success, or an error message."""
    try:
        with db.conn():
            db.conn().execute("INSERT INTO menu_items (name, category, price) VALUES (?, ?, ?)",
                              (name, category, price))
    except sqlite3.IntegrityError:
        return f'"{name}" is already on the menu.'
    reload()
    return None


def update_item(item_id, name, category, price):
    try:
        with db.conn():
            db.conn().execute("UPDATE menu_items SET name=?, category=?, price=? WHERE id=?",
                              (name, category, price, item_id))
    except sqlite3.IntegrityError:
        return f'"{name}" is already on the menu.'
    reload()
    return None


def set_available(item_id, available):
    with db.conn():
        db.conn().execute("UPDATE menu_items SET available=? WHERE id=?",
                          (int(available), item_id))
    reload()


def delete_item(item_id):
    with db.conn():
        db.conn().execute("DELETE FROM menu_items WHERE id=?", (item_id,))
    reload()


def money(value):
    return f"Nu. {value:g}"


reload()
