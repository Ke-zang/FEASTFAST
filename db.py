"""SQLite database for Feast Fast (file: feastfast.db, created next to the app).

Every screen talks to the database through the small *_store modules, so this
is the only file that knows how the tables are built.

Tables: users, menu_items, orders, order_items, payments, tables,
        reservations, notifications
"""
import json
import os
import sqlite3
import hashlib
import secrets

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("FEASTFAST_DB", os.path.join(APP_DIR, "feastfast.db"))

DEFAULT_STAFF = ("manager", "Manager@123", "Store Manager")

DEFAULT_MENU = (
    ("Ema Datshi Rice", "Veg", 70), ("Paneer Curry", "Veg", 80),
    ("Veg Thukpa", "Veg", 60), ("Vegetable Momo", "Veg", 65),
    ("Chicken Momo", "Non-Veg", 80), ("Chicken Fried Rice", "Non-Veg", 90),
    ("Beef Noodles", "Non-Veg", 95), ("Pork Ribs", "Non-Veg", 110),
    ("Milk Tea", "Beverage", 20), ("Black Coffee", "Beverage", 25),
    ("Bottled Water", "Beverage", 15), ("Fresh Lime Soda", "Beverage", 30),
)

DEFAULT_TABLES = (("Table 1", 2), ("Table 2", 2), ("Table 3", 4), ("Table 4", 4),
                  ("Table 5", 6), ("Table 6", 6), ("Table 7", 8), ("Table 8", 4))

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name       TEXT NOT NULL,
    email           TEXT UNIQUE NOT NULL,          -- customers: email, staff: username
    phone           TEXT,
    salt            TEXT NOT NULL,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('customer', 'manager')),
    photo           TEXT,
    session_version INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS menu_items (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL UNIQUE,
    category  TEXT NOT NULL CHECK (category IN ('Veg', 'Non-Veg', 'Beverage')),
    price     REAL NOT NULL CHECK (price > 0),
    available INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS orders (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER REFERENCES users(id) ON DELETE SET NULL,
    customer_email TEXT NOT NULL,
    customer_name  TEXT NOT NULL,
    total          REAL NOT NULL,
    status         TEXT NOT NULL DEFAULT 'Pending'
                   CHECK (status IN ('Pending','Preparing','Ready','Completed','Cancelled')),
    created_at     TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS order_items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id     INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    menu_item_id INTEGER REFERENCES menu_items(id) ON DELETE SET NULL,
    name         TEXT NOT NULL,                    -- copied, so history survives menu edits
    quantity     INTEGER NOT NULL CHECK (quantity > 0),
    price        REAL NOT NULL
);

-- One row per journal number a customer typed for an order (a customer whose number
-- was rejected can try again, so an order can have several rows; the newest counts).
CREATE TABLE IF NOT EXISTS payments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id     INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    method       TEXT NOT NULL CHECK (method IN ('QR payment', 'Account payment')),
    journal_no   TEXT NOT NULL,
    amount       REAL NOT NULL,
    status       TEXT NOT NULL DEFAULT 'Submitted'
                 CHECK (status IN ('Submitted','Verified','Rejected','Refund due','Refunded')),
    submitted_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    verified_at  TEXT
);
-- the database itself refuses the same journal number on two orders (a rejected
-- number is free again, because it was not a real payment)
CREATE UNIQUE INDEX IF NOT EXISTS one_use_per_journal
    ON payments(journal_no) WHERE status <> 'Rejected';
CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id);

CREATE TABLE IF NOT EXISTS tables (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL UNIQUE,
    capacity INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS reservations (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER REFERENCES users(id) ON DELETE SET NULL,
    customer_email TEXT NOT NULL,
    booking_name   TEXT NOT NULL,
    table_id       INTEGER NOT NULL REFERENCES tables(id),
    date           TEXT NOT NULL,                  -- DD/MM/YY
    time           TEXT NOT NULL,                  -- e.g. 6:30 pm
    people         INTEGER NOT NULL,
    status         TEXT NOT NULL DEFAULT 'RESERVED' CHECK (status IN ('RESERVED','CANCELLED'))
);
-- the database itself refuses a second RESERVED booking for the same table and slot
CREATE UNIQUE INDEX IF NOT EXISTS one_booking_per_slot
    ON reservations(table_id, date, time) WHERE status = 'RESERVED';

CREATE TABLE IF NOT EXISTS notifications (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient  TEXT NOT NULL,                      -- 'admin' or a customer's email
    order_id   INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    message    TEXT NOT NULL,
    toasted    INTEGER NOT NULL DEFAULT 0,         -- already popped up on screen?
    is_read    INTEGER NOT NULL DEFAULT 0,         -- opened in the bell list?
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_orders_email  ON orders(customer_email);
CREATE INDEX IF NOT EXISTS idx_notif_to      ON notifications(recipient, toasted, is_read);
"""

_conn = None


def conn():
    """One shared connection for the whole app (opened on first use)."""
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, timeout=5)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys = ON")      # SQLite ignores FKs unless asked
        _conn.execute("PRAGMA journal_mode = WAL")     # two app windows can share the file
        init_db(_conn)
    return _conn


def close():
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000)
    return salt, digest.hex()


def init_db(c):
    c.executescript(SCHEMA)
    if not c.execute("SELECT 1 FROM users WHERE role = 'manager'").fetchone():
        user, pw, name = DEFAULT_STAFF
        salt, digest = hash_password(pw)
        c.execute("INSERT INTO users (full_name, email, salt, password_hash, role) "
                  "VALUES (?, ?, ?, ?, 'manager')", (name, user, salt, digest))
    if not c.execute("SELECT 1 FROM tables").fetchone():
        c.executemany("INSERT INTO tables (name, capacity) VALUES (?, ?)", DEFAULT_TABLES)
    if not c.execute("SELECT 1 FROM menu_items").fetchone():
        c.executemany("INSERT INTO menu_items (name, category, price) VALUES (?, ?, ?)",
                      DEFAULT_MENU)
    c.commit()
    if c.execute("PRAGMA user_version").fetchone()[0] == 0:
        _import_old_json(c)                      # first run only
        c.execute("PRAGMA user_version = 1")
        c.commit()


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _import_old_json(c):
    """One-time copy of the old users.json / data/*.json into the database.

    Runs once, on the very first start with the new database. The old files are
    left in place (safe to delete afterwards).
    """
    old = _read_json(os.path.join(APP_DIR, "users.json")) or {}
    for rec in old.get("customers", {}).values():
        c.execute("INSERT OR IGNORE INTO users (full_name, email, phone, salt, "
                  "password_hash, role, photo, session_version) "
                  "VALUES (?, ?, ?, ?, ?, 'customer', ?, ?)",
                  (rec.get("name", ""), rec.get("email", ""), rec.get("phone"),
                   rec.get("salt", ""), rec.get("hash", ""), rec.get("photo"),
                   rec.get("session_version", 0)))
    for username, rec in old.get("staff", {}).items():
        if c.execute("UPDATE users SET full_name=?, salt=?, password_hash=? "
                     "WHERE email=? AND role='manager'",
                     (rec.get("name", username), rec.get("salt", ""), rec.get("hash", ""),
                      username)).rowcount == 0:
            c.execute("INSERT OR IGNORE INTO users (full_name, email, salt, password_hash, role) "
                      "VALUES (?, ?, ?, ?, 'manager')",
                      (rec.get("name", username), username, rec.get("salt", ""),
                       rec.get("hash", "")))

    data_dir = os.path.join(APP_DIR, "data")
    saved_menu = _read_json(os.path.join(data_dir, "menu.json"))
    if isinstance(saved_menu, list) and saved_menu:
        c.execute("DELETE FROM menu_items")
        for i in saved_menu:
            c.execute("INSERT OR IGNORE INTO menu_items (name, category, price, available) "
                      "VALUES (?, ?, ?, ?)",
                      (i["name"], i["category"], i["price"], int(i.get("available", True))))
    for o in _read_json(os.path.join(data_dir, "orders.json")) or []:
        cur = c.execute("INSERT INTO orders (customer_email, customer_name, total, status) "
                        "VALUES (?, ?, ?, ?)",
                        (o.get("email") or "", o.get("customer", "Guest"),
                         o.get("total", 0), o.get("status", "Pending")))
        for i in o.get("items", []):
            c.execute("INSERT INTO order_items (order_id, menu_item_id, name, quantity, price) "
                      "VALUES (?, (SELECT id FROM menu_items WHERE name = ?), ?, ?, ?)",
                      (cur.lastrowid, i["name"], i["name"], i["quantity"], i["price"]))
    for b in _read_json(os.path.join(data_dir, "bookings.json")) or []:
        row = c.execute("SELECT id FROM tables WHERE name = ?", (b.get("table"),)).fetchone()
        if row:
            try:
                c.execute("INSERT INTO reservations (customer_email, booking_name, table_id, "
                          "date, time, people, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (b.get("email") or "", b.get("booking", "Guest"), row["id"],
                           b["date"], b["time"], b["people"], b.get("status", "RESERVED")))
            except sqlite3.IntegrityError:
                pass
    c.commit()
