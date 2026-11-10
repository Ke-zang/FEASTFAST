"""Admin screen: Manage Menu (page name: "admin_menu").

Add items, change a price, or mark an item sold out. Changes are saved and show
up straight away on the customer Menu screens.
"""
import tkinter as tk
from tkinter import messagebox, ttk

from main import C, FlatButton, font
from admin_reservation import AdminPage
from check_availability import ADMIN_BG, DataTable
import menu_data
from menu_data import CATEGORIES, MENU_ITEMS, add_item, money
from ui_helpers import buttons_cell, chip, text_cell

COLUMNS = [("Food Item", 4, "w"), ("Category", 2, "w"), ("Price", 2, "w"),
           ("Status", 2, "w"), ("", 6, "e")]


class ItemDialog(tk.Toplevel):
    """Small modal form used for both Add and Edit."""

    def __init__(self, parent, title, item=None):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=C["card"])
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.result = None
        body = tk.Frame(self, bg=C["card"])
        body.pack(padx=26, pady=22)
        self.name = self._row(body, "Food item", tk.Entry(body, width=30, font=font(10)))
        self.cat = self._row(body, "Category", ttk.Combobox(
            body, values=CATEGORIES, state="readonly", width=28, font=font(10)))
        self.price = self._row(body, "Price (Nu.)", tk.Entry(body, width=30, font=font(10)))
        item = item or {}
        self.name.insert(0, item.get("name", ""))
        self.cat.set(item.get("category", CATEGORIES[0]))
        self.price.insert(0, f'{item["price"]:g}' if "price" in item else "")
        btns = tk.Frame(body, bg=C["card"])
        btns.pack(fill="x", pady=(16, 0))
        FlatButton(btns, "Save", self._save, width=110, height=40).pack(side="right")
        FlatButton(btns, "Cancel", self.destroy, kind="outline", width=110,
                   height=40).pack(side="right", padx=8)
        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())
        # centre over the app, wait until visible, THEN grab (grab_set on a window
        # that is not yet on screen fails on some systems and the form never opens)
        root = parent.winfo_toplevel()
        self.update_idletasks()
        x = root.winfo_rootx() + (root.winfo_width() - self.winfo_reqwidth()) // 2
        y = root.winfo_rooty() + (root.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
        self.wait_visibility()
        self.grab_set()
        self.name.focus_set()

    @staticmethod
    def _row(parent, label, widget):
        tk.Label(parent, text=label, font=font(9, "bold"), fg=C["ink"], bg=C["card"],
                 anchor="w").pack(fill="x", pady=(8, 3))
        widget.pack(fill="x")
        return widget

    def _save(self):
        name, cat = self.name.get().strip(), self.cat.get()
        try:
            price = float(self.price.get().strip().replace("Nu.", "").replace(",", ""))
            if price != price or price in (float("inf"), float("-inf")):
                price = -1
        except ValueError:
            price = -1
        if not name or cat not in CATEGORIES or price <= 0:
            messagebox.showwarning("Check the form", "Enter a name, pick a category and "
                                   "give a price above zero.", parent=self)
            return
        self.result = (name, cat, int(price) if price == int(price) else price)
        self.destroy()


class AdminMenuPage(AdminPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, active="admin_menu")
        bar = tk.Frame(self.content, bg=ADMIN_BG)
        bar.pack(fill="x", pady=(0, 12))
        FlatButton(bar, "+ Add Item", self.add, width=140, height=40).pack(side="right")
        self.table = DataTable(self.content, COLUMNS, empty_text="The menu is empty.")
        self.table.pack(fill="both", expand=True)
        # visible scrollbar so new items at the bottom of the list can be reached
        bar_y = ttk.Scrollbar(self.table, orient="vertical", command=self.table.canvas.yview)
        self.table.canvas.configure(yscrollcommand=bar_y.set)
        bar_y.pack(side="right", fill="y", before=self.table.canvas)

    def refresh(self):
        self.set_header("Manage Menu", "Add items, change prices, or mark an item sold out.")
        menu_data.reload()
        rows = []
        for item in MENU_ITEMS:
            ok = item.get("available", True)
            rows.append([text_cell(item["name"], bold=True), item["category"],
                         money(item["price"]), chip("Available" if ok else "Sold out"),
                         buttons_cell(("Edit", lambda i=item: self.edit(i), "soft"),
                                      ("Mark sold out" if ok else "Mark available",
                                       lambda i=item: self.toggle(i), "dark"),
                                      ("Delete", lambda i=item: self.delete(i), "soft"))])
        self.table.set_rows(rows)

    def _ask(self, title, item=None):
        dlg = ItemDialog(self, title, item)
        self.wait_window(dlg)
        return dlg.result

    def add(self):
        result = self._ask("Add menu item")
        if result:
            error = add_item(*result)
            if error:
                messagebox.showwarning("Menu", error, parent=self)
            else:
                self.controller.toast(f"{result[0]} added — customers can order it now")
            self.refresh()
            if not error:                     # jump to the new item at the bottom
                self.update_idletasks()
                self.table.canvas.yview_moveto(1)

    def edit(self, item):
        result = self._ask("Edit menu item", item)
        if result:
            error = menu_data.update_item(item["id"], *result)
            if error:
                messagebox.showwarning("Menu", error, parent=self)
            self.refresh()

    def toggle(self, item):
        menu_data.set_available(item["id"], not item.get("available", True))
        self.refresh()

    def delete(self, item):
        if messagebox.askyesno("Delete item", f'Remove "{item["name"]}" from the menu?'):
            menu_data.delete_item(item["id"])
            self.refresh()


if __name__ == "__main__":
    import main
    main.App("admin_menu").mainloop()
