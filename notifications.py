"""In-app notifications (stored in the `notifications` table).

recipient is the word "admin" (every manager) or a customer's email address.
 - new paid order / new journal number / customer cancelled (refund due) -> notify "admin"
 - payment confirmed / journal number not found / preparing started /
   order Ready / refund sent                                              -> notify that customer

The App polls this table every couple of seconds (see main.App._poll): new rows
pop up as a toast and the bell in the top bar shows how many are unread. The
add() function does NOT commit, so a notification is saved in the same
transaction as the order change that caused it (both happen, or neither).
"""
import tkinter as tk

import db

ADMIN = "admin"


def add(recipient, message, order_pk=None):
    db.conn().execute("INSERT INTO notifications (recipient, order_id, message) "
                      "VALUES (?, ?, ?)", (recipient, order_pk, message))


def take_new(recipient):
    """Messages not yet shown as a toast; marks them as shown."""
    rows = db.conn().execute("SELECT id, message FROM notifications "
                             "WHERE recipient=? AND toasted=0 ORDER BY id",
                             (recipient,)).fetchall()
    if rows:
        with db.conn():
            db.conn().executemany("UPDATE notifications SET toasted=1 WHERE id=?",
                                  [(r["id"],) for r in rows])
    return [r["message"] for r in rows]


def unread_count(recipient):
    return db.conn().execute("SELECT COUNT(*) FROM notifications WHERE recipient=? "
                             "AND is_read=0", (recipient,)).fetchone()[0]


def recent(recipient, limit=30):
    return db.conn().execute("SELECT message, is_read, created_at FROM notifications "
                             "WHERE recipient=? ORDER BY id DESC LIMIT ?",
                             (recipient, limit)).fetchall()


def mark_all_read(recipient):
    with db.conn():
        db.conn().execute("UPDATE notifications SET is_read=1 WHERE recipient=? AND is_read=0",
                          (recipient,))


def recipient_for(controller):
    """Who is signed in on this window: 'admin', a customer's email, or None."""
    st = controller.state
    if st.get("role") == "manager":
        return ADMIN
    return st.get("email")


class NotificationBell(tk.Label):
    """🔔 chip for the top bar: shows the unread count, click to read them."""

    def __init__(self, parent, controller, bg):
        from main import C, font          # local import: main loads this module lazily too
        self._C, self._font = C, font
        super().__init__(parent, text="", font=font(10, "bold"), bg=bg, fg=C["ink"],
                         cursor="hand2", padx=10, pady=4, highlightthickness=1,
                         highlightbackground=C["border"])
        self.controller = controller
        self.bind("<Button-1>", lambda e: self.open_list())
        self.update_count()

    def update_count(self):
        who = recipient_for(self.controller)
        n = unread_count(who) if who else 0
        self.config(text=f"🔔 {n}" if n else "🔔",
                    fg=self._C["primary"] if n else self._C["ink"])

    def open_list(self):
        who = recipient_for(self.controller)
        if not who:
            return
        C, font = self._C, self._font
        rows = recent(who)
        win = tk.Toplevel(self)
        win.title("Notifications")
        win.configure(bg=C["card"])
        win.transient(self.winfo_toplevel())
        win.geometry("460x380")
        tk.Label(win, text="Notifications", font=font(14, "bold"), fg=C["ink"],
                 bg=C["card"], anchor="w").pack(fill="x", padx=20, pady=(16, 8))
        body = tk.Frame(win, bg=C["card"])
        body.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        if not rows:
            tk.Label(body, text="Nothing yet.", font=font(10), fg=C["muted"],
                     bg=C["card"]).pack(pady=30)
        for r in rows[:8]:
            card = tk.Frame(body, bg=C["primary_soft"] if not r["is_read"] else C["field"])
            card.pack(fill="x", pady=3)
            tk.Label(card, text=r["message"], font=font(10, "bold" if not r["is_read"] else "normal"),
                     fg=C["ink"], bg=card["bg"], anchor="w", justify="left",
                     wraplength=380).pack(fill="x", padx=12, pady=(8, 0))
            tk.Label(card, text=r["created_at"], font=font(8), fg=C["muted"], bg=card["bg"],
                     anchor="w").pack(fill="x", padx=12, pady=(0, 8))
        mark_all_read(who)
        self.update_count()
