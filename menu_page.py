"""Menu screens: Menu (all items) and, via subclasses, Veg / Non-Veg / Beverage.

Built on CustomerPage so the sidebar, Log Out, the user chip and the cart all
work exactly like the rest of the app. Data comes from menu_data.MENU_ITEMS.
"""
import tkinter as tk
from tkinter import ttk

from main import C, font
from dashboard import EDGE, PAGE_BG, CustomerPage
from check_availability import DataTable
import menu_data
from menu_data import MENU_ITEMS, money
from ui_helpers import button_cell, chip, text_cell

COLUMNS = [("Food Item", 4, "w"), ("Category", 2, "w"), ("Price", 2, "w"),
           ("Status", 2, "w"), ("", 2, "e")]

# tab label -> (page name, category filter)
TABS = (("All", "menu", None), ("Veg", "veg", "Veg"),
        ("Non-Veg", "non_veg", "Non-Veg"), ("Beverage", "beverage", "Beverage"))


class MenuPage(CustomerPage):
    def __init__(self, parent, controller, category=None):
        super().__init__(parent, controller, active="menu")
        self.category = category

        bar = tk.Frame(self.content, bg=PAGE_BG)
        bar.pack(fill="x")
        # category tabs (each one opens its own screen)
        for label, page, cat in TABS:
            on = cat == category
            tab = tk.Label(bar, text=label, font=font(10, "bold"), cursor="hand2",
                           fg="#FFFFFF" if on else C["ink"],
                           bg=C["primary"] if on else C["card"], padx=16, pady=7,
                           highlightthickness=1,
                           highlightbackground=C["primary"] if on else EDGE)
            tab.pack(side="left", padx=(0, 8))
            tab.bind("<Button-1>", lambda e, p=page: controller.show(p))

        self.cart_link = tk.Label(bar, text="", font=font(10, "bold"), fg=C["primary"],
                                  bg=PAGE_BG, cursor="hand2")
        self.cart_link.pack(side="right")
        self.cart_link.bind("<Button-1>", lambda e: controller.show("cart"))

        tools = tk.Frame(self.content, bg=PAGE_BG)
        tools.pack(fill="x", pady=(12, 12))
        tk.Label(tools, text="Search", font=font(9, "bold"), fg=C["muted"],
                 bg=PAGE_BG).pack(side="left")
        self.search = tk.StringVar()
        box = tk.Frame(tools, bg="#FFFFFF", highlightthickness=1, highlightbackground=EDGE)
        box.pack(side="left", padx=(8, 22))
        tk.Entry(box, textvariable=self.search, width=24, relief="flat", font=font(10),
                 bg="#FFFFFF", fg=C["ink"], insertbackground=C["ink"]).pack(padx=8, pady=6)
        tk.Label(tools, text="Quantity", font=font(9, "bold"), fg=C["muted"],
                 bg=PAGE_BG).pack(side="left")
        self.qty = ttk.Combobox(tools, values=[str(n) for n in range(1, 11)], width=4,
                                state="readonly", font=font(10))
        self.qty.set("1")
        self.qty.pack(side="left", padx=8)
        self.search.trace_add("write", lambda *a: self.render())

        self.table = DataTable(self.content, COLUMNS, empty_text="No items match your search.",
                               light_header=False)
        self.table.pack(fill="both", expand=True)

    # -- data
    def items(self):
        term = self.search.get().strip().lower()
        return [i for i in MENU_ITEMS
                if (self.category is None or i["category"] == self.category)
                and (term in i["name"].lower() or term in i["category"].lower())]

    def refresh(self):
        title = "Today's Menu" if self.category is None else f"{self.category} Menu"
        self.set_header(title, "Choose your favourite food and add it to your cart.")
        menu_data.reload()                      # the manager may have changed the menu
        self.search.set("")
        self.qty.set("1")
        self.render()

    def render(self):
        n = sum(c["quantity"] for c in self.controller.state["cart"])
        self.cart_link.config(text=f"🛒 My Cart ({n})  →")
        rows = []
        for item in self.items():
            ok = item.get("available", True)
            rows.append([text_cell(item["name"], bold=True), item["category"],
                         money(item["price"]), chip("Available" if ok else "Sold out"),
                         button_cell("Add to Cart", lambda i=item: self.add(i)) if ok
                         else text_cell("—", anchor="e")])
        self.table.set_rows(rows)

    def add(self, item):
        self.controller.add_to_cart(item["name"], self.qty.get())
        self.render()


if __name__ == "__main__":
    import main
    main.App("menu").mainloop()
