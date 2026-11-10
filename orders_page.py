"""Customer screen: My Order (page name: "orders").

Cancel rules:
  * Pending            -> Cancel button. If the order was already paid, the money is
                          refunded BY HAND: the customer phones the manager (number on
                          the About Us page). The manager then marks it Refunded.
  * Preparing / Ready  -> locked, can't be cancelled.
Fix payment: if the manager could not find the journal number, the customer can type
another one (a few tries, see orders_store.MAX_ATTEMPTS).
"""
from tkinter import messagebox

from main import C
from dashboard import CustomerPage
from check_availability import DataTable
from menu_data import money
from orders_store import (MANAGER_PHONE, attempts_left, can_fix_payment, cancel_order,
                          orders_for, payment_status, summary, sync_state)
from ui_helpers import (button_cell, chip, payment_cell, stacked_buttons_cell, text_cell,
                        two_line_cell, wrap_cell)

COLUMNS = [("Order", 4, "w"), ("Items", 4, "w"), ("Total", 3, "w"), ("Payment", 5, "w"),
           ("Status", 4, "w"), ("", 5, "e")]


class OrdersPage(CustomerPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, active="orders")
        self.table = DataTable(self.content, COLUMNS,
                               empty_text="You haven't placed an order yet.")
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        self.set_header("My Order", "Track your current order and see your past orders.")
        rows = []
        for o in orders_for(self.controller.state.get("email")):
            rows.append([two_line_cell(o["id"], o["placed"]), wrap_cell(summary(o, 80), 100),
                         money(o["total"]), payment_cell(o), chip(o["status"]), self.action(o)])
        self.table.set_rows(rows)

    def action(self, o):
        pay = payment_status(o)
        if o["status"] == "Pending":
            specs = []
            if can_fix_payment(o):
                specs.append(("Fix payment", lambda o=o: self.fix_payment(o), "primary"))
            elif pay == "Rejected":                      # no tries left
                specs.append(("Call manager", lambda o=o: self.call_help(o), "primary"))
            specs.append(("Cancel", lambda o=o: self.cancel(o), "soft"))
            return stacked_buttons_cell(*specs)
        if o["status"] == "Cancelled" and pay == "Refund due":
            return button_cell("How to get refund", lambda o=o: self.refund_help(o), "soft")
        if o["status"] in ("Preparing", "Ready"):        # the rule: locked once preparing
            return text_cell("Can't cancel now", fg=C["muted"], anchor="e")
        return text_cell("", anchor="e")

    # ── actions ──
    def cancel(self, order):
        paid = payment_status(order) in ("Submitted", "Verified")
        text = f"Cancel order {order['id']}?"
        if paid:
            text += (f"\n\nYou have already paid {money(order['total'])}. Refunds are done by "
                     f"hand: after cancelling, call the manager on {MANAGER_PHONE} "
                     "(it is also on the About Us page).")
        if not messagebox.askyesno("Cancel order", text):
            return
        refund, error = cancel_order(order)          # the database decides: Pending only
        sync_state(self.controller)
        if error:
            self.controller.toast(error)
        elif refund:
            self.refund_help(order, cancelled_now=True)
        else:
            self.controller.toast(f"Order {order['id']} cancelled — the canteen has been told")
        self.refresh()

    def refund_help(self, order, cancelled_now=False):
        pay = order["payment"]
        head = (f"Order {order['id']} is cancelled." if cancelled_now
                else f"Order {order['id']} was cancelled and your payment is waiting for a refund.")
        messagebox.showinfo(
            "Get your refund",
            f"{head}\n\nTo get your {money(order['total'])} back, call the manager on "
            f"{MANAGER_PHONE} and tell them:\n   • order number {order['id']}\n"
            f"   • journal number {pay['journal']}\n\n"
            "You will get a notification when the refund has been sent.")

    def call_help(self, order):
        messagebox.showinfo(
            "Payment problem",
            f"The canteen could not find your payment for order {order['id']} and you have "
            f"no tries left.\n\nPlease call the manager on {MANAGER_PHONE} with your "
            f"journal number ({order['payment']['journal']}). "
            "If you did not pay, you can cancel this order.")

    def fix_payment(self, order):
        if attempts_left(order) <= 0:
            return self.call_help(order)
        self.controller.state["repay"] = order
        self.controller.show("payment")


if __name__ == "__main__":
    import main
    main.App("orders").mainloop()
