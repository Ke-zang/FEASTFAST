"""Create Account screen."""
import re
import tkinter as tk

from main import (C, AuthPage, Banner, FlatButton, FormField, LinkLabel, font,
                  register_customer, validate_email, validate_name, validate_password)

# (label, bar colour, label text colour)  - label colours pass 4.5:1 on white
STRENGTH = (("", C["border"], C["muted"]), ("Weak", "#D32F2F", "#B3261E"),
            ("Fair", "#E08A00", "#8A5200"), ("Good", "#7CB342", "#3F6B12"),
            ("Strong", "#2E7D32", C["success"]))


def password_score(pw):
    """0 (empty) to 4 (strong)."""
    if not pw:
        return 0
    points = sum((len(pw) >= 8,
                  bool(re.search(r"[a-z]", pw) and re.search(r"[A-Z]", pw)),
                  bool(re.search(r"\d", pw)),
                  bool(re.search(r"[^A-Za-z0-9]", pw))))
    return max(1, points)


class StrengthMeter(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=C["card"])
        self.segs = []
        for _ in range(4):
            seg = tk.Frame(self, height=4, bg=C["border"])
            seg.pack(side="left", fill="x", expand=True, padx=(0, 4))
            self.segs.append(seg)
        self.label = tk.Label(self, text=" ", width=7, anchor="e", font=font(9, "bold"),
                              fg=C["muted"], bg=C["card"])
        self.label.pack(side="left")

    def update_for(self, pw):
        score = password_score(pw)
        text, bar, ink = STRENGTH[score]
        for i, seg in enumerate(self.segs):
            seg.config(bg=bar if i < score else C["border"])
        self.label.config(text=text or " ", fg=ink)


class CreateAccountPage(AuthPage):
    def __init__(self, parent, controller):
        super().__init__(
            parent, controller, "signup",
            "Join\nFeast Fast.",
            "Create your free account and start ordering in under a minute.",
            ("One account for orders and tables", "Save time on every break",
             "Manage and cancel reservations"))
        body = self.body
        self.heading("Create account", "Set up your account to get started.")

        go = self.submit
        self.name = FormField(body, "Full Name", "Enter your full name",
                              validator=validate_name, on_enter=go)
        self.email = FormField(body, "Email", "your.email@example.com",
                               validator=validate_email, on_enter=go)
        self.password = FormField(body, "Password", "Create a strong password",
                                  secret=True, validator=validate_password,
                                  on_enter=go)
        self.meter = StrengthMeter(body)
        self.confirm = FormField(body, "Confirm Password", "Repeat your password",
                                 secret=True, validator=self._check_confirm,
                                 on_enter=go)
        self.name.pack(fill="x")
        self.email.pack(fill="x", pady=(2, 0))
        self.password.pack(fill="x", pady=(2, 0))
        self.meter.pack(fill="x", pady=(0, 6))
        self.confirm.pack(fill="x", pady=(2, 0))

        # live strength meter + re-check "confirm" when the password changes
        def on_password_key(event):
            self.password._key(event)
            self.meter.update_for(self.password.get())
            if self.confirm.get():
                self.confirm.validate()
        self.password.entry.bind("<KeyRelease>", on_password_key)

        self.banner = Banner(body)
        self.banner.pack(fill="x")
        FlatButton(body, "Create Account", self.submit, kind="accent",
                   height=46).pack(fill="x", pady=(4, 0))

        row = tk.Frame(body, bg=C["card"])
        row.pack(pady=(14, 0))
        tk.Label(row, text="Already have an account?", font=font(9), fg=C["muted"],
                 bg=C["card"]).pack(side="left")
        LinkLabel(row, " Log in", lambda: controller.show("customer_login"),
                  fg=C["accent"], bold=True).pack(side="left")

    def _check_confirm(self, value):
        if not value:
            return "Please confirm your password."
        if value != self.password.get():
            return "Passwords do not match."
        return None

    def on_show(self, **kwargs):
        for f in (self.name, self.email, self.password, self.confirm):
            f.clear()
        self.meter.update_for("")
        self.banner.hide()
        self.focus_set()

    def submit(self):
        fields = (self.name, self.email, self.password, self.confirm)
        results = [f.validate() for f in fields]      # validate all, show all errors
        if not all(results):
            fields[results.index(False)].focus()
            return
        error = register_customer(self.name.get(), self.email.get(),
                                  self.password.get())
        if error:
            self.email.set_error(error)
            self.email.focus()
            return
        self.controller.show("customer_login", email=self.email.get().strip(),
                             notice="Account created! Please log in.")


if __name__ == "__main__":
    import main
    main.App("create_account").mainloop()
