"""Customer screen: Check Table Availability (page name: "reservation").

This file also holds the shared reservation data and widgets
(BOOKINGS, DataTable, Field, ...) that my_bookings.py and admin_reservation.py import.
"""
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from main import C, FlatButton, font
from dashboard import EDGE, PAGE_BG, CustomerPage
from reservations_store import bookings_for, create_booking, is_free, tables

GREEN = "#12A150"
GREEN_SOFT = "#E7F8EF"
RED_SOFT = "#FDE8E6"
GREY_SOFT = "#EFEFEF"
PRIMARY_DARK = "#A8160F"
ADMIN_BG = "#F0EBE4"


def time_slots():
    return [datetime(2000, 1, 1, h, m).strftime("%I:%M %p").lstrip("0").lower()
            for h in range(10, 22) for m in (0, 30)]


def sync_state(controller):
    st = controller.state
    st["reservations"] = bookings_for(st.get("email"))


def parse_date(text):
    for fmt in ("%d/%m/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text.strip(), fmt)
        except ValueError:
            pass
    return None


def status_chip(text):
    colors = {"RESERVED": (GREEN, GREEN_SOFT), "AVAILABLE": (GREEN, GREEN_SOFT),
              "CANCELLED": (C["primary"], RED_SOFT)}
    fg, bg = colors.get(text, (C["muted"], GREY_SOFT))

    def make(parent):
        return tk.Label(parent, text=f"✓ {text}", font=font(8, "bold"), fg=fg, bg=bg,
                        padx=8, pady=2)
    return make


def action_button(text, command):
    def make(parent):
        b = tk.Label(parent, text=text, font=font(9, "bold"), fg="#FFFFFF",
                     bg=C["primary"], padx=14, pady=6, cursor="hand2")
        b.bind("<Enter>", lambda e: b.config(bg=PRIMARY_DARK))
        b.bind("<Leave>", lambda e: b.config(bg=C["primary"]))
        b.bind("<Button-1>", lambda e: command())
        return b
    return make


class Field(tk.Frame):
    def __init__(self, parent, label, placeholder, values=None):
        super().__init__(parent, bg=C["card"])
        self.placeholder = placeholder
        self.dropdown = values is not None
        tk.Label(self, text=label, font=font(8, "bold"), fg=C["ink"], bg=C["card"],
                 anchor="w").pack(fill="x")
        box = tk.Frame(self, bg="#FFFFFF", highlightthickness=1, highlightbackground=EDGE)
        box.pack(fill="x", pady=(6, 0))
        if self.dropdown:
            self.w = ttk.Combobox(box, values=values, state="readonly", font=font(10))
            self.w.pack(fill="x", padx=6, pady=8)
            self.w.set(placeholder)
        else:
            self._ph = True
            self.w = tk.Entry(box, relief="flat", font=font(10), fg=C["muted"],
                              bg="#FFFFFF", insertbackground=C["ink"])
            self.w.pack(fill="x", padx=10, pady=10)
            self.w.insert(0, placeholder)
            self.w.bind("<FocusIn>", self._in)
            self.w.bind("<FocusOut>", self._out)

    def _in(self, e):
        if self._ph:
            self.w.delete(0, "end")
            self.w.config(fg=C["ink"])
            self._ph = False

    def _out(self, e):
        if not self.w.get().strip():
            self.w.delete(0, "end")
            self.w.insert(0, self.placeholder)
            self.w.config(fg=C["muted"])
            self._ph = True

    def get(self):
        value = self.w.get().strip()
        return "" if value == self.placeholder else value

    def clear(self):
        if self.dropdown:
            self.w.set(self.placeholder)
        else:
            self.w.delete(0, "end")
            self.w.insert(0, self.placeholder)
            self.w.config(fg=C["muted"])
            self._ph = True


class DataTable(tk.Frame):
    STICKY = {"w": "w", "center": "", "e": "e"}

    def __init__(self, parent, columns, empty_text="Nothing here yet.", light_header=False):
        super().__init__(parent, bg=C["card"], highlightthickness=1,
                         highlightbackground=EDGE)
        self.columns, self.empty_text = columns, empty_text
        hbg, hfg = ("#F8F9FC", C["ink"]) if light_header else (C["primary"], "#FFFFFF")
        head = tk.Frame(self, bg=hbg)
        head.pack(fill="x")
        self._cols(head)
        for i, (title, _, anchor) in enumerate(columns):
            tk.Label(head, text=title, font=font(9, "bold"), fg=hfg, bg=hbg,
                     anchor=anchor).grid(row=0, column=i, sticky="ew", padx=(16, 8), pady=13)

        self.canvas = tk.Canvas(self, bg=C["card"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=C["card"])
        win = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(win, width=e.width))
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._wheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _cols(self, frame):
        for i, (_, weight, _) in enumerate(self.columns):
            frame.columnconfigure(i, weight=weight, uniform="col")

    def _wheel(self, e):
        if self.inner.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")

    def set_rows(self, rows):
        for w in self.inner.winfo_children():
            w.destroy()
        self.canvas.yview_moveto(0)
        if not rows:
            tk.Label(self.inner, text=self.empty_text, font=font(10), fg=C["muted"],
                     bg=C["card"]).pack(pady=40)
            return
        for cells in rows:
            row = tk.Frame(self.inner, bg=C["card"])
            row.pack(fill="x")
            self._cols(row)
            for i, cell in enumerate(cells):
                anchor = self.columns[i][2]
                if callable(cell):
                    w = cell(row)
                    w.grid(row=0, column=i, sticky=self.STICKY[anchor], padx=(16, 8), pady=11)
                else:
                    w = tk.Label(row, text=cell, font=font(10, "bold" if i == 1 else "normal"),
                                 fg=C["ink"], bg=C["card"], anchor=anchor)
                    w.grid(row=0, column=i, sticky="ew", padx=(16, 8), pady=14)
            tk.Frame(self.inner, height=1, bg=EDGE).pack(fill="x")


def booking_rows(bookings):
    return [[b["booking"], b["table"], b["date"], b["time"], f'{b["people"]} people',
             status_chip(b["status"])] for b in bookings]


BOOKING_COLUMNS = [("Booking", 2, "w"), ("Table", 2, "w"), ("Date", 2, "center"),
                   ("Time", 2, "center"), ("People", 2, "center"), ("Status", 2, "center")]


class ReservationPage(CustomerPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, active="reservation")
        self.query = None

        card = tk.Frame(self.content, bg=C["card"], highlightthickness=1,
                        highlightbackground=EDGE)
        card.pack(fill="x")
        row = tk.Frame(card, bg=C["card"])
        row.pack(fill="x", padx=22, pady=18)
        self.f_date = Field(row, "DATE", "DD/MM/YY")
        self.f_time = Field(row, "TIME", "Select Time", time_slots())
        self.f_people = Field(row, "PEOPLE", "Number of People",
                              [str(n) for n in range(1, 9)])
        for i, f in enumerate((self.f_date, self.f_time, self.f_people)):
            row.columnconfigure(i, weight=1, uniform="f")
            f.grid(row=0, column=i, sticky="ew", padx=(0, 20))
        row.columnconfigure(3, weight=0)
        FlatButton(row, "Check Availability", self.check, size=10, width=170, height=44,
                   bg=C["card"]).grid(row=0, column=3, sticky="s")

        strip = tk.Frame(self.content, bg=PAGE_BG)
        strip.pack(fill="x", pady=(16, 12))
        self.banner = tk.Frame(strip, bg=GREY_SOFT)
        self.banner.pack(side="left", fill="x", expand=True)
        self.accent = tk.Frame(self.banner, width=4, bg=C["muted"])
        self.accent.pack(side="left", fill="y")
        self.banner_lbl = tk.Label(self.banner, text="", font=font(9, "bold"),
                                   bg=GREY_SOFT, fg=C["muted"], anchor="w")
        self.banner_lbl.pack(side="left", padx=14, pady=9)
        link = tk.Label(strip, text="My bookings  →", font=font(9, "bold"), fg=C["primary"],
                        bg=PAGE_BG, cursor="hand2")
        link.pack(side="right", padx=(16, 0))
        link.bind("<Button-1>", lambda e: controller.show("bookings"))

        self.table = DataTable(self.content, [("ID", 1, "w"), ("TABLE", 4, "w"),
                                              ("CAPACITY", 2, "w"), ("STATUS", 2, "w"),
                                              ("ACTION", 2, "e")],
                               empty_text="Choose a date, time and party size above.",
                               light_header=True)
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        self.set_header("Check Table Availability",
                        "Choose a date, time and number of people to see which tables are free.")
        sync_state(self.controller)
        self.query = None
        for f in (self.f_date, self.f_time, self.f_people):
            f.clear()
        self._banner("Enter your details and press Check Availability.", "hint")
        self.table.set_rows([])

    def _banner(self, text, kind):
        fg, bg = {"ok": (GREEN, GREEN_SOFT), "none": (C["primary"], RED_SOFT),
                  "hint": (C["muted"], GREY_SOFT)}[kind]
        self.banner.config(bg=bg)
        self.accent.config(bg=fg)
        self.banner_lbl.config(text=text, fg=fg, bg=bg)

    def check(self):
        d = parse_date(self.f_date.get())
        time_s, people = self.f_time.get(), self.f_people.get()
        if d is None:
            return messagebox.showwarning("Date", "Enter the date as DD/MM/YY, e.g. 02/09/26.")
        if not time_s:
            return messagebox.showwarning("Time", "Please select a time.")
        if not people:
            return messagebox.showwarning("People", "Please select the number of people.")
        when = datetime.combine(d.date(), datetime.strptime(time_s, "%I:%M %p").time())
        if when < datetime.now():
            return messagebox.showwarning("Date", "That date and time has already passed.")

        date_s, n = d.strftime("%d/%m/%y"), int(people)
        self.query = (date_s, time_s, n)
        free = [t for t in tables() if t[2] >= n and is_free(t[1], date_s, time_s)]
        if free:
            self._banner(f"{len(free)} suitable table{'s' if len(free) != 1 else ''} available.",
                         "ok")
        else:
            self._banner("No tables available for that slot. Try another time.", "none")
        self.table.set_rows([[str(t[0]), t[1], f"{t[2]} people", status_chip("AVAILABLE"),
                              action_button("Reserve Table", lambda t=t: self.reserve(t))]
                             for t in free])

    def reserve(self, table):
        if not self.query:
            return
        date_s, time_s, n = self.query
        parts = self.customer_name.strip().split()
        if not create_booking(self.controller.state.get("email"),
                              parts[0].title() if parts else "Guest",
                              table[1], date_s, time_s, n):
            messagebox.showinfo("Taken", f"{table[1]} was just booked. Please check again.")
            return self.check()
        sync_state(self.controller)
        messagebox.showinfo("Reserved", f"{table[1]} reserved for {n} on {date_s} at {time_s}.")
        self.controller.show("bookings")


if __name__ == "__main__":
    import main
    main.App("reservation").mainloop()