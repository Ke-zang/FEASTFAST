"""Table reservations (tables `tables` and `reservations` in SQLite)."""
import sqlite3

import db


def tables():
    """[(id, name, capacity), ...]"""
    return [(r["id"], r["name"], r["capacity"]) for r in
            db.conn().execute("SELECT id, name, capacity FROM tables ORDER BY id")]


def _booking(r):
    return {"pk": r["id"], "booking": r["booking_name"], "email": r["customer_email"],
            "table": r["table_name"], "date": r["date"], "time": r["time"],
            "people": r["people"], "status": r["status"]}


_SELECT = ("SELECT r.*, t.name AS table_name FROM reservations r "
           "JOIN tables t ON t.id = r.table_id ")


def all_bookings():
    return [_booking(r) for r in db.conn().execute(_SELECT + "ORDER BY r.id")]


def bookings_for(email):
    return [_booking(r) for r in
            db.conn().execute(_SELECT + "WHERE r.customer_email = ? ORDER BY r.id", (email,))]


def count_reserved():
    return db.conn().execute("SELECT COUNT(*) FROM reservations "
                             "WHERE status = 'RESERVED'").fetchone()[0]


def is_free(table_name, date_s, time_s):
    return db.conn().execute(
        "SELECT 1 FROM reservations r JOIN tables t ON t.id = r.table_id "
        "WHERE t.name=? AND r.date=? AND r.time=? AND r.status='RESERVED'",
        (table_name, date_s, time_s)).fetchone() is None


def create_booking(email, booking_name, table_name, date_s, time_s, people):
    """True if booked, False if somebody got that table and slot first."""
    c = db.conn()
    try:
        with c:
            user = c.execute("SELECT id FROM users WHERE email=? AND role='customer'",
                             (email,)).fetchone()
            c.execute("INSERT INTO reservations (user_id, customer_email, booking_name, table_id,"
                      " date, time, people) VALUES (?, ?, ?, (SELECT id FROM tables WHERE name=?),"
                      " ?, ?, ?)", (user["id"] if user else None, email or "", booking_name,
                                    table_name, date_s, time_s, people))
        return True
    except sqlite3.IntegrityError:          # the unique index refused a double booking
        return False


def cancel_booking(pk):
    with db.conn():
        db.conn().execute("UPDATE reservations SET status='CANCELLED' WHERE id=?", (pk,))
