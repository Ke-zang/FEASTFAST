"""Customer screens: Payment (page "payment") and Payment Submitted (page "payment_done").

Flow:  My Cart -> Proceed to Payment -> Payment -> Payment Submitted -> My Order
The order is only created when the payment is submitted (orders_store.place_order),
so a customer who has not paid cannot order. The canteen then checks the journal
number and confirms the payment before it starts preparing.

Fix payment: if the manager says a journal number was wrong, My Order opens this
same screen again for that order (state["repay"]) so the customer can type another.

To show the canteen's real QR code, save it as canteen_qr.png next to this file.
"""
import math
import os
import random
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

from main import C, FlatButton, FormField, font, round_rect
from dashboard import EDGE, PAGE_BG, CustomerPage
from about_page import Scroller
from menu_data import money
from orders_store import (ACCOUNT_DETAILS, MANAGER_PHONE, MAX_ATTEMPTS, attempts_left,
                          can_fix_payment, check_journal, get_order, place_order,
                          resubmit_payment, sync_state)
from ui_helpers import AMBER, AMBER_SOFT, GREEN, GREEN_SOFT

QR_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "canteen_qr.png")
GAP = (0, 18)                      # right margin so content clears the scroll bar


# ════════════════════════════ ICONS ════════════════════════════
class PayIcon(tk.Canvas):
    """Small drawn icons for the payment screens (no image files needed)."""
    SIZES = {"dollar": (56, 34), "qr": (30, 30), "bank": (40, 36),
             "receipt": (30, 30), "badge": (90, 90)}

    def __init__(self, parent, name, bg):
        w, h = self.SIZES[name]
        super().__init__(parent, width=w, height=h, bg=bg, highlightthickness=0)
        getattr(self, "_" + name)()

    def _dollar(self):
        round_rect(self, 3, 3, 53, 31, 10, outline=GREEN, fill="#FFFFFF", width=3)
        self.create_oval(19, 7, 37, 27, outline=GREEN, width=2)
        self.create_text(28, 17, text="$", fill=GREEN, font=font(11, "bold"))

    def _qr(self):
        for x, y in ((2, 2), (18, 2), (2, 18)):
            self.create_rectangle(x, y, x + 10, y + 10, outline="black", width=2)
            self.create_rectangle(x + 3, y + 3, x + 7, y + 7, fill="black", outline="black")
        for x, y in ((18, 18), (24, 18), (18, 24), (24, 24)):
            self.create_rectangle(x, y, x + 4, y + 4, fill="black", outline="black")

    def _bank(self):
        r = C["primary"]
        self.create_polygon(3, 11, 20, 2, 37, 11, outline=r, fill="", width=2, joinstyle="round")
        self.create_line(3, 11, 37, 11, fill=r, width=2)
        for x in (8, 14, 20, 26, 32):
            self.create_line(x, 14, x, 26, fill=r, width=3)
        self.create_line(4, 29, 36, 29, fill=r, width=2)
        self.create_line(2, 33, 38, 33, fill=r, width=3)

    def _receipt(self):
        g = C["success"]
        round_rect(self, 4, 4, 26, 26, 3, outline=g, fill="", width=2)
        self.create_rectangle(8, 8, 14, 14, outline=g, width=2)
        self.create_line(17, 9, 23, 9, fill=g, width=2)
        self.create_line(17, 13, 23, 13, fill=g, width=2)
        self.create_line(8, 18, 23, 18, fill=g, width=2)
        self.create_line(8, 22, 23, 22, fill=g, width=2)

    def _badge(self):                                  # scalloped success badge
        cx = cy = 45
        for i in range(12):
            a = i * math.pi / 6
            x, y = cx + 31 * math.cos(a), cy + 31 * math.sin(a)
            self.create_oval(x - 11, y - 11, x + 11, y + 11, fill="#3DBA55", outline="#3DBA55")
        self.create_oval(cx - 33, cy - 33, cx + 33, cy + 33, fill="#3DBA55", outline="#3DBA55")
        self.create_oval(cx - 22, cy - 22, cx + 22, cy + 22, fill="#8FD69D", outline="#8FD69D")
        self.create_line(33, 46, 42, 55, 58, 36, fill="white", width=6,
                         capstyle="round", joinstyle="round")


# ════════════════════════════ SMALL WIDGETS ════════════════════════════
class MethodCard(tk.Frame):
    """Clickable card with a radio dot. The chosen card gets a red border."""

    def __init__(self, parent, title, icon, var, value):
        super().__init__(parent, bg=C["card"], highlightthickness=2,
                         highlightbackground=EDGE, cursor="hand2")
        self.var, self.value = var, value
        head = tk.Frame(self, bg=C["card"])
        head.pack(fill="x", padx=16, pady=(10, 4))
        PayIcon(head, icon, C["card"]).pack(side="left")
        tk.Label(head, text=title, font=font(11, "bold"), fg=C["primary"],
                 bg=C["card"]).pack(side="left", padx=10)
        self.dot = tk.Canvas(head, width=22, height=22, bg=C["card"], highlightthickness=0)
        self.dot.pack(side="right")
        self.body = tk.Frame(self, bg=C["card"])
        self.body.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        var.trace_add("write", lambda *a: self.redraw())

    def activate(self):
        """Call once the body is filled: any click on the card selects it."""
        def bind(widget):
            widget.bind("<Button-1>", lambda e: self.var.set(self.value))
            for child in widget.winfo_children():
                bind(child)
        bind(self)
        self.redraw()

    def redraw(self):
        chosen = self.var.get() == self.value
        self.config(highlightbackground=C["primary"] if chosen else EDGE)
        self.dot.delete("all")
        self.dot.create_oval(3, 3, 19, 19, outline=C["primary"] if chosen else C["input_border"],
                             width=2)
        if chosen:
            self.dot.create_oval(7, 7, 15, 15, fill=C["primary"], outline=C["primary"])


def _card(parent, **pack):
    card = tk.Frame(parent, bg=C["card"], highlightthickness=1, highlightbackground=EDGE)
    card.pack(fill="x", **pack)
    return card


def _qr_picture(parent):
    """The canteen's QR (canteen_qr.png) if it exists, otherwise a drawn placeholder."""
    size = 124
    try:
        img = tk.PhotoImage(file=QR_FILE)
        short = max(img.width(), img.height())
        img = img.subsample(math.ceil(short / size)) if short > size else img.zoom(size // short)
        lbl = tk.Label(parent, image=img, bg=C["card"])
        lbl.image = img                                  # keep a reference alive
        return lbl
    except (tk.TclError, OSError):
        pass
    cv = tk.Canvas(parent, width=size, height=size, bg="#FFFFFF", highlightthickness=1,
                   highlightbackground=EDGE)
    rnd, n = random.Random(105), 25
    grid = [[rnd.random() > 0.5 for _ in range(n)] for _ in range(n)]
    for r0, c0 in ((0, 0), (0, n - 7), (n - 7, 0)):      # the three corner squares
        for r in range(-1, 8):
            for c in range(-1, 8):
                rr, cc = r0 + r, c0 + c
                if 0 <= rr < n and 0 <= cc < n:
                    edge = r in (0, 6) or c in (0, 6)
                    core = 2 <= r <= 4 and 2 <= c <= 4
                    grid[rr][cc] = 0 <= r <= 6 and 0 <= c <= 6 and (edge or core)
    cell = size // (n + 2)
    pad = (size - cell * n) // 2
    for r, row in enumerate(grid):
        for c, on in enumerate(row):
            if on:
                cv.create_rectangle(pad + c * cell, pad + r * cell, pad + (c + 1) * cell,
                                    pad + (r + 1) * cell, fill="black", outline="")
    return cv


# ════════════════════════════ PAYMENT ════════════════════════════
class PaymentPage(CustomerPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, active="cart")
        self.method = tk.StringVar(value="QR payment")
        self.total, self.order = 0.0, None        # self.order is set only when fixing a payment

        bar = tk.Frame(self.content, bg=PAGE_BG)       # buttons stay visible at the bottom
        bar.pack(side="bottom", fill="x", pady=(12, 0))
        FlatButton(bar, "◀  Back", self.go_back, kind="outline", width=130,
                   height=44).pack(side="left")
        FlatButton(bar, "Submit payment  ▶", self.submit, width=210,
                   height=44).pack(side="right")
        self.scroller = Scroller(self.content, PAGE_BG)
        self.scroller.pack(fill="both", expand=True)
        body = self.scroller.inner

        # total + order summary
        head = tk.Frame(body, bg=C["primary_soft"], highlightthickness=1,
                        highlightbackground="#EBC5C0")
        head.pack(fill="x", padx=GAP)
        left = tk.Frame(head, bg=C["primary_soft"])
        left.pack(side="left", padx=18, pady=10)
        PayIcon(left, "dollar", C["primary_soft"]).pack(side="left")
        txt = tk.Frame(left, bg=C["primary_soft"])
        txt.pack(side="left", padx=(12, 0))
        tk.Label(txt, text="Total amount to pay", font=font(9, "bold"), fg=C["ink"],
                 bg=C["primary_soft"], anchor="w").pack(anchor="w")
        self.total_lbl = tk.Label(txt, text="", font=font(20, "bold"), fg=C["primary"],
                                  bg=C["primary_soft"])
        self.total_lbl.pack(anchor="w")
        self.items_box = tk.Frame(head, bg=C["primary_soft"])
        self.items_box.pack(side="right", padx=18, pady=8)

        self.notice = tk.Frame(body, bg=PAGE_BG)       # "your journal number was rejected"
        self.notice.pack(fill="x", padx=GAP)

        # the two payment methods
        row = tk.Frame(body, bg=PAGE_BG)
        row.pack(fill="x", padx=GAP, pady=(14, 0))
        row.columnconfigure(0, weight=1, uniform="m")
        row.columnconfigure(1, weight=1, uniform="m")
        qr = MethodCard(row, "QR payment", "qr", self.method, "QR payment")
        qr.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(qr.body, text="Scan the QR code with your mobile banking app.",
                 font=font(9), fg=C["muted"], bg=C["card"], anchor="w", justify="left",
                 wraplength=250).pack(fill="x", pady=(0, 8))
        _qr_picture(qr.body).pack(anchor="w")
        qr.activate()

        acc = MethodCard(row, "Account payment", "bank", self.method, "Account payment")
        acc.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        tk.Label(acc.body, text="Transfer the amount to the college canteen account.",
                 font=font(9), fg=C["muted"], bg=C["card"], anchor="w", justify="left",
                 wraplength=250).pack(fill="x", pady=(0, 8))
        info = tk.Frame(acc.body, bg=C["card"])
        info.pack(fill="x")
        for i, (k, v) in enumerate(ACCOUNT_DETAILS):
            tk.Label(info, text=k, font=font(9), fg=C["muted"], bg=C["card"],
                     anchor="w").grid(row=i, column=0, sticky="w", pady=3)
            tk.Label(info, text=v, font=font(10, "bold"), fg=C["ink"], bg=C["card"],
                     anchor="w").grid(row=i, column=1, sticky="w", padx=(14, 0), pady=3)
        acc.activate()

        # journal number (needed for BOTH methods: it is how the canteen finds your payment)
        box = _card(body, padx=GAP, pady=(14, 0))
        inner = tk.Frame(box, bg=C["card"])
        inner.pack(fill="x", padx=20, pady=(12, 10))
        self.journal = FormField(inner, "Transaction / journal number", "e.g. 202611090012",
                                 validator=lambda v: check_journal(v)[1], on_enter=self.submit)
        self.journal.pack(fill="x")
        self.hint = tk.Label(inner, text="", font=font(9), fg=C["muted"], bg=C["card"],
                             anchor="w", justify="left", wraplength=600)
        self.hint.pack(fill="x")

    # ── showing ──
    def refresh(self):
        st = self.controller.state
        repay = st.get("repay")
        self.order = None
        for w in self.notice.winfo_children():
            w.destroy()
        if repay:                                   # fixing a rejected journal number
            order = get_order(repay["pk"])
            if order is None or not can_fix_payment(order):
                st.pop("repay", None)
                self.controller.toast("That payment can't be changed any more.")
                self.controller.show("orders")
                return
            self.order, self.total = order, order["total"]
            lines = [(i["name"], i["quantity"], i["price"]) for i in order["items"]]
            left = attempts_left(order)
            tk.Label(self.notice, bg=AMBER_SOFT, fg=AMBER, font=font(9, "bold"), anchor="w",
                     justify="left", wraplength=560, padx=14, pady=10,
                     text=f"Order {order['id']}: the canteen could not find journal number "
                          f"{order['payment']['journal']}. Enter the correct number "
                          f"({left} {'try' if left == 1 else 'tries'} left).").pack(
                fill="x", pady=(14, 0))
            self.set_header("Fix payment", f"Order {order['id']} is waiting for a correct journal number.")
        else:
            if not st["cart"]:
                self.controller.toast("Your cart is empty")
                self.controller.show("cart")
                return
            lines = [(c["name"], c["quantity"], c["price"]) for c in st["cart"]]
            self.total = sum(q * p for _, q, p in lines)
            self.set_header("Payment", "Pay first. The canteen starts your order once it "
                                       "confirms your payment.")
        self.total_lbl.config(text=money(self.total))
        for w in self.items_box.winfo_children():
            w.destroy()
        tk.Label(self.items_box, text="Order summary", font=font(9, "bold"), fg=C["primary"],
                 bg=C["primary_soft"]).grid(row=0, column=0, columnspan=2, sticky="w")
        for i, (name, qty, price) in enumerate(lines[:4], start=1):
            tk.Label(self.items_box, text=f"{name} ({qty})", font=font(9), fg=C["ink"],
                     bg=C["primary_soft"], anchor="w").grid(row=i, column=0, sticky="w", padx=(0, 22))
            tk.Label(self.items_box, text=money(qty * price), font=font(9, "bold"),
                     fg=C["ink"], bg=C["primary_soft"], anchor="e").grid(row=i, column=1, sticky="e")
        if len(lines) > 4:
            tk.Label(self.items_box, text=f"+ {len(lines) - 4} more", font=font(9), fg=C["muted"],
                     bg=C["primary_soft"]).grid(row=5, column=0, sticky="w")
        self.hint.config(
            text=f"Pay exactly {money(self.total)}, then type the journal number shown in your "
                 "banking app. The canteen checks it against its bank statement before cooking, "
                 "so a wrong number delays your order.")
        self.method.set("QR payment")
        self.journal.clear()
        self.scroller.to_top()

    # ── actions ──
    def go_back(self):
        if self.order is not None:
            self.controller.state.pop("repay", None)
            self.controller.show("orders")
        else:
            self.controller.show("cart")

    def submit(self):
        if not self.journal.validate():
            self.journal.focus()
            return
        journal, _ = check_journal(self.journal.get())
        method = self.method.get()
        if not messagebox.askyesno(
                "Check your journal number",
                f"Journal number:   {journal}\nAmount:   {money(self.total)}\n"
                f"Method:   {method}\n\nIs the journal number exactly as shown in your "
                "banking app?\nA wrong number delays your order."):
            return
        st = self.controller.state
        if self.order is None:
            order, error = place_order(st.get("email"), st.get("name", "Guest"), st["cart"],
                                       method, journal, self.total)
        else:
            error = resubmit_payment(self.order, method, journal)
            order = None if error else get_order(self.order["pk"])
        if error:
            messagebox.showwarning("Payment not sent", error)
            return
        if self.order is None:
            st["cart"].clear()
        st.pop("repay", None)
        sync_state(self.controller)
        st["last_payment"] = {
            "code": order["id"], "journal": journal, "method": method,
            "time": datetime.now().strftime("%d %B %Y, %I:%M %p"), "total": order["total"],
            "items": [(i["name"], i["quantity"], i["price"]) for i in order["items"]]}
        self.controller.show("payment_done")


# ════════════════════════════ PAYMENT SUBMITTED ════════════════════════════
class PaymentDonePage(CustomerPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, active="cart")
        self.scroller = Scroller(self.content, PAGE_BG)
        self.scroller.pack(fill="both", expand=True)
        self.body = tk.Frame(self.scroller.inner, bg=PAGE_BG)
        self.body.pack(fill="x", padx=GAP)

    def refresh(self):
        data = self.controller.state.get("last_payment")
        if not data:
            self.controller.show("orders")
            return
        self.set_header("Payment submitted", "Your order has been sent to the canteen.")
        self.scroller.to_top()
        for w in self.body.winfo_children():
            w.destroy()
        b = self.body

        top = tk.Frame(b, bg=PAGE_BG)
        top.pack(pady=(4, 0))
        PayIcon(top, "badge", PAGE_BG).pack()
        tk.Label(top, text="Payment submitted!", font=font(20, "bold"), fg=C["success"],
                 bg=PAGE_BG).pack(pady=(6, 2))
        tk.Label(top, text="The canteen will check your journal number and then start "
                           "preparing your order.", font=font(10), fg=C["muted"],
                 bg=PAGE_BG).pack()

        panels = tk.Frame(b, bg=PAGE_BG)
        panels.pack(fill="x", pady=(16, 0))
        panels.columnconfigure(0, weight=1, uniform="p")
        panels.columnconfigure(1, weight=1, uniform="p")

        pay = tk.Frame(panels, bg=C["card"], highlightthickness=1, highlightbackground=EDGE)
        pay.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(pay, text="Payment summary", font=font(11, "bold"), fg=C["success"],
                 bg=C["card"]).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 8))
        rows = (("Order no.", data["code"]), ("Journal no.", data["journal"]),
                ("Payment", data["method"]), ("Date & time", data["time"]),
                ("Amount paid", money(data["total"])),
                ("Status", "Waiting for the canteen to confirm"))
        for i, (k, v) in enumerate(rows, start=1):
            tk.Label(pay, text=k, font=font(9), fg=C["muted"], bg=C["card"],
                     anchor="w").grid(row=i, column=0, sticky="nw", padx=(16, 8), pady=3)
            tk.Label(pay, text=v, font=font(10, "bold"), fg=C["ink"], bg=C["card"], anchor="w",
                     justify="left", wraplength=240).grid(row=i, column=1, sticky="w", padx=(0, 16), pady=3)
        tk.Frame(pay, height=10, bg=C["card"]).grid(row=len(rows) + 1, column=0)

        order = tk.Frame(panels, bg=C["card"], highlightthickness=1, highlightbackground=EDGE)
        order.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        order.columnconfigure(0, weight=1)
        tk.Label(order, text="Order summary", font=font(11, "bold"), fg=C["success"],
                 bg=C["card"]).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 8))
        r = 1
        for name, qty, price in data["items"]:
            tk.Label(order, text=f"{name} ({qty})", font=font(10), fg=C["ink"], bg=C["card"],
                     anchor="w").grid(row=r, column=0, sticky="w", padx=16, pady=2)
            tk.Label(order, text=money(qty * price), font=font(10), fg=C["ink"], bg=C["card"],
                     anchor="e").grid(row=r, column=1, sticky="e", padx=16, pady=2)
            r += 1
        tk.Frame(order, height=1, bg=EDGE).grid(row=r, column=0, columnspan=2, sticky="ew",
                                                padx=16, pady=8)
        tk.Label(order, text="Total amount paid", font=font(10, "bold"), fg=C["ink"],
                 bg=C["card"]).grid(row=r + 1, column=0, sticky="w", padx=16, pady=(0, 14))
        tk.Label(order, text=money(data["total"]), font=font(10, "bold"), fg=C["success"],
                 bg=C["card"]).grid(row=r + 1, column=1, sticky="e", padx=16, pady=(0, 14))

        note = tk.Frame(b, bg=GREEN_SOFT)
        note.pack(fill="x", pady=(14, 0))
        PayIcon(note, "receipt", GREEN_SOFT).pack(side="left", padx=(14, 8), pady=12)
        tk.Label(note, bg=GREEN_SOFT, fg=C["ink"], font=font(9), justify="left", anchor="w",
                 wraplength=520,
                 text="You will get a notification (pop-up and bell) when the canteen confirms "
                      "your payment, and again when your order is ready. If the journal number "
                      "can't be found, you can correct it in My Order (up to "
                      f"{MAX_ATTEMPTS} tries). You can cancel only while the order is "
                      "Pending.").pack(side="left", padx=(0, 14), pady=12)

        btns = tk.Frame(b, bg=PAGE_BG)
        btns.pack(pady=(16, 8))
        FlatButton(btns, "Track my order", lambda: self.controller.show("orders"),
                   width=170, height=44).pack(side="left", padx=6)
        FlatButton(btns, "Back to Dashboard", lambda: self.controller.show("dashboard"),
                   kind="outline", width=180, height=44).pack(side="left", padx=6)


if __name__ == "__main__":
    import main
    main.App("payment").mainloop()
