"""Customer screen: My Cart (page name: "cart").

Reads state["cart"] (filled by the Menu screens). "Proceed to Payment" opens the
Payment screen: the order is only created (and the manager only sees it) once the
customer has paid. A sold-out item is caught here, BEFORE the customer pays.
"""
import tkinter as tk

from main import C, FlatButton, font
from dashboard import PAGE_BG, CustomerPage
from check_availability import DataTable
from menu_data import money
from orders_store import cart_problem
from ui_helpers import button_cell, buttons_cell, text_cell

COLUMNS = [("Food Item", 4, "w"), ("Price", 2, "w"), ("Quantity", 3, "w"),
           ("Subtotal", 2, "w"), ("", 2, "e")]


class CartPage(CustomerPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, active="cart")
        self.table = DataTable(self.content, COLUMNS,
                               empty_text="Your cart is empty. Browse the menu to add food.")
        self.table.pack(fill="both", expand=True)

        foot = tk.Frame(self.content, bg=PAGE_BG)
        foot.pack(fill="x", pady=(14, 0))
        self.total = tk.Label(foot, text="", font=font(15, "bold"), fg=C["ink"], bg=PAGE_BG)
        self.total.pack(side="left")
        FlatButton(foot, "Proceed to Payment", self.submit, width=200, height=44).pack(side="right")
        FlatButton(foot, "Add more items", lambda: controller.show("menu"), kind="outline",
                   width=160, height=44).pack(side="right", padx=12)

    @property
    def cart(self):
        return self.controller.state["cart"]

    def refresh(self):
        self.set_header("My Cart", "Review the items you've added, then pay to place your order.")
        self.render()

    def render(self):
        rows = []
        for line in self.cart:
            rows.append([
                text_cell(line["name"], bold=True), money(line["price"]),
                buttons_cell(("−", lambda l=line: self.change(l, -1), "soft"),
                             (str(line["quantity"]), lambda: None, "dark"),
                             ("+", lambda l=line: self.change(l, +1), "soft")),
                money(line["price"] * line["quantity"]),
                button_cell("Remove", lambda l=line: self.remove(l), "soft")])
        self.table.set_rows(rows)
        total = sum(c["price"] * c["quantity"] for c in self.cart)
        self.total.config(text=f"Total: {money(total)}")

    def change(self, line, delta):
        line["quantity"] += delta
        if line["quantity"] <= 0:
            self.cart.remove(line)
        self.render()

    def remove(self, line):
        self.cart.remove(line)
        self.render()

    def submit(self):
        if not self.cart:
            self.controller.toast("Your cart is empty")
            return
        problem = cart_problem(self.cart)          # e.g. an item was just marked sold out
        if problem:
            self.controller.toast(problem, ms=4500)
            return
        self.controller.state.pop("repay", None)   # a normal payment, not a "fix payment"
        self.controller.show("payment")


if __name__ == "__main__":
    import main
    main.App("cart").mainloop()
