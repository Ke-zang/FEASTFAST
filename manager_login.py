"""Manager / Staff Portal login screen."""
import tkinter as tk
from tkinter import messagebox

from main import (C, AuthPage, Banner, FlatButton, FormField, LinkLabel, RoleSwitch,
                  font, THROTTLE, validate_required_password, validate_username,
                  verify_staff)


class ManagerLoginPage(AuthPage):
    def __init__(self, parent, controller):
        super().__init__(
            parent, controller, "staff",
            "Canteen operations,\nsimplified.",
            "Manage orders, menus and reservations from one place.",
            ("Review incoming orders", "Update menu availability",
             "Manage table reservations"))
        body = self.body
        self.heading("Staff Portal", "Sign in with your staff credentials.")
        RoleSwitch(body, "staff", controller).pack(fill="x", pady=(0, 10))

        self.banner = Banner(body)
        self.banner.pack(fill="x")
        self.username = FormField(body, "Staff Username", "Enter your username",
                                  validator=validate_username, on_enter=self.submit)
        self.password = FormField(body, "Password", "Enter your password", secret=True,
                                  validator=validate_required_password,
                                  on_enter=self.submit)
        self.username.pack(fill="x")
        self.password.pack(fill="x", pady=(4, 0))

        LinkLabel(body, "Forgot password?", self._forgot, fg=C["ink"],
                  bold=True).pack(anchor="e")
        FlatButton(body, "Sign In", self.submit, kind="dark",
                   height=46).pack(fill="x", pady=(14, 0))

        tk.Label(body, text="Authorized staff only", font=font(9, "bold"),
                 fg=C["muted"], bg=C["card"]).pack(pady=(18, 0))

    def on_show(self, **kwargs):
        self.username.clear()
        self.password.clear()
        self.banner.hide()
        self.focus_set()

    def _forgot(self):
        messagebox.showinfo("Reset password",
                            "Staff passwords are reset by the system administrator.")

    def submit(self):
        results = [self.username.validate(), self.password.validate()]
        if not all(results):
            (self.username, self.password)[results.index(False)].focus()
            return
        key = "staff:" + self.username.get().strip().lower()
        wait = THROTTLE.locked_for(key)
        if wait:
            self.banner.show(f"Too many attempts. Try again in {wait}s.")
            return
        staff = verify_staff(self.username.get(), self.password.get())
        if staff is None:
            THROTTLE.fail(key)
            self.banner.show("Incorrect username or password.")
            self.password.clear()
            self.password.focus()
            return
        THROTTLE.reset(key)
        self.controller.show("admin_dashboard", role="Manager", name=staff["name"])


if __name__ == "__main__":
    import main
    main.App("manager_login").mainloop()
