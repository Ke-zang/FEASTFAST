"""Customer screen: My Table Bookings (page name: "bookings")."""
import tkinter as tk
from tkinter import messagebox

from main import C, font
from dashboard import CustomerPage
from check_availability import (BOOKING_COLUMNS, DataTable, action_button,
                                booking_rows, sync_state)
from reservations_store import cancel_booking

MY_COLUMNS = BOOKING_COLUMNS + [("Action", 2, "e")]


def _dash(parent):
    return tk.Label(parent, text="—", font=font(10), fg=C["muted"], bg=C["card"])


class MyBookingsPage(CustomerPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, active="reservation")
        self.table = DataTable(self.content, MY_COLUMNS,
                               empty_text="You have no table bookings yet.")
        self.table.pack(fill="both", expand=True, pady=(10, 0))

    def refresh(self):
        self.set_header("My Table Bookings", "Your table reservations. You can cancel a booking any time.")
        sync_state(self.controller)
        mine = self.controller.state["reservations"]
        rows = booking_rows(mine)
        for row, booking in zip(rows, mine):
            row.append(action_button("Cancel", lambda b=booking: self.cancel(b))
                       if booking["status"] == "RESERVED" else _dash)
        self.table.set_rows(rows)

    def cancel(self, booking):
        if not messagebox.askyesno("Cancel booking",
                                   f'Cancel {booking["table"]} on {booking["date"]} at '
                                   f'{booking["time"]}?'):
            return
        cancel_booking(booking["pk"])
        self.controller.toast("Booking cancelled")
        self.refresh()


if __name__ == "__main__":
    import main
    main.App("bookings").mainloop()
