"""Customer Profile screen.

Personal information (photo, first/last name, email, phone), Change password,
and a Danger zone (log out of all other sessions, delete account).
Changing the email or deleting the account asks for the password again.
"""
import tkinter as tk
from tkinter import filedialog, messagebox

from main import (C, FlatButton, FormField, bump_session_version, change_customer_email,
                  change_customer_password, delete_customer, font, get_customer,
                  load_avatar, pillow_installed, remove_avatar, save_avatar,
                  update_customer, validate_email, validate_name, validate_password,
                  validate_phone, validate_required_password, verify_customer)
from dashboard import EDGE, Avatar, CustomerPage


# ════════════════════════════ HELPERS ════════════════════════════
def validate_first(v):
    return "First name is required." if not v.strip() else validate_name(v)


def validate_last(v):
    return validate_name(v) if v.strip() else None       # optional


def confirm_dialog(parent, title, message, confirm_text, password_for=None):
    """Modal confirmation. When `password_for` (an email) is given the person
    must also re-enter their password. Returns True only if confirmed."""
    root = parent.winfo_toplevel()
    dlg = tk.Toplevel(root)
    dlg.title(title)
    dlg.configure(bg=C["card"])
    dlg.resizable(False, False)
    dlg.transient(root)
    result = {"ok": False}

    body = tk.Frame(dlg, bg=C["card"])
    body.pack(padx=28, pady=(24, 22))
    tk.Label(body, text=title, font=font(14, "bold"), fg=C["ink"], bg=C["card"],
             anchor="w").pack(fill="x")
    tk.Label(body, text=message, font=font(10), fg=C["muted"], bg=C["card"],
             anchor="w", justify="left", wraplength=340).pack(fill="x", pady=(6, 14))

    field = None

    def confirm():
        if field is not None:
            if not field.validate():
                return
            if verify_customer(password_for, field.get()) is None:
                field.set_error("Incorrect password.")
                return
        result["ok"] = True
        dlg.destroy()

    if password_for:
        field = FormField(body, "Confirm your password", "Enter your password",
                          secret=True, validator=validate_required_password,
                          on_enter=confirm)
        field.pack(fill="x")

    row = tk.Frame(body, bg=C["card"])
    row.pack(fill="x", pady=(6, 0))
    FlatButton(row, confirm_text, confirm, width=170, height=40, size=9).pack(side="right")
    FlatButton(row, "Cancel", dlg.destroy, kind="outline", width=90, height=40,
               size=9).pack(side="right", padx=(0, 10))

    dlg.bind("<Escape>", lambda e: dlg.destroy())
    dlg.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - dlg.winfo_reqwidth()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - dlg.winfo_reqheight()) // 2
    dlg.geometry(f"+{max(0, x)}+{max(0, y)}")
    dlg.wait_visibility()
    dlg.grab_set()
    if field is not None:
        field.focus()
    dlg.wait_window()
    return result["ok"]


def password_dialog(parent, email):
    """Modal 'Change password' form. Returns True if the password was changed."""
    root = parent.winfo_toplevel()
    dlg = tk.Toplevel(root)
    dlg.title("Change password")
    dlg.configure(bg=C["card"])
    dlg.resizable(False, False)
    dlg.transient(root)
    result = {"ok": False}

    body = tk.Frame(dlg, bg=C["card"])
    body.pack(padx=28, pady=(24, 22))
    tk.Label(body, text="Change password", font=font(14, "bold"), fg=C["ink"],
             bg=C["card"], anchor="w").pack(fill="x", pady=(0, 10))

    def check_confirm(v):
        if not v:
            return "Please confirm your new password."
        return None if v == new.get() else "Passwords do not match."

    def submit():
        fields = (current, new, confirm)
        results = [f.validate() for f in fields]
        if not all(results):
            fields[results.index(False)].focus()
            return
        if new.get() == current.get():
            new.set_error("Choose a password different from the current one.")
            new.focus()
            return
        error = change_customer_password(email, current.get(), new.get())
        if error:
            current.set_error(error)
            current.focus()
            return
        result["ok"] = True
        dlg.destroy()

    current = FormField(body, "Current password", "Enter your current password",
                        secret=True, validator=validate_required_password)
    new = FormField(body, "New password", "At least 8 characters",
                    secret=True, validator=validate_password)
    confirm = FormField(body, "Confirm new password", "Re-enter the new password",
                        secret=True, validator=check_confirm, on_enter=submit)
    for f in (current, new, confirm):
        f.pack(fill="x")

    row = tk.Frame(body, bg=C["card"])
    row.pack(fill="x", pady=(6, 0))
    FlatButton(row, "Update password", submit, width=170, height=40, size=9).pack(side="right")
    FlatButton(row, "Cancel", dlg.destroy, kind="outline", width=90, height=40,
               size=9).pack(side="right", padx=(0, 10))

    dlg.bind("<Escape>", lambda e: dlg.destroy())
    dlg.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - dlg.winfo_reqwidth()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - dlg.winfo_reqheight()) // 2
    dlg.geometry(f"+{max(0, x)}+{max(0, y)}")
    dlg.wait_visibility()
    dlg.grab_set()
    current.focus()
    dlg.wait_window()
    return result["ok"]


# ════════════════════════════ PAGE ════════════════════════════
class ProfilePage(CustomerPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, active="profile")
        self.set_header("Profile", "Manage your account details and preferences.")
        self._loaded = ("", "", "", "")

        # ── Personal information card
        card = tk.Frame(self.content, bg=C["card"], highlightthickness=1,
                        highlightbackground=EDGE, highlightcolor=EDGE)
        card.pack(fill="x")
        inner = tk.Frame(card, bg=C["card"])
        inner.pack(fill="x", padx=24, pady=(18, 18))
        tk.Label(inner, text="Personal information", font=font(12, "bold"),
                 fg=C["ink"], bg=C["card"], anchor="w").pack(fill="x")

        row = tk.Frame(inner, bg=C["card"])
        row.pack(fill="x", pady=(12, 10))
        self.photo_avatar = Avatar(row, size=64, bg=C["card"])
        self.photo_avatar.pack(side="left")
        self.btn_change = FlatButton(row, "Change photo", self._change_photo,
                                     kind="soft", size=9, width=120, height=34)
        self.btn_change.pack(side="left", padx=(16, 8))
        self.btn_remove = FlatButton(row, "Remove", self._remove_photo,
                                     kind="outline", size=9, width=90, height=34)
        self.btn_remove.pack(side="left")

        grid = tk.Frame(inner, bg=C["card"])
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1, uniform="f")
        grid.columnconfigure(1, minsize=16)
        grid.columnconfigure(2, weight=1, uniform="f")
        self.first = FormField(grid, "First name", "Enter your first name",
                               validator=validate_first, on_enter=self.save)
        self.last = FormField(grid, "Last name", "Enter your last name (optional)",
                              validator=validate_last, on_enter=self.save)
        self.email = FormField(grid, "Email", "name@example.com",
                               validator=validate_email, on_enter=self.save)
        self.phone = FormField(grid, "Phone number", "+975 17 123 456",
                               validator=validate_phone, on_enter=self.save)
        self.first.grid(row=0, column=0, sticky="ew")
        self.last.grid(row=0, column=2, sticky="ew")
        self.email.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.phone.grid(row=1, column=2, sticky="new", pady=(4, 0))
        for f in (self.first, self.last, self.email, self.phone):
            f.entry.bind("<KeyRelease>", lambda e: self._dirty_check(), add="+")

        foot = tk.Frame(inner, bg=C["card"])
        foot.pack(fill="x", pady=(8, 0))
        self.btn_save = FlatButton(foot, "Save changes", self.save, width=140, height=40,
                                   size=9)
        self.btn_save.pack(side="left")
        FlatButton(foot, "Change password", self._change_password, kind="outline",
                   width=150, height=40, size=9).pack(side="left", padx=(10, 0))
        self.status = tk.Label(foot, text="", font=font(9), fg=C["success"], bg=C["card"])
        self.status.pack(side="left", padx=14)

        # ── Danger zone card
        zone = tk.Frame(self.content, bg=C["card"], highlightthickness=1,
                        highlightbackground=EDGE, highlightcolor=EDGE)
        zone.pack(fill="x", pady=(16, 0))
        tk.Label(zone, text="Danger zone", font=font(10, "bold"), fg=C["accent"],
                 bg=C["card"], anchor="w").pack(fill="x", padx=24, pady=(12, 8))
        self._danger_row(zone, "Log out of all devices",
                         "Ends every active session except this one.",
                         "Log out everywhere", "outline", self._logout_everywhere)
        self._danger_row(zone, "Delete account",
                         "Removes your profile, orders, and reservations.",
                         "Delete account", "danger", self._delete_account)

    def _danger_row(self, parent, title, desc, button, kind, command):
        tk.Frame(parent, height=1, bg=EDGE).pack(fill="x")
        row = tk.Frame(parent, bg=C["card"])
        row.pack(fill="x", padx=24, pady=11)
        text = tk.Frame(row, bg=C["card"])
        text.pack(side="left")
        tk.Label(text, text=title, font=font(10, "bold"), fg=C["ink"], bg=C["card"],
                 anchor="w").pack(anchor="w")
        tk.Label(text, text=desc, font=font(9), fg=C["muted"], bg=C["card"],
                 anchor="w").pack(anchor="w")
        FlatButton(row, button, command, kind=kind, size=9, width=160,
                   height=36).pack(side="right")

    # ── data
    def _email(self):
        return self.controller.state.get("email")

    def _values(self):
        return (self.first.get().strip(), self.last.get().strip(),
                self.email.get().strip().lower(), self.phone.get().strip())

    def _dirty_check(self):
        self.btn_save.set_enabled(self._values() != self._loaded)
        self.status.config(text="")

    def on_show(self, **kwargs):
        super().on_show(**kwargs)
        if self._email():                       # (not redirected to the landing page)
            self._load()

    def _load(self):
        record = get_customer(self._email()) or {}
        first, _, last = record.get("name", "").partition(" ")
        self.first.set(first)
        self.last.set(last.strip())
        self.phone.set(record.get("phone", ""))
        self.email.set(record.get("email", ""))
        self._loaded = self._values()
        self._paint_photo()
        self.btn_save.set_enabled(False)
        self.status.config(text="")

    def _paint_photo(self):
        photo = self.controller.state.get("photo")
        self.photo_avatar.set(self.controller.state["name"].strip()[:1] or "?",
                        load_avatar(photo, 64))
        self.btn_remove.set_enabled(bool(photo))

    # ── actions
    def save(self):
        old_email = self._email()
        if not old_email:
            self.controller.toast("Log in to edit your profile.")
            return
        fields = (self.first, self.last, self.email, self.phone)
        results = [f.validate() for f in fields]
        if not all(results):
            fields[results.index(False)].focus()
            return
        first, last, email, phone = self._values()
        if (first, last, email, phone) == self._loaded:
            return
        if email != old_email:                    # changing the login needs the password
            if not confirm_dialog(self, "Change your email?",
                                  f"You will log in with {email} from now on. "
                                  "Enter your password to confirm.",
                                  "Change email", password_for=old_email):
                return
            error = change_customer_email(old_email, email)
            if error:
                self.email.set_error(error)
                self.email.focus()
                return
            self.controller.state["email"] = email
        name = f"{first} {last}".strip()
        error = update_customer(email, name=name, phone=phone or None)
        if error:
            self.controller.toast(error)
            return
        self.controller.state["name"] = name
        self._loaded = (first, last, email, phone)
        self.refresh_user()
        self._paint_photo()
        self.btn_save.set_enabled(False)
        self.status.config(text="Changes saved.")
        self.focus_set()

    def _change_password(self):
        email = self._email()
        if not email:
            self.controller.toast("Log in to change your password.")
            return
        if password_dialog(self, email):
            # sign out every other device, stay signed in here
            self.controller.state["session_version"] = bump_session_version(email)
            self.status.config(text="Password updated.")

    def _change_photo(self):
        email = self._email()
        if not email:
            return
        kinds = ("*.png *.jpg *.jpeg *.gif *.bmp *.webp" if pillow_installed()
                 else "*.png *.gif")
        path = filedialog.askopenfilename(parent=self, title="Choose a profile photo",
                                          filetypes=[("Images", kinds)])
        if not path:
            return
        filename, error = save_avatar(email, path)
        if error:
            messagebox.showerror("Profile photo", error, parent=self)
            return
        old = self.controller.state.get("photo")
        update_customer(email, photo=filename)
        if old and old != filename:
            remove_avatar(old)
        self.controller.state["photo"] = filename
        self._paint_photo()
        self.refresh_user()
        self.controller.toast("Profile photo updated.")

    def _remove_photo(self):
        email, photo = self._email(), self.controller.state.get("photo")
        if not (email and photo):
            return
        update_customer(email, photo=None)
        remove_avatar(photo)
        self.controller.state["photo"] = None
        self._paint_photo()
        self.refresh_user()
        self.controller.toast("Profile photo removed.")

    def _logout_everywhere(self):
        email = self._email()
        if not email:
            return
        if confirm_dialog(self, "Log out of all devices?",
                          "This signs your account out everywhere else. "
                          "You'll stay logged in on this device.",
                          "Log out everywhere"):
            self.controller.state["session_version"] = bump_session_version(email)
            self.controller.toast("Signed out of all other sessions.")

    def _delete_account(self):
        email = self._email()
        if not email:
            return
        if confirm_dialog(self, "Delete your account?",
                          "This permanently removes your profile, orders and "
                          "reservations. This can't be undone.",
                          "Delete account", password_for=email):
            delete_customer(email)
            self.controller.logout("Your account has been deleted.")


if __name__ == "__main__":
    import main
    main.App("profile").mainloop()
