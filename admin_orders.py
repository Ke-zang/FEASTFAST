"""Admin screen: Manage Order (page name: "admin_orders").

Shows every customer order together with its payment. For each new order:
  1. Check the journal number and amount against the canteen's bank statement.
  2. Found       -> Confirm payment, then Start Preparing -> Mark Ready -> Complete.
     Not found   -> Wrong journal no.: the customer is told and can type another number.
The manager can't start an order whose payment is not confirmed (also enforced in
orders_store). Once an order is Preparing the customer can no longer cancel it.
A customer who cancels a paid, still-Pending order phones the manager; the order then
shows Refund due until the manager sends the money back and presses Mark Refunded.
"""
from tkinter import messagebox

from main import C
from admin_reservation import AdminPage
from check_availability import DataTable
from menu_data import money
from orders_store import (advance_order, all_orders, attempts_left, mark_refunded,
                          payment_status, reject_payment, summary, verify_payment)
from ui_helpers import (button_cell, chip, payment_cell, stacked_buttons_cell, text_cell,
                        two_line_cell, wrap_cell)

COLUMNS = [("Order", 4, "w"), ("Items", 4, "w"), ("Total", 3, "w"), ("Payment", 5, "w"),
           ("Status", 4, "w"), ("", 5, "e")]
ACTION = {"Pending": "Start Preparing", "Preparing": "Mark Ready", "Ready": "Complete"}


class AdminOrdersPage(AdminPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, active="admin_orders")
        self.table = DataTable(self.content, COLUMNS, empty_text="No orders yet.")
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        self.set_header("Manage Order", "Check each payment first, then prepare the order.")
        rows = []
        for o in all_orders():
            rows.append([two_line_cell(o["id"], o["customer"], o["placed"]),
                         wrap_cell(summary(o, 80), 100), money(o["total"]), payment_cell(o),
                         chip(o["status"]), self.action(o)])
        self.table.set_rows(rows)

    def action(self, o):
        pay = payment_status(o)
        if o["status"] == "Pending":
            if pay == "Submitted":                       # waiting for the manager's check
                return stacked_buttons_cell(
                    ("Confirm payment", lambda o=o: self.confirm(o), "primary"),
                    ("Wrong journal no.", lambda o=o: self.reject(o), "soft"))
            if pay == "Rejected":
                left = attempts_left(o)
                return text_cell("Waiting for customer" if left else "Customer must call",
                                 fg=C["muted"], anchor="e")
            return button_cell("Start Preparing", lambda o=o: self.advance(o))
        if o["status"] in ACTION:
            return button_cell(ACTION[o["status"]], lambda o=o: self.advance(o))
        if o["status"] == "Cancelled" and pay == "Refund due":
            specs = [("Mark Refunded", lambda o=o: self.refunded(o), "primary")]
            if o["payment"]["verified"] is None:         # the payment was never confirmed
                specs.append(("Not received", lambda o=o: self.reject(o), "soft"))
            return stacked_buttons_cell(*specs)
        return text_cell("", anchor="e")

    # ── actions ──
    def _done(self, error, message=None):
        if error:
            self.controller.toast(error)
        elif message:
            self.controller.toast(message)
        self.refresh()

    def confirm(self, o):
        pay = o["payment"]
        if not messagebox.askyesno(
                "Confirm payment",
                f"Open the canteen's bank statement and look for:\n\n"
                f"   Journal number:  {pay['journal']}\n"
                f"   Amount:  {money(o['total'])}\n"
                f"   Method:  {pay['method']}\n\n"
                "Did you find this journal number with the full amount?"):
            return
        error = verify_payment(o)
        self._done(error, f"Payment confirmed — you can now start preparing {o['id']}")

    def reject(self, o):
        pay = o["payment"]
        if o["status"] == "Cancelled":
            text = (f"Mark journal number {pay['journal']} as NOT received?\n"
                    f"The order is cancelled, so {o['customer']} will be told that no "
                    "refund is due.")
        else:
            text = (f"Mark journal number {pay['journal']} as NOT found?\n"
                    f"{o['customer']} will be told to check the number and enter it again "
                    "(or to call you).")
        if not messagebox.askyesno("Journal number not found", text):
            return
        error = reject_payment(o)
        self._done(error, f"{o['customer']} has been told")

    def refunded(self, o):
        if not messagebox.askyesno("Mark refunded",
                                   f"Have you sent {money(o['total'])} back to {o['customer']}?"):
            return
        error = mark_refunded(o)
        self._done(error, f"Refund for {o['id']} recorded")

    def advance(self, order):
        new, error = advance_order(order)
        if error:
            self.controller.toast(error, ms=4000)
        elif new == "Ready":
            self.controller.toast(f"{order['id']} is ready — {order['customer']} has been notified")
        self.refresh()


if __name__ == "__main__":
    import main
    main.App("admin_orders").mainloop()
