"""Customer Log In screen."""
import tkinter as tk
from tkinter import messagebox

from main import (C, AuthPage, Banner, FlatButton, FormField, LinkLabel, RoleSwitch,
                  font, THROTTLE, validate_email, validate_required_password,
                  verify_customer)


class CustomerLoginPage(AuthPage):
    def __init__(self, parent, controller):
        super().__init__(
            parent, controller, "customer",
            "Hungry?\nSkip the queue.",
            "Order ahead, reserve a table and pick up your food the moment it's ready.",
            ("Browse the full canteen menu", "Reserve a table in seconds",
             "Track your order status live"))
        body = self.body
        self.heading("Welcome back", "Log in to order your food.")
        RoleSwitch(body, "customer", controller).pack(fill="x", pady=(0, 10))

        self.banner = Banner(body)
        self.banner.pack(fill="x")
        self.email = FormField(body, "Email", "your.email@example.com",
                               validator=validate_email, on_enter=self.submit)
        self.password = FormField(body, "Password", "Enter your password", secret=True,
                                  validator=validate_required_password,
                                  on_enter=self.submit)
        self.email.pack(fill="x")
        self.password.pack(fill="x", pady=(4, 0))

        LinkLabel(body, "Forgot password?", self._forgot, fg=C["primary"],
                  bold=True).pack(anchor="e")
        FlatButton(body, "Log In", self.submit, height=46).pack(fill="x", pady=(14, 0))

        row = tk.Frame(body, bg=C["card"])
        row.pack(pady=(18, 0))
        tk.Label(row, text="New here?", font=font(9), fg=C["muted"],
                 bg=C["card"]).pack(side="left")
        LinkLabel(row, " Create an account", lambda: controller.show("create_account"),
                  fg=C["primary"], bold=True).pack(side="left")

    def on_show(self, email="", notice="", **kwargs):
        self.email.set(email)
        self.password.clear()
        self.banner.hide()
        if notice:
            self.banner.show(notice, "success")
        (self.password if email else self.email).focus()

    def _forgot(self):
        messagebox.showinfo("Reset password",
                            "Password reset isn't available yet.\n"
                            "Please contact support@feastfast.example.")

    def submit(self):
        results = [self.email.validate(), self.password.validate()]
        if not all(results):
            (self.email, self.password)[results.index(False)].focus()
            return
        key = "customer:" + self.email.get().strip().lower()
        wait = THROTTLE.locked_for(key)
        if wait:
            self.banner.show(f"Too many attempts. Try again in {wait}s.")
            return
        user = verify_customer(self.email.get(), self.password.get())
        if user is None:
            THROTTLE.fail(key)
            self.banner.show("Incorrect email or password.")
            self.password.clear()
            self.password.focus()
            return
        THROTTLE.reset(key)
        self.controller.show("dashboard", name=user["name"], email=user["email"])


if __name__ == "__main__":
    import main
    main.App("customer_login").mainloop()
