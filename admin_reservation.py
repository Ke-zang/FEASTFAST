"""Admin screen: Manage Reservation (page name: "admin_reservation")."""
import tkinter as tk

from main import C, FlatButton, Logo, Page, font
from dashboard import SIDEBAR, NavItem
from check_availability import ADMIN_BG, BOOKING_COLUMNS, DataTable, booking_rows
from notifications import NotificationBell
from reservations_store import all_bookings

ADMIN_NAV = (
    ("admin_dashboard", "Dashboard", "home"),
    ("admin_menu", "Manage Menu", "menu"),
    ("admin_orders", "Manage Order", "order"),
    ("admin_reservation", "Reservation", "table"),
    ("admin_about", "About Us", "info"),
)


class AdminPage(Page):
    """Dark sidebar + title + content area for admin screens."""

    def __init__(self, parent, controller, active="admin_reservation"):
        super().__init__(parent, controller)
        side = tk.Frame(self, bg=SIDEBAR, width=220)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        brand = tk.Frame(side, bg=SIDEBAR)
        brand.pack(fill="x", padx=20, pady=(24, 28))
        Logo(brand, size=40, bg=SIDEBAR, color=C["accent_on_dark"]).pack(side="left")
        tk.Label(brand, text="Feast\nFast", justify="left", fg="#FFFFFF", bg=SIDEBAR,
                 font=font(11, "bold")).pack(side="left", padx=10)
        for target, label, icon in ADMIN_NAV:
            NavItem(side, label, icon, lambda t=target: controller.show(t),
                    active=(target == active)).pack(fill="x", pady=1)
        FlatButton(side, "Log Out", controller.logout, size=10, height=40,
                   bg=SIDEBAR).pack(side="bottom", fill="x", padx=22, pady=26)

        main = tk.Frame(self, bg=ADMIN_BG)
        main.pack(side="left", fill="both", expand=True)
        top = tk.Frame(main, bg=ADMIN_BG)
        top.pack(fill="x", padx=32, pady=(24, 0))
        self.bell = NotificationBell(top, controller, ADMIN_BG)
        self.bell.pack(side="right", anchor="n")
        titles = tk.Frame(top, bg=ADMIN_BG)
        titles.pack(side="left", fill="x", expand=True)
        self.title_lbl = tk.Label(titles, text="", font=font(20, "bold"), fg=C["ink"],
                                  bg=ADMIN_BG, anchor="w")
        self.title_lbl.pack(fill="x")
        self.sub_lbl = tk.Label(titles, text="", font=font(10), fg=C["muted"],
                                bg=ADMIN_BG, anchor="w")
        self.sub_lbl.pack(fill="x")
        self.content = tk.Frame(main, bg=ADMIN_BG)
        self.content.pack(fill="both", expand=True, padx=32, pady=(18, 24))

    def set_header(self, title, subtitle=""):
        self.title_lbl.config(text=title)
        self.sub_lbl.config(text=subtitle or " ")

    def on_show(self, **kwargs):
        self.controller.state["role"] = "manager"      # so notifications go to the manager
        self.bell.update_count()
        self.refresh()

    def refresh(self):
        """Override to reload live data."""


class AdminReservationPage(AdminPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, active="admin_reservation")
        self.table = DataTable(self.content, BOOKING_COLUMNS,
                               empty_text="No reservations yet.")
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        self.set_header("Manage Reservation", "All table bookings made by customers.")
        self.table.set_rows(booking_rows(all_bookings()))


if __name__ == "__main__":
    import main
    main.App("admin_reservation").mainloop()