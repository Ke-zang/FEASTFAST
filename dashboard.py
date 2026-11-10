"""Customer Dashboard + shared customer shell.

CustomerPage  - base class: dark sidebar (active highlight), top bar with page
                title + user chip, and a content area (self.content). Every
                customer screen (menu, cart, orders, reservation, profile)
                should subclass it and override refresh() if it shows live data.
DashboardPage - the screen customers land on after login.
SectionPage   - temporary "coming soon" screen so every sidebar link works
                until the real screen is built.
"""
import tkinter as tk
from datetime import datetime

import menu_data
from main import (C, MENU_ITEMS, FlatButton, Icon, Logo, Page, font, get_customer,
                  load_avatar, round_rect)
from notifications import NotificationBell

SIDEBAR = "#1C1C1C"
SIDEBAR_HOVER = "#2A2A2A"
SIDEBAR_ACTIVE = "#2F2F2F"
PAGE_BG = "#FBF3F0"
EDGE = "#EEDFDA"

# (page name, label, icon)  -> page names must exist in main.PAGES
NAV = (
    ("dashboard", "Dashboard", "home"),
    ("menu", "Menu", "menu"),
    ("cart", "My Cart", "cart"),
    ("orders", "My Order", "order"),
    ("reservation", "Reservation", "table"),
    ("profile", "Profile", "user"),
    ("about", "About Us", "info"),
)


# ════════════════════════════ SHELL ════════════════════════════
class NavItem(tk.Frame):
    def __init__(self, parent, text, icon, command, active=False):
        self.active = active
        self._base = SIDEBAR_ACTIVE if active else SIDEBAR
        super().__init__(parent, bg=self._base, cursor="hand2")
        self.bar = tk.Frame(self, width=4, bg=C["primary"] if active else self._base)
        self.bar.pack(side="left", fill="y")
        self.icon = Icon(self, icon, 20, "#FFFFFF", self._base)
        self.icon.pack(side="left", padx=(18, 12), pady=12)
        self.label = tk.Label(self, text=text, fg="#FFFFFF", bg=self._base,
                              font=font(11, "bold" if active else "normal"))
        self.label.pack(side="left")
        for w in (self, self.icon, self.label, self.bar):
            w.bind("<Enter>", lambda e: self._paint(SIDEBAR_HOVER if not self.active
                                                    else SIDEBAR_ACTIVE))
            w.bind("<Leave>", lambda e: self._paint(self._base))
            w.bind("<Button-1>", lambda e: command())

    def _paint(self, bg):
        for w in (self, self.icon, self.label):
            w.config(bg=bg)
        if not self.active:
            self.bar.config(bg=bg)


class Avatar(tk.Canvas):
    def __init__(self, parent, size=40, bg=PAGE_BG):
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0)
        self.size = size
        self.set("?")

    def set(self, letter, photo=None):
        """Show a photo (cropped to a circle) or, without one, the initial."""
        self.delete("all")
        s = self.size
        if photo is not None:
            self._img = photo                      # keep a reference alive
            self.create_image(s / 2, s / 2, image=photo)
            # a thick ring in the background colour masks the square corners
            self.create_oval(-s / 2, -s / 2, s * 1.5, s * 1.5, outline=self["bg"],
                             width=s)
            return
        self.create_oval(1, 1, s - 1, s - 1, fill=C["primary"], outline="")
        self.create_text(s / 2, s / 2, text=letter.upper(), fill="#FFFFFF",
                         font=font(max(10, int(s * 0.36)), "bold"))


class CustomerPage(Page):
    """Sidebar + top bar + content area. Put screen content into self.content."""

    def __init__(self, parent, controller, active="dashboard"):
        super().__init__(parent, controller)
        self.active = active

        # sidebar
        side = tk.Frame(self, bg=SIDEBAR, width=220)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        brand = tk.Frame(side, bg=SIDEBAR, cursor="hand2")
        brand.pack(fill="x", padx=20, pady=(24, 28))
        Logo(brand, size=40, bg=SIDEBAR, color=C["accent_on_dark"]).pack(side="left")
        tk.Label(brand, text="Feast\nFast", justify="left", fg="#FFFFFF", bg=SIDEBAR,
                 font=font(11, "bold")).pack(side="left", padx=10)
        for w in (brand, *brand.winfo_children()):
            w.bind("<Button-1>", lambda e: controller.show("dashboard"))
        for target, label, icon in NAV:
            NavItem(side, label, icon, lambda t=target: controller.show(t),
                    active=(target == active)).pack(fill="x", pady=1)
        FlatButton(side, "Log Out", controller.logout, size=10, height=40,
                   bg=SIDEBAR).pack(side="bottom", fill="x", padx=22, pady=26)

        # main column: top bar + content
        main = tk.Frame(self, bg=PAGE_BG)
        main.pack(side="left", fill="both", expand=True)
        top = tk.Frame(main, bg=PAGE_BG)
        top.pack(fill="x", padx=32, pady=(22, 0))
        titles = tk.Frame(top, bg=PAGE_BG)
        titles.pack(side="left")
        self.title_lbl = tk.Label(titles, text="", font=font(20, "bold"), fg=C["ink"],
                                  bg=PAGE_BG, anchor="w")
        self.title_lbl.pack(anchor="w")
        self.sub_lbl = tk.Label(titles, text="", font=font(10), fg=C["muted"],
                                bg=PAGE_BG, anchor="w")
        self.sub_lbl.pack(anchor="w")

        chip = tk.Frame(top, bg=PAGE_BG)
        chip.pack(side="right")
        self.bell = NotificationBell(top, controller, PAGE_BG)
        self.bell.pack(side="right", padx=(0, 18))
        self.avatar = Avatar(chip)
        self.avatar.pack(side="left")
        who = tk.Frame(chip, bg=PAGE_BG)
        who.pack(side="left", padx=(10, 0))
        self.name_lbl = tk.Label(who, text="", font=font(10, "bold"), fg=C["ink"],
                                 bg=PAGE_BG, anchor="w")
        self.name_lbl.pack(anchor="w")
        tk.Label(who, text="Customer", font=font(9), fg=C["muted"], bg=PAGE_BG,
                 anchor="w").pack(anchor="w")

        self.content = tk.Frame(main, bg=PAGE_BG)
        self.content.pack(fill="both", expand=True, padx=32, pady=(18, 20))

    # -- helpers
    @property
    def customer_name(self):
        return self.controller.state.get("name", "Guest")

    def set_header(self, title, subtitle=""):
        self.title_lbl.config(text=title)
        self.sub_lbl.config(text=subtitle or " ")

    def section_header(self, text, link=None, command=None, pady=(22, 10)):
        row = tk.Frame(self.content, bg=PAGE_BG)
        row.pack(fill="x", pady=pady)
        tk.Label(row, text=text, font=font(13, "bold"), fg=C["ink"], bg=PAGE_BG).pack(side="left")
        if link:
            lbl = tk.Label(row, text=link, font=font(9, "bold"), fg=C["primary"],
                           bg=PAGE_BG, cursor="hand2")
            lbl.pack(side="right")
            lbl.bind("<Button-1>", lambda e: command())
        return row

    def on_show(self, name=None, email=None, **kwargs):
        st = self.controller.state
        if email:                                   # fresh login: remember who
            record = get_customer(email) or {}
            st.update(email=email.strip().lower(), photo=record.get("photo"), role="customer",
                      session_version=record.get("session_version", 0))
        if name:
            st["name"] = name
        if st.get("email"):                         # still a valid session?
            record = get_customer(st["email"])
            if record is None or record.get("session_version", 0) != st["session_version"]:
                self.controller.logout("You were signed out on another device.")
                return
        self.refresh_user()
        self.refresh()

    def refresh_user(self):
        """Update the name + avatar chip in the top bar."""
        shown = self.customer_name
        self.name_lbl.config(text=shown)
        self.bell.update_count()
        self.avatar.set(shown.strip()[:1] or "?",
                        load_avatar(self.controller.state.get("photo"), 40))

    def refresh(self):
        """Override to update live data every time the page is shown."""


# ════════════════════════════ DASHBOARD WIDGETS ════════════════════════════
class Hero(tk.Canvas):
    H = 150

    def __init__(self, parent, command):
        super().__init__(parent, height=self.H, bg=PAGE_BG, highlightthickness=0)
        btn = FlatButton(self, "BROWSE MENU", command, kind="light", size=9,
                         width=150, height=38, bg=C["primary"])
        self.create_window(30, self.H - 22, window=btn, anchor="sw")
        self.bind("<Configure>", self._draw)

    def _draw(self, e):
        w, h = e.width, self.H
        self.delete("deco")
        round_rect(self, 0, 0, w, h, 18, fill=C["primary"], outline="", tags="deco")
        cx, cy = w - 110, h / 2
        self.create_oval(cx - 62, cy - 62, cx + 62, cy + 62, fill="#CF2019",
                         outline="", tags="deco")
        self.create_oval(cx - 44, cy - 44, cx + 44, cy + 44, fill="#FFFFFF",
                         outline="", tags="deco")
        self.create_oval(cx - 32, cy - 32, cx + 32, cy + 32, fill="#FBE3E1",
                         outline="", tags="deco")
        for dx, dy, r, col in ((-10, -8, 9, "#F5DDB0"), (12, -4, 9, "#F5DDB0"),
                               (-2, 12, 9, "#F5DDB0"), (6, 4, 4, C["primary"])):
            self.create_oval(cx + dx - r, cy + dy - r, cx + dx + r, cy + dy + r,
                             fill=col, outline="", tags="deco")
        self.create_oval(cx - 150, cy + 10, cx - 120, cy + 40, outline="#CF2019",
                         width=3, tags="deco")
        self.create_text(30, 24, text="Skip the Queue.", anchor="nw", fill="#FFFFFF",
                         font=font(24, "bold"), tags="deco")
        self.create_text(30, 68, text="Order ahead and collect your food when it's ready.",
                         anchor="nw", fill="#FDE8E6", font=font(10), tags="deco")
        self.tag_lower("deco")


class ActionCard(tk.Frame):
    """Clickable Quick Action tile with a live count badge."""

    def __init__(self, parent, icon, title, subtitle, command):
        super().__init__(parent, bg=C["card"], cursor="hand2",
                         highlightthickness=1, highlightbackground=EDGE)
        inner = tk.Frame(self, bg=C["card"], cursor="hand2")
        inner.pack(fill="both", expand=True, padx=18, pady=16)
        top = tk.Frame(inner, bg=C["card"], cursor="hand2")
        top.pack(fill="x")
        tile = tk.Frame(top, bg=C["primary_soft"], width=46, height=46)
        tile.pack(side="left")
        tile.pack_propagate(False)
        ic = Icon(tile, icon, 26, C["primary"], C["primary_soft"], lw=2)
        ic.place(relx=0.5, rely=0.5, anchor="center")
        self.badge = tk.Label(top, text="", font=font(9, "bold"), fg=C["primary"],
                              bg=C["primary_soft"], padx=9, pady=3)
        self.badge.pack(side="right", anchor="n")
        t = tk.Label(inner, text=title, font=font(12, "bold"), fg=C["ink"],
                     bg=C["card"], anchor="w")
        t.pack(fill="x", pady=(12, 0))
        s = tk.Label(inner, text=subtitle, font=font(9), fg=C["muted"],
                     bg=C["card"], anchor="w")
        s.pack(fill="x")
        for w in (self, inner, top, tile, ic, t, s, self.badge):
            w.bind("<Enter>", lambda e: self.config(highlightbackground=C["primary"]))
            w.bind("<Leave>", lambda e: self.config(highlightbackground=EDGE))
            w.bind("<Button-1>", lambda e: command())


class DishCard(tk.Frame):
    def __init__(self, parent, item, command):
        super().__init__(parent, bg=C["card"], cursor="hand2",
                         highlightthickness=1, highlightbackground=EDGE)
        art = tk.Canvas(self, height=62, bg=item["tint"], highlightthickness=0,
                        cursor="hand2")
        art.pack(fill="x")

        def draw(e):
            art.delete("all")
            cx, cy = e.width / 2, 31
            art.create_oval(cx - 24, cy - 24, cx + 24, cy + 24, fill="#FFFFFF", outline="")
            art.create_oval(cx - 16, cy - 16, cx + 16, cy + 16, fill=item["dot"], outline="")
            art.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill="#FFFFFF", outline="")
        art.bind("<Configure>", draw)

        row = tk.Frame(self, bg=C["card"], cursor="hand2")
        row.pack(fill="x", padx=12, pady=(9, 0))
        name = tk.Label(row, text=item["name"], font=font(10, "bold"), fg=C["ink"],
                        bg=C["card"], anchor="w")
        name.pack(side="left")
        cat = tk.Label(self, text=item["category"], font=font(9), fg=C["muted"],
                       bg=C["card"], anchor="w")
        cat.pack(fill="x", padx=12)
        price = tk.Label(self, text=f"Nu. {item['price']}", font=font(10, "bold"),
                         fg=C["primary"], bg=C["card"], anchor="w")
        price.pack(fill="x", padx=12, pady=(2, 10))
        for w in (self, art, row, name, cat, price):
            w.bind("<Enter>", lambda e: self.config(highlightbackground=C["primary"]))
            w.bind("<Leave>", lambda e: self.config(highlightbackground=EDGE))
            w.bind("<Button-1>", lambda e: command())


# ════════════════════════════ DASHBOARD ════════════════════════════
class DashboardPage(CustomerPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, active="dashboard")
        c = self.content
        Hero(c, lambda: controller.show("menu")).pack(fill="x")

        self.section_header("Quick Actions")
        grid = tk.Frame(c, bg=PAGE_BG)
        grid.pack(fill="x")
        self.cards = {}
        for i, (key, icon, title, sub, target) in enumerate((
                ("cart", "menu", "Order Food", "Browse today's menu", "menu"),
                ("reservations", "table", "Reserve Table", "Book a table", "reservation"),
                ("orders", "order", "Track Order", "Check your order status", "orders"))):
            card = ActionCard(grid, icon, title, sub,
                              lambda t=target: controller.show(t))
            self._cell(grid, card, i, 3, 16)
            self.cards[key] = card

        self.section_header("Popular Today", "View full menu  →",
                            lambda: controller.show("menu"), pady=(24, 10))
        self.dishes = tk.Frame(c, bg=PAGE_BG)
        self.dishes.pack(fill="x")

    @staticmethod
    def _cell(grid, widget, i, count, gap):
        """Place widget in an equal-width column separated by fixed gap columns."""
        grid.columnconfigure(i * 2, weight=1, uniform="cell")
        if i < count - 1:
            grid.columnconfigure(i * 2 + 1, minsize=gap)
        widget.grid(row=0, column=i * 2, sticky="nsew")

    def _fill_dishes(self):
        menu_data.reload()
        for w in self.dishes.winfo_children():
            w.destroy()
        for i, item in enumerate([m for m in MENU_ITEMS if m.get('available', True)][:4]):
            self._cell(self.dishes, DishCard(self.dishes, item,
                                             lambda: self.controller.show("menu")), i, 4, 14)

    def refresh(self):
        self._fill_dishes()
        now = datetime.now()
        part = "morning" if now.hour < 12 else "afternoon" if now.hour < 17 else "evening"
        parts = self.customer_name.strip().split()
        first = parts[0].title() if parts else "Guest"
        self.set_header(f"Good {part}, {first}", now.strftime("%A, %d %B  •  What would you like to eat today?"))
        from check_availability import sync_state as sync_bookings   # local: avoids a cycle
        from orders_store import sync_state as sync_orders
        sync_bookings(self.controller)
        sync_orders(self.controller)
        st = self.controller.state
        self.cards["cart"].badge.config(text=f"{sum(c['quantity'] for c in st['cart'])} in cart")
        self.cards["reservations"].badge.config(text=f"{sum(b['status'] == 'RESERVED' for b in st['reservations'])} booked")
        self.cards["orders"].badge.config(text=f"{len(st['orders'])} active")


# ════════════════════════════ PLACEHOLDER SECTIONS ════════════════════════════
class SectionPage(CustomerPage):
    """Stand-in for screens that are not built yet (menu, cart, ...)."""

    def __init__(self, parent, controller, key="menu", title="Menu", blurb="", icon="menu"):
        super().__init__(parent, controller, active=key)
        self.set_header(title, "This section is under construction.")
        card = tk.Frame(self.content, bg=C["card"], highlightthickness=1,
                        highlightbackground=EDGE)
        card.pack(fill="x", pady=(8, 0))
        body = tk.Frame(card, bg=C["card"])
        body.pack(padx=30, pady=44)
        tile = tk.Frame(body, bg=C["primary_soft"], width=76, height=76)
        tile.pack()
        tile.pack_propagate(False)
        Icon(tile, icon, 38, C["primary"], C["primary_soft"], lw=3).place(
            relx=0.5, rely=0.5, anchor="center")
        tk.Label(body, text=f"{title} is coming soon", font=font(15, "bold"),
                 fg=C["ink"], bg=C["card"]).pack(pady=(18, 4))
        tk.Label(body, text=blurb, font=font(10), fg=C["muted"], bg=C["card"],
                 wraplength=420, justify="center").pack()
        FlatButton(body, "BACK TO DASHBOARD", lambda: controller.show("dashboard"),
                   size=9, width=190, height=42).pack(pady=(22, 0))


if __name__ == "__main__":
    import main
    main.App("dashboard").mainloop()
