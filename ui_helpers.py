"""Small widgets reused by the menu, cart, orders and admin screens."""
import tkinter as tk

from main import C, font
from orders_store import payment_label

GREEN, GREEN_SOFT = "#12A150", "#E7F8EF"
AMBER, AMBER_SOFT = "#9A5B00", "#FFF1D6"
BLUE, BLUE_SOFT = "#1D5FA8", "#E4F0FC"
GREY, GREY_SOFT = "#666666", "#EFEFEF"
RED, RED_SOFT = C["primary"], "#FDE8E6"

STATUS_COLOURS = {
    "Pending": (AMBER, AMBER_SOFT), "Preparing": (BLUE, BLUE_SOFT),
    "Ready": (GREEN, GREEN_SOFT), "Completed": (GREY, GREY_SOFT),
    "Cancelled": (RED, RED_SOFT), "Available": (GREEN, GREEN_SOFT),
    "Sold out": (RED, RED_SOFT),
    # payment states (see orders_store.PAYMENT_LABELS)
    "Checking": (AMBER, AMBER_SOFT), "Verified": (GREEN, GREEN_SOFT),
    "Rejected": (RED, RED_SOFT), "Refund due": (RED, RED_SOFT),
    "Refunded": (GREY, GREY_SOFT),
}


def chip(text):
    """Cell factory for DataTable: a small coloured status pill."""
    fg, bg = STATUS_COLOURS.get(text, (GREY, GREY_SOFT))

    def make(parent):
        return tk.Label(parent, text=text.upper(), font=font(8, "bold"), fg=fg, bg=bg,
                        padx=8, pady=2)
    return make


def text_cell(text, bold=False, fg=None, anchor="w"):
    def make(parent):
        return tk.Label(parent, text=text, font=font(10, "bold" if bold else "normal"),
                        fg=fg or C["ink"], bg=C["card"], anchor=anchor)
    return make


def wrap_cell(text, wrap=120):
    """Text that wraps onto more lines instead of being cut off."""
    def make(parent):
        return tk.Label(parent, text=text, font=font(10), fg=C["ink"], bg=C["card"],
                        anchor="w", justify="left", wraplength=wrap)
    return make


def two_line_cell(top, *rest):
    """Bold first line with small grey lines under it (e.g. order number, customer, time)."""
    def make(parent):
        f = tk.Frame(parent, bg=C["card"])
        tk.Label(f, text=top, font=font(10, "bold"), fg=C["ink"], bg=C["card"],
                 anchor="w").pack(anchor="w")
        for i, line in enumerate(rest):
            tk.Label(f, text=line, font=font(8), fg=C["muted"], bg=C["card"], anchor="w",
                     justify="left", wraplength=115).pack(anchor="w", pady=(3 if i == 0 else 0, 0))
        return f
    return make


def mini_button(parent, text, command, kind="primary"):
    """Compact clickable label used inside table rows."""
    fg, bg, hover = {"primary": ("#FFFFFF", C["primary"], "#A8160F"),
                     "soft": (C["primary"], C["primary_soft"], "#F5D9D5"),
                     "dark": ("#FFFFFF", C["ink"], "#000000")}[kind]
    b = tk.Label(parent, text=text, font=font(9, "bold"), fg=fg, bg=bg,
                 padx=12, pady=5, cursor="hand2")
    b.bind("<Enter>", lambda e: b.config(bg=hover))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    b.bind("<Button-1>", lambda e: command())
    return b


def button_cell(text, command, kind="primary"):
    return lambda parent: mini_button(parent, text, command, kind)


def buttons_cell(*specs):
    """Several mini buttons side by side: specs are (text, command, kind)."""
    def make(parent):
        f = tk.Frame(parent, bg=C["card"])
        for text, command, kind in specs:
            mini_button(f, text, command, kind).pack(side="left", padx=(6, 0))
        return f
    return make


def stacked_buttons_cell(*specs):
    """Several mini buttons one above the other (for narrow table columns)."""
    def make(parent):
        f = tk.Frame(parent, bg=C["card"])
        for text, command, kind in specs:
            mini_button(f, text, command, kind).pack(fill="x", pady=2)
        return f
    return make


def payment_cell(order):
    """Payment status chip with the journal number written under it."""
    pay = order.get("payment")

    def make(parent):
        f = tk.Frame(parent, bg=C["card"])
        if pay is None:
            tk.Label(f, text="—", font=font(10), fg=C["muted"], bg=C["card"]).pack(anchor="w")
            return f
        chip(payment_label(pay["status"]))(f).pack(anchor="w")
        tk.Label(f, text=f"Journal {pay['journal']}", font=font(8), fg=C["muted"],
                 bg=C["card"], anchor="w", justify="left",
                 wraplength=125).pack(anchor="w", pady=(3, 0))
        return f
    return make


def stat_card(parent, label, bg=None):
    """A KPI tile; returns (frame, value_label) so the caller can update the number."""
    card = tk.Frame(parent, bg=C["card"], highlightthickness=1, highlightbackground="#EEDFDA")
    tk.Label(card, text=label, font=font(9, "bold"), fg=C["muted"], bg=C["card"],
             anchor="w").pack(fill="x", padx=18, pady=(16, 0))
    value = tk.Label(card, text="0", font=font(26, "bold"), fg=C["primary"], bg=C["card"],
                     anchor="w")
    value.pack(fill="x", padx=18, pady=(2, 16))
    return card, value
