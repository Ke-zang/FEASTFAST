"""Orders and payments shared between the customer screens and the manager screens (SQLite).

Order life-cycle:   Pending -> Preparing -> Ready -> Completed
                    Pending -> Cancelled          (customer, ONLY while Pending)

An order only exists once the customer has paid: the cart goes to the Payment
screen and place_order() creates the order together with its payment.

Payment life-cycle (table `payments`, one row per journal number typed):
    Submitted  -> Verified    the manager found the journal number in the canteen's bank statement
    Submitted  -> Rejected    not found (wrong number). The customer may re-enter it, up to
                              MAX_ATTEMPTS times in total, then must call the manager
    Submitted / Verified -> Refund due -> Refunded
                              the customer cancelled a paid order that was still Pending.
                              Refunds are done by hand: the customer phones the manager.

Why wrong journal numbers can't slip through:
  * the format is checked (check_journal) before anything is saved,
  * the same journal number can't be used for a second order (unique index in db.py),
  * the manager can only press Start Preparing after pressing Confirm payment,
  * the rules are enforced inside SQL (UPDATE ... WHERE ...), so even if two windows click
    at the same moment, an unpaid order can't be started and a started order can't be cancelled.
"""
import re
import sqlite3
from datetime import datetime

import db
import notifications

FLOW = ("Pending", "Preparing", "Ready", "Completed")     # manager moves an order along
ACTIVE = ("Pending", "Preparing", "Ready")

# ── Payment settings (change them here, every screen reads them from this file) ──
MANAGER_PHONE = "+975 17 000 000"        # TODO: put the canteen manager's real number here
ACCOUNT_DETAILS = (("Bank Name", "BOB (Bank of Bhutan)"),
                   ("Account name", "College Canteen"),
                   ("Account Number", "205218541"))
METHODS = ("QR payment", "Account payment")
JOURNAL_MIN, JOURNAL_MAX = 6, 20         # allowed length of a journal number
MAX_ATTEMPTS = 3                         # journal numbers a customer may try for one order

PAYMENT_LABELS = {"Submitted": "Checking", "Verified": "Verified", "Rejected": "Rejected",
                  "Refund due": "Refund due", "Refunded": "Refunded"}

# SQL: the order may be started if its payment is verified (or if it has no payment row
# at all, which only happens to orders placed before online payment existed).
_PAID_OK = ("(NOT EXISTS (SELECT 1 FROM payments p WHERE p.order_id = orders.id) "
            "OR EXISTS (SELECT 1 FROM payments p WHERE p.order_id = orders.id "
            "AND p.status = 'Verified'))")


def order_code(pk):
    return f"FF-{1000 + pk}"


def _placed(text):
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%y %I:%M %p").lower()
    except (TypeError, ValueError):
        return text or ""


# ── Journal number check ────────────────────────────────────────────────────
def _is_run(text):
    """True for 123456, 987654, ABCDEF ... (a straight run of characters)."""
    steps = {ord(b) - ord(a) for a, b in zip(text, text[1:])}
    return steps in ({1}, {-1})


def check_journal(text):
    """Returns (clean journal number, None) or (None, error message)."""
    clean = re.sub(r"\s+", "", text or "").upper()
    if not clean:
        return None, "Enter the journal number from your payment."
    if not re.fullmatch(r"[A-Z0-9]+", clean):
        return None, "A journal number has letters and digits only."
    if not JOURNAL_MIN <= len(clean) <= JOURNAL_MAX:
        return None, f"A journal number is {JOURNAL_MIN}-{JOURNAL_MAX} characters long."
    if len(set(clean)) == 1 or _is_run(clean):
        return None, "That doesn't look like a real journal number. Copy it from your banking app."
    return clean, None


# ── Reading orders ──────────────────────────────────────────────────────────
def _orders(where="", args=()):
    c = db.conn()
    rows = c.execute(f"SELECT * FROM orders {where} ORDER BY id DESC", args).fetchall()
    if not rows:
        return []
    ids = [r["id"] for r in rows]
    marks = ",".join("?" * len(ids))
    items = {}
    for i in c.execute(f"SELECT * FROM order_items WHERE order_id IN ({marks}) ORDER BY id", ids):
        items.setdefault(i["order_id"], []).append(
            {"name": i["name"], "quantity": i["quantity"], "price": i["price"]})
    latest, tries = {}, {}                       # newest payment of each order, number of tries
    for p in c.execute(f"SELECT * FROM payments WHERE order_id IN ({marks}) ORDER BY id", ids):
        latest[p["order_id"]] = {"id": p["id"], "method": p["method"], "journal": p["journal_no"],
                                 "amount": p["amount"], "status": p["status"],
                                 "submitted": _placed(p["submitted_at"]),
                                 "verified": p["verified_at"]}
        tries[p["order_id"]] = tries.get(p["order_id"], 0) + 1
    return [{"pk": r["id"], "id": order_code(r["id"]), "email": r["customer_email"],
             "customer": r["customer_name"], "items": items.get(r["id"], []),
             "total": r["total"], "status": r["status"], "placed": _placed(r["created_at"]),
             "payment": latest.get(r["id"]), "attempts": tries.get(r["id"], 0)}
            for r in rows]


def all_orders():
    """Every order, newest first (manager screens)."""
    return _orders()


def orders_for(email):
    """One customer's orders, newest first."""
    return _orders("WHERE customer_email = ?", (email,))


def get_order(pk):
    rows = _orders("WHERE id = ?", (pk,))
    return rows[0] if rows else None


def count_status(*statuses):
    marks = ",".join("?" * len(statuses))
    return db.conn().execute(f"SELECT COUNT(*) FROM orders WHERE status IN ({marks})",
                             statuses).fetchone()[0]


def count_ready_to_start():
    """Pending orders whose payment the manager has confirmed."""
    return db.conn().execute(
        f"SELECT COUNT(*) FROM orders WHERE status = 'Pending' AND {_PAID_OK}").fetchone()[0]


def count_payments(*statuses):
    """Orders whose newest payment is in one of these states."""
    marks = ",".join("?" * len(statuses))
    return db.conn().execute(
        f"SELECT COUNT(*) FROM payments p WHERE p.status IN ({marks}) AND p.id = "
        "(SELECT MAX(id) FROM payments WHERE order_id = p.order_id)", statuses).fetchone()[0]


# ── Small helpers the screens use ───────────────────────────────────────────
def payment_status(order):
    """'Submitted', 'Verified', 'Rejected', 'Refund due', 'Refunded' or None."""
    pay = order.get("payment")
    return pay["status"] if pay else None


def payment_label(status):
    return PAYMENT_LABELS.get(status, status)


def attempts_left(order):
    return max(0, MAX_ATTEMPTS - order.get("attempts", 0))


def can_fix_payment(order):
    """The manager rejected the journal number and the customer may type another."""
    return (order["status"] == "Pending" and payment_status(order) == "Rejected"
            and attempts_left(order) > 0)


def _latest_payment(c, pk):
    return c.execute("SELECT * FROM payments WHERE order_id=? ORDER BY id DESC LIMIT 1",
                     (pk,)).fetchone()


_DUPLICATE = ("That journal number has already been used for another order. "
              "Check it in your banking app. If you are sure it is right, call the manager "
              f"on {MANAGER_PHONE}.")


# ── Placing an order (= paying) ─────────────────────────────────────────────
def _price_cart(c, cart):
    """Re-check prices and availability against the menu table right now.
    Returns (lines, total, problem message or None)."""
    lines, problems = [], []
    for line in cart:
        row = c.execute("SELECT * FROM menu_items WHERE name = ?", (line["name"],)).fetchone()
        if row is None or not row["available"]:
            problems.append(line["name"])
        else:
            lines.append((row["id"], row["name"], line["quantity"], row["price"]))
    if problems:
        return None, 0, ("No longer available: " + ", ".join(problems)
                         + ". Remove them and try again.")
    if not lines:
        return None, 0, "Your cart is empty."
    return lines, sum(q * p for _, _, q, p in lines), None


def cart_problem(cart):
    """Message if the cart can't be ordered right now (sold-out item, empty), else None.
    The cart screen calls this BEFORE sending the customer to pay."""
    return _price_cart(db.conn(), cart)[2]


def place_order(email, name, cart, method, journal, expected_total=None):
    """Create the order together with its payment, in one transaction.
    Returns (order, None) or (None, error message).

    expected_total is the amount the customer was shown (and paid); if a price
    changed in the meantime the order is refused instead of charging a different amount.
    """
    if method not in METHODS:
        return None, "Choose how you paid: QR payment or Account payment."
    clean, error = check_journal(journal)
    if error:
        return None, error
    c = db.conn()
    lines, total, problem = _price_cart(c, cart)
    if problem:
        return None, problem
    if expected_total is not None and abs(total - expected_total) > 0.005:
        return None, (f"A price changed while you were paying. The total is now Nu. {total:g}. "
                      "Go back to your cart and check it. If you have already sent money, "
                      f"call the manager on {MANAGER_PHONE}.")
    try:
        with c:                                       # one transaction: all or nothing
            user = c.execute("SELECT id FROM users WHERE email = ? AND role = 'customer'",
                             (email,)).fetchone()
            cur = c.execute("INSERT INTO orders (user_id, customer_email, customer_name, total) "
                            "VALUES (?, ?, ?, ?)",
                            (user["id"] if user else None, email, name, total))
            pk = cur.lastrowid
            c.executemany("INSERT INTO order_items (order_id, menu_item_id, name, quantity, price) "
                          "VALUES (?, ?, ?, ?, ?)", [(pk, *line) for line in lines])
            c.execute("INSERT INTO payments (order_id, method, journal_no, amount) "
                      "VALUES (?, ?, ?, ?)", (pk, method, clean, total))
            count = sum(q for _, _, q, _ in lines)
            notifications.add(notifications.ADMIN,
                              f"New PAID order {order_code(pk)} from {name}: {count} "
                              f"item{'s' if count != 1 else ''}, Nu. {total:g} ({method}, "
                              f"journal no. {clean}). Check the journal number, then confirm "
                              f"the payment and start preparing.", pk)
    except sqlite3.IntegrityError:                    # same journal number already used
        return None, _DUPLICATE
    return get_order(pk), None


def resubmit_payment(order, method, journal):
    """The manager rejected the journal number: the customer types another one.
    Returns None on success, or an error message."""
    if method not in METHODS:
        return "Choose how you paid: QR payment or Account payment."
    clean, error = check_journal(journal)
    if error:
        return error
    c = db.conn()
    try:
        with c:
            row = c.execute("SELECT status, total FROM orders WHERE id=?", (order["pk"],)).fetchone()
            if row is None or row["status"] != "Pending":
                now = row["status"].lower() if row else "removed"
                return f"This order is {now}, so its payment can't be changed."
            last = _latest_payment(c, order["pk"])
            if last is None or last["status"] != "Rejected":
                return "This payment doesn't need to be entered again."
            tries = c.execute("SELECT COUNT(*) FROM payments WHERE order_id=?",
                              (order["pk"],)).fetchone()[0]
            if tries >= MAX_ATTEMPTS:
                return (f"You have used all {MAX_ATTEMPTS} tries. "
                        f"Please call the manager on {MANAGER_PHONE}.")
            c.execute("INSERT INTO payments (order_id, method, journal_no, amount) "
                      "VALUES (?, ?, ?, ?)", (order["pk"], method, clean, row["total"]))
            notifications.add(notifications.ADMIN,
                              f"Order {order['id']} from {order['customer']}: new journal no. "
                              f"{clean} ({method}), Nu. {row['total']:g}. Please check it.",
                              order["pk"])
    except sqlite3.IntegrityError:
        return _DUPLICATE
    return None


# ── Cancelling ──────────────────────────────────────────────────────────────
def cancel_order(order):
    """Customer cancels. Allowed ONLY while the order is still Pending.
    Returns (refund_due, None) on success, or (False, message saying why not).

    If the customer had paid, the payment becomes 'Refund due'. The refund is done by
    hand: the customer phones the manager (number on the About Us page)."""
    c = db.conn()
    refund = False
    with c:
        changed = c.execute("UPDATE orders SET status='Cancelled' "
                            "WHERE id=? AND status='Pending'", (order["pk"],)).rowcount
        if changed:
            pay = _latest_payment(c, order["pk"])
            if pay and c.execute("UPDATE payments SET status='Refund due' WHERE id=? "
                                 "AND status IN ('Submitted','Verified')",
                                 (pay["id"],)).rowcount:
                refund = True
                check = "" if pay["verified_at"] else " (payment not confirmed yet: check the bank statement first)"
                notifications.add(notifications.ADMIN,
                                  f"Order {order['id']} was cancelled by {order['customer']}. "
                                  f"REFUND DUE: Nu. {pay['amount']:g}, journal no. "
                                  f"{pay['journal_no']}{check}. The customer will call you. "
                                  f"Refund by hand, then press Mark Refunded.", order["pk"])
            else:
                notifications.add(notifications.ADMIN,
                                  f"Order {order['id']} was cancelled by {order['customer']}.",
                                  order["pk"])
    if changed:
        return refund, None
    row = c.execute("SELECT status FROM orders WHERE id=?", (order["pk"],)).fetchone()
    now = row["status"] if row else "removed"
    if now == "Cancelled":
        return False, "This order is already cancelled."
    return False, f"Too late to cancel: the order is already {now.lower()}."


# ── Manager: payments ───────────────────────────────────────────────────────
def verify_payment(order):
    """Manager found the journal number (and the right amount) in the bank statement.
    Returns None on success, or an error message."""
    c = db.conn()
    changed = 0
    with c:
        pay = _latest_payment(c, order["pk"])
        if pay and pay["status"] == "Submitted":
            changed = c.execute(
                "UPDATE payments SET status='Verified', verified_at=datetime('now','localtime') "
                "WHERE id=? AND status='Submitted' "
                "AND EXISTS (SELECT 1 FROM orders WHERE id=? AND status='Pending')",
                (pay["id"], order["pk"])).rowcount
        if changed:
            notifications.add(order["email"],
                              f"Payment for order {order['id']} is confirmed. "
                              f"The canteen will start preparing it soon.", order["pk"])
    return None if changed else "This payment was just changed (maybe the order was cancelled). Refreshing…"


def reject_payment(order):
    """Manager could NOT find the journal number (wrong number / money not received).
    Works on a Pending order (customer may then re-enter the number) and on a cancelled
    order whose payment was never confirmed (no refund is due after all).
    Returns None on success, or an error message."""
    c = db.conn()
    changed = 0
    with c:
        pay = _latest_payment(c, order["pk"])
        if pay and (pay["status"] == "Submitted"
                    or (pay["status"] == "Refund due" and pay["verified_at"] is None)):
            was = pay["status"]
            changed = c.execute("UPDATE payments SET status='Rejected' WHERE id=? AND status=?",
                                (pay["id"], was)).rowcount
        if changed:
            journal = pay["journal_no"]
            if was == "Refund due":
                text = (f"No payment with journal number {journal} was found for the cancelled "
                        f"order {order['id']}, so no refund is due. If you did pay, please call "
                        f"the manager on {MANAGER_PHONE}.")
            else:
                tries = c.execute("SELECT COUNT(*) FROM payments WHERE order_id=?",
                                  (order["pk"],)).fetchone()[0]
                left = MAX_ATTEMPTS - tries
                if left > 0:
                    text = (f"We could not find journal number {journal} for order {order['id']}. "
                            f"If you paid, open My Order > Fix payment and enter the correct "
                            f"number ({left} {'try' if left == 1 else 'tries'} left), or call "
                            f"the manager on {MANAGER_PHONE}.")
                else:
                    text = (f"We could not find journal number {journal} for order {order['id']} "
                            f"and you have no tries left. Please call the manager on "
                            f"{MANAGER_PHONE}.")
            notifications.add(order["email"], text, order["pk"])
    return None if changed else "This payment was just changed. Refreshing…"


def mark_refunded(order):
    """Manager paid the money back by hand. Returns None on success, or an error message."""
    c = db.conn()
    changed = 0
    with c:
        pay = _latest_payment(c, order["pk"])
        if pay:
            changed = c.execute("UPDATE payments SET status='Refunded' WHERE id=? "
                                "AND status='Refund due'", (pay["id"],)).rowcount
        if changed:
            notifications.add(order["email"],
                              f"Your refund of Nu. {pay['amount']:g} for order {order['id']} "
                              f"has been sent.", order["pk"])
    return None if changed else "This refund was just changed. Refreshing…"


# ── Manager: moving an order along ──────────────────────────────────────────
def next_status(order):
    i = FLOW.index(order["status"]) if order["status"] in FLOW else len(FLOW) - 1
    return FLOW[min(i + 1, len(FLOW) - 1)]


def advance_order(order):
    """Manager moves an order one step. Returns (new_status, None) or (None, error).

    An order can only leave Pending once its payment is Verified (checked inside SQL)."""
    c = db.conn()
    row = c.execute("SELECT status FROM orders WHERE id=?", (order["pk"],)).fetchone()
    if row is None or row["status"] not in FLOW[:-1]:
        shown = row["status"] if row else "removed"
        return None, f"This order is {shown.lower()} and can't be moved on."
    old = row["status"]
    new = FLOW[FLOW.index(old) + 1]
    guard = f" AND {_PAID_OK}" if old == "Pending" else ""
    with c:
        changed = c.execute(f"UPDATE orders SET status=? WHERE id=? AND status=?{guard}",
                            (new, order["pk"], old)).rowcount
        if changed and new == "Preparing":
            notifications.add(order["email"],
                              f"The canteen has started preparing order {order['id']}. "
                              f"It can no longer be cancelled.", order["pk"])
        if changed and new == "Ready":
            notifications.add(order["email"],
                              f"Your order {order['id']} is ready — please collect it "
                              f"at the counter.", order["pk"])
    if changed:
        return new, None
    if old == "Pending":                               # still Pending: so the payment is the reason
        still = c.execute("SELECT status FROM orders WHERE id=?", (order["pk"],)).fetchone()
        pay = _latest_payment(c, order["pk"])
        if still and still["status"] == "Pending" and pay:
            if pay["status"] == "Submitted":
                return None, "Confirm the payment first (check the journal number in the bank statement)."
            if pay["status"] == "Rejected":
                return None, "The journal number was rejected. Wait for the customer to enter a correct one."
    return None, "This order was just changed (maybe cancelled). Refreshing…"


def summary(order, limit=34):
    text = ", ".join(f'{i["quantity"]} × {i["name"]}' for i in order["items"])
    return text if len(text) <= limit else text[:limit - 1] + "…"


def sync_state(controller):
    """Keep the customer's session counters (dashboard badges) up to date."""
    st = controller.state
    st["orders"] = [o for o in orders_for(st.get("email")) if o["status"] in ACTIVE]
