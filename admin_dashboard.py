"""Admin Dashboard (page name: "admin_dashboard") - the screen managers land on."""
import tkinter as tk

from main import C, FlatButton, font
from admin_reservation import AdminPage
import menu_data
from check_availability import ADMIN_BG
from menu_data import MENU_ITEMS
from orders_store import count_payments, count_ready_to_start, count_status
from reservations_store import count_reserved
from ui_helpers import stat_card


class AdminDashboardPage(AdminPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, active="admin_dashboard")
        grid = tk.Frame(self.content, bg=ADMIN_BG)
        grid.pack(fill="x")
        self.values = {}
        for i, (key, label) in enumerate((("check", "PAYMENTS TO CHECK"),
                                          ("waiting", "READY TO START"),
                                          ("progress", "IN PROGRESS"),
                                          ("refunds", "REFUNDS DUE"),
                                          ("tables", "TABLES BOOKED"),
                                          ("menu", "MENU ITEMS AVAILABLE"))):
            card, value = stat_card(grid, label)
            col = (i % 3) * 2
            grid.columnconfigure(col, weight=1, uniform="stat")
            if col:
                grid.columnconfigure(col - 1, minsize=14)
            card.grid(row=i // 3, column=col, sticky="nsew", pady=(0 if i < 3 else 14, 0))
            self.values[key] = value

        tk.Label(self.content, text="Quick actions", font=font(13, "bold"),
                 fg=C["ink"], bg=ADMIN_BG, anchor="w").pack(fill="x", pady=(26, 10))
        row = tk.Frame(self.content, bg=ADMIN_BG)
        row.pack(fill="x")
        for text, page in (("Manage Orders", "admin_orders"), ("Manage Menu", "admin_menu"),
                           ("Reservations", "admin_reservation")):
            FlatButton(row, text, lambda p=page: controller.show(p), kind="outline",
                       width=170, height=44, bg=ADMIN_BG).pack(side="left", padx=(0, 12))

    def refresh(self):
        self.set_header("Dashboard", "A quick look at today's canteen activity.")
        v = self.values
        menu_data.reload()
        v["check"].config(text=str(count_payments("Submitted")))
        v["waiting"].config(text=str(count_ready_to_start()))
        v["refunds"].config(text=str(count_payments("Refund due")))
        v["progress"].config(text=str(count_status("Preparing", "Ready")))
        v["tables"].config(text=str(count_reserved()))
        v["menu"].config(text=str(sum(i.get("available", True) for i in MENU_ITEMS)))


if __name__ == "__main__":
    import main
    main.App("admin_dashboard").mainloop()
