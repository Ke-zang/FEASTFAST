"""About Us (page names: "about_public", "about", "about_admin").

One shared body (build_about) shown in three shells, so the page is available
from the landing page, from the customer sidebar and from the manager sidebar.
"""
import tkinter as tk

from main import C, LinkLabel, Logo, Page, font
from dashboard import EDGE, PAGE_BG, CustomerPage
from admin_reservation import AdminPage
from check_availability import ADMIN_BG
from orders_store import MANAGER_PHONE, MAX_ATTEMPTS

WRAP = 700

INTRO = ("Feast Fast is an online food ordering and table reservation system for the "
         "college canteen. Students and staff can order ahead, reserve a table and "
         "collect their food the moment it is ready, instead of standing in a long line. "
         "Canteen managers get one place to see orders, update their progress, manage "
         "the menu and handle reservations.")

PROBLEMS = (
    ("Long lines", "Order from your phone or laptop and skip the queue."),
    ("No table booking", "Reserve a table by date, time and number of people."),
    ("Mistakes in orders", "Pick items from a live menu; sold-out food can't be ordered."),
    ("Hard to track orders", "Managers see every order and move it through each stage."),
)

CUSTOMER_STEPS = (
    ("Create an account and log in", "Sign up with your name, email and a strong password."),
    ("Browse the menu", "Search, or filter by Veg, Non-Veg and Beverage, then press "
                        "Add to Cart. Choose the quantity first."),
    ("Check your cart", "Change quantities or remove items, then press Proceed to Payment."),
    ("Pay first", "Choose QR payment or Account payment, pay the exact total, then type the "
                  "journal number from your banking app. You can only order after paying."),
    ("Wait for confirmation", "The canteen checks your journal number and confirms your "
                              "payment before it starts cooking. You get a notification."),
    ("Track your order", "My Order shows the status: Pending, Preparing, Ready, Completed."),
    ("Collect your food", "When the canteen marks it Ready you get a notification "
                          "(pop-up and the bell). Collect it at the counter."),
)

TABLE_STEPS = (
    ("Open Reservation", "Pick a date (DD/MM/YY), a time and the number of people."),
    ("Check Availability", "You see the tables that are free and big enough."),
    ("Reserve Table", "Press Reserve Table. Find it later under My Bookings, "
                      "where you can cancel any time."),
)

MANAGER_STEPS = (
    ("Sign in to the Staff Portal", "Use your staff username and password."),
    ("Watch the Dashboard", "See orders waiting, orders in progress, tables booked and "
                            "menu items available."),
    ("Check the payment", "Each new order shows its journal number. Look for it in the canteen "
                          "bank statement (same amount), then press Confirm payment. If it is "
                          "not there, press Wrong journal no. and the customer is told."),
    ("Manage Order", "Only after the payment is confirmed: Start Preparing, Mark Ready, "
                     "Complete. The customer is notified when it is Ready."),
    ("Refunds", "If a customer cancels a paid order they phone you. Send the money back by "
                "hand, then press Mark Refunded."),
    ("Manage Menu", "Add items, change prices, mark an item sold out or delete it. "
                    "Customers see changes straight away."),
    ("Reservation", "See every table booking made by customers."),
)

RULES = (
    "You must pay before you can order. An order only reaches the canteen once the "
    "payment (with its journal number) has been submitted.",
    "The canteen starts preparing only after it has confirmed your payment.",
    "A journal number can be used for one order only. If the canteen can't find yours, "
    f"you can enter it again in My Order (Fix payment), up to {MAX_ATTEMPTS} tries in total, "
    "then you must call the manager.",
    "A customer can cancel an order only while it is Pending. Once the manager starts "
    "preparing it, the order is locked and cannot be cancelled.",
    "If you cancel a paid order while it is still Pending, you get your money back by "
    "calling the manager (number above). Refunds are done by hand.",
    "The manager is notified when a paid order arrives and when a customer cancels one.",
    "The customer is notified when the payment is confirmed, when preparing starts and "
    "when the order is Ready.",
    "Notifications appear as a pop-up and in the bell at the top right (the number is "
    "how many you haven't read). The app checks for news every 2 seconds.",
    "A table can't be booked twice for the same date and time.",
    "Passwords are never stored in plain text, only as a salted hash.",
)

PAYMENT_GUIDE = (
    ("Checking", "You paid and entered a journal number. The canteen has not confirmed it yet."),
    ("Verified", "The canteen found your payment. Preparing can start."),
    ("Rejected", "The journal number wasn't found. Use Fix payment in My Order, or call the manager."),
    ("Refund due", "You cancelled a paid order. Call the manager to get your money back."),
    ("Refunded", "The manager has sent your money back."),
)

TECH = (("Design", "Figma: one shared design system and a screen flow for each member."),
        ("Screens", "Python Tkinter: login, dashboard, menu, cart, orders, reservations, manager screens."),
        ("Logic", "Python: checks input, handles orders, cancelling, bookings and notifications."),
        ("Database", "SQLite (feastfast.db): users, menu_items, orders, order_items, payments, "
                     "tables, reservations and notifications."))

TEAM = "Ugyen Wangmo · Kezang Tshomo · Benita Sharma · Dechen Wangmo · Nima Wangmo · Dhan Maya Gurung"
TUTOR = "Mr. Sangay Thinley"


class Scroller(tk.Frame):
    """A frame whose content scrolls with the mouse wheel."""

    def __init__(self, parent, bg):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        bar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=bg)
        win = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(win, width=e.width))
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._wheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _wheel(self, e):
        self.canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")

    def to_top(self):
        self.canvas.yview_moveto(0)


def _card(parent, bg, title):
    card = tk.Frame(parent, bg=C["card"], highlightthickness=1, highlightbackground=EDGE)
    card.pack(fill="x", pady=(0, 14), padx=(0, 18))
    tk.Label(card, text=title, font=font(13, "bold"), fg=C["ink"], bg=C["card"],
             anchor="w").pack(fill="x", padx=22, pady=(18, 8))
    body = tk.Frame(card, bg=C["card"])
    body.pack(fill="x", padx=22, pady=(0, 18))
    return body


def _para(parent, text, muted=False):
    tk.Label(parent, text=text, font=font(10), fg=C["muted"] if muted else C["ink"],
             bg=C["card"], anchor="w", justify="left", wraplength=WRAP).pack(fill="x")


def _steps(parent, steps):
    for n, (head, text) in enumerate(steps, 1):
        row = tk.Frame(parent, bg=C["card"])
        row.pack(fill="x", pady=5)
        badge = tk.Label(row, text=str(n), font=font(10, "bold"), fg="#FFFFFF",
                         bg=C["primary"], width=3, pady=3)
        badge.pack(side="left", anchor="n")
        col = tk.Frame(row, bg=C["card"])
        col.pack(side="left", fill="x", expand=True, padx=(12, 0))
        tk.Label(col, text=head, font=font(10, "bold"), fg=C["ink"], bg=C["card"],
                 anchor="w").pack(fill="x")
        tk.Label(col, text=text, font=font(10), fg=C["muted"], bg=C["card"], anchor="w",
                 justify="left", wraplength=WRAP - 50).pack(fill="x")


def _bullets(parent, lines):
    for line in lines:
        row = tk.Frame(parent, bg=C["card"])
        row.pack(fill="x", pady=3)
        tk.Label(row, text="•", font=font(11, "bold"), fg=C["primary"],
                 bg=C["card"]).pack(side="left", anchor="n")
        tk.Label(row, text=line, font=font(10), fg=C["ink"], bg=C["card"], anchor="w",
                 justify="left", wraplength=WRAP).pack(side="left", padx=(8, 0))


def build_about(parent, bg):
    """Fill `parent` with the About Us content; returns the Scroller."""
    sc = Scroller(parent, bg)
    p = sc.inner

    _para(_card(p, bg, "What is Feast Fast?"), INTRO)

    body = _card(p, bg, "Contact the canteen manager")
    _para(body, "Call for refunds and payment problems (for example a journal number the "
                "canteen can't find).")
    tk.Label(body, text=MANAGER_PHONE, font=font(16, "bold"), fg=C["primary"], bg=C["card"],
             anchor="w").pack(fill="x", pady=(8, 0))

    body = _card(p, bg, "Problems we solve")
    for head, text in PROBLEMS:
        row = tk.Frame(body, bg=C["card"])
        row.pack(fill="x", pady=3)
        tk.Label(row, text=head, font=font(10, "bold"), fg=C["primary"], bg=C["card"],
                 width=20, anchor="w").pack(side="left")
        tk.Label(row, text=text, font=font(10), fg=C["ink"], bg=C["card"], anchor="w",
                 justify="left", wraplength=WRAP - 160).pack(side="left")

    _steps(_card(p, bg, "How it works: ordering food (customers)"), CUSTOMER_STEPS)
    _steps(_card(p, bg, "How it works: reserving a table (customers)"), TABLE_STEPS)
    _steps(_card(p, bg, "How it works: running the canteen (managers)"), MANAGER_STEPS)
    _bullets(_card(p, bg, "Important rules and notifications"), RULES)

    body = _card(p, bg, "Order status guide")
    for status, text in (("Pending", "Order and payment received. You can still cancel it."),
                         ("Preparing", "The kitchen has started. It can no longer be cancelled."),
                         ("Ready", "Your food is ready. Come to the counter."),
                         ("Completed", "Collected. Thank you!"),
                         ("Cancelled", "Cancelled before preparing started. If you had paid, call "
                                       "the manager for a refund.")):
        row = tk.Frame(body, bg=C["card"])
        row.pack(fill="x", pady=3)
        tk.Label(row, text=status, font=font(10, "bold"), fg=C["ink"], bg=C["card"],
                 width=12, anchor="w").pack(side="left")
        tk.Label(row, text=text, font=font(10), fg=C["muted"], bg=C["card"],
                 anchor="w").pack(side="left")

    body = _card(p, bg, "Payment status guide")
    for status, text in PAYMENT_GUIDE:
        row = tk.Frame(body, bg=C["card"])
        row.pack(fill="x", pady=3)
        tk.Label(row, text=status, font=font(10, "bold"), fg=C["ink"], bg=C["card"],
                 width=12, anchor="w").pack(side="left", anchor="n")
        tk.Label(row, text=text, font=font(10), fg=C["muted"], bg=C["card"], anchor="w",
                 justify="left", wraplength=WRAP - 110).pack(side="left")

    body = _card(p, bg, "How it is built")
    for head, text in TECH:
        row = tk.Frame(body, bg=C["card"])
        row.pack(fill="x", pady=3)
        tk.Label(row, text=head, font=font(10, "bold"), fg=C["ink"], bg=C["card"],
                 width=10, anchor="w").pack(side="left", anchor="n")
        tk.Label(row, text=text, font=font(10), fg=C["muted"], bg=C["card"], anchor="w",
                 justify="left", wraplength=WRAP - 90).pack(side="left")

    body = _card(p, bg, "The team")
    _para(body, TEAM)
    tk.Label(body, text=f"Module tutor: {TUTOR}", font=font(10, "bold"), fg=C["ink"],
             bg=C["card"], anchor="w").pack(fill="x", pady=(8, 0))
    _para(body, "College project: Online Food Ordering and Table Reservation System.",
          muted=True)
    return sc


class PublicAboutPage(Page):
    """About Us from the landing page (no login needed)."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        top = tk.Frame(self, bg=C["bg"])
        top.pack(fill="x", padx=48, pady=(24, 8))
        Logo(top, size=36, bg=C["bg"]).pack(side="left")
        tk.Label(top, text="About Feast Fast", font=font(18, "bold"), fg=C["ink"],
                 bg=C["bg"]).pack(side="left", padx=12)
        LinkLabel(top, "←  Back to home", lambda: controller.show("landing"),
                  fg=C["muted"], bg=C["bg"], size=10).pack(side="right")
        self.scroller = build_about(self, C["bg"])
        self.scroller.pack(fill="both", expand=True, padx=48, pady=(0, 16))

    def on_show(self, **kwargs):
        self.scroller.to_top()


class CustomerAboutPage(CustomerPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, active="about")
        self.scroller = build_about(self.content, PAGE_BG)
        self.scroller.pack(fill="both", expand=True)

    def refresh(self):
        self.set_header("About Us", "What Feast Fast is and how it works.")
        self.scroller.to_top()


class AdminAboutPage(AdminPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, active="admin_about")
        self.scroller = build_about(self.content, ADMIN_BG)
        self.scroller.pack(fill="both", expand=True)

    def refresh(self):
        self.set_header("About Us", "What Feast Fast is and how it works.")
        self.scroller.to_top()


if __name__ == "__main__":
    import main
    main.App("about_public").mainloop()
