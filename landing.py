"""Landing page: one message, one illustration, two actions.

Design choices: a single focal point (the headline + primary button), lots of
whitespace on an 8-pt rhythm, and only one decorative card in the illustration.
"""
import tkinter as tk
from datetime import datetime

from main import C, SP, FlatButton, LinkLabel, Logo, Page, font, round_rect


class HeroArt(tk.Canvas):
    """A covered serving dish on a soft disc, with a single status card."""

    W = H = 400

    def __init__(self, parent):
        super().__init__(parent, width=self.W, height=self.H, bg=C["bg"],
                         highlightthickness=0)
        self.create_oval(30, 30, 370, 370, fill="#F4DAD4", outline="")           # disc
        self.create_oval(70, 70, 330, 330, fill="#FFFFFF", outline="#E8DED0",
                         width=2)                                                 # plate
        # serving dome (cloche) with a handle, steam and a chilli on the plate
        self.create_oval(96, 252, 304, 292, fill="#E8DED0", outline="")           # shadow
        self.create_arc(112, 120, 288, 296, start=0, extent=180, fill="#C8501A",
                        outline="#A63F12", width=2)                               # dome
        self.create_arc(134, 142, 220, 228, start=70, extent=60, style="arc",
                        outline="#E98A5C", width=4)                               # shine
        self.create_rectangle(104, 205, 296, 216, fill="#A63F12", outline="")     # rim
        self.create_oval(190, 100, 210, 120, fill="#F4DAD4", outline="#A63F12",
                         width=2)                                                 # handle
        for sx in (170, 200, 230):                                               # steam
            self.create_line(sx, 92, sx - 8, 78, sx + 8, 64, sx, 50, smooth=True,
                             fill="#D9CFC2", width=3, capstyle="round")
        self.create_oval(250, 222, 290, 236, fill="#2E7D32", outline="")          # chilli
        self.create_oval(246, 224, 262, 236, fill="#6FAE5B", outline="")
        # the one floating card
        x1, y1, x2, y2 = 188, 302, 392, 368
        round_rect(self, x1 + 2, y1 + 4, x2 + 2, y2 + 4, 16, fill="#E4CBC4", outline="")
        round_rect(self, x1, y1, x2, y2, 16, fill="#FFFFFF", outline="#EADFD2")
        self.create_oval(x1 + 18, y1 + 26, x1 + 32, y1 + 40, fill="#2E7D32", outline="")
        self.create_text(x1 + 46, y1 + 24, text="Order ready", anchor="w", fill=C["ink"],
                         font=font(10, "bold"))
        self.create_text(x1 + 46, y1 + 45, text="Counter 2  •  just now", anchor="w",
                         fill=C["muted"], font=font(9))


class LandingPage(Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        bg = C["bg"]

        # ── top bar: brand on the left, one quiet link on the right
        nav = tk.Frame(self, bg=bg)
        nav.pack(fill="x", padx=SP["xxl"], pady=(SP["lg"], 0))
        brand = tk.Frame(nav, bg=bg)
        brand.pack(side="left")
        Logo(brand, size=40, bg=bg).pack(side="left")
        tk.Label(brand, text="Feast Fast", font=font(14, "bold"), fg=C["ink"],
                 bg=bg).pack(side="left", padx=SP["md"] - 4)
        LinkLabel(nav, "Staff Portal", lambda: controller.show("manager_login"),
                  fg=C["muted"], bg=bg, size=10).pack(side="right")
        LinkLabel(nav, "About Us", lambda: controller.show("about_public"),
                  fg=C["muted"], bg=bg, size=10).pack(side="right", padx=(0, 24))

        tk.Label(self, text=f"© {datetime.now().year} Feast Fast", font=font(9),
                 fg=C["muted"], bg=bg).pack(side="bottom", pady=SP["lg"])

        # ── hero: text left, illustration right
        body = tk.Frame(self, bg=bg)
        body.pack(fill="both", expand=True, padx=SP["xxl"])
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=0, minsize=HeroArt.W)
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=bg)
        left.grid(row=0, column=0, sticky="w")
        tk.Label(left, text="Skip the queue.", font=font(36, "bold"), fg=C["ink"],
                 bg=bg).pack(anchor="w")
        tk.Label(left, text="Savor every bite.", font=font(36, "bold"), fg=C["primary"],
                 bg=bg).pack(anchor="w")
        tk.Label(left, text="Order your favourite food ahead and pick it up the "
                            "moment it's ready.",
                 font=font(12), fg=C["muted"], bg=bg, wraplength=400,
                 justify="left").pack(anchor="w", pady=(SP["lg"], 0))

        cta = tk.Frame(left, bg=bg)
        cta.pack(anchor="w", pady=(SP["xl"] + SP["sm"], 0))
        FlatButton(cta, "Customer Login", lambda: controller.show("customer_login"),
                   width=168, height=48).pack(side="left")
        FlatButton(cta, "Create Account", lambda: controller.show("create_account"),
                   kind="outline", width=168, height=48).pack(side="left", padx=SP["md"])

        tk.Label(left, text="Order ahead   •   Reserve a table   •   Track live",
                 font=font(10), fg=C["muted"], bg=bg).pack(anchor="w",
                                                          pady=(SP["xxl"], 0))

        HeroArt(body).grid(row=0, column=1, sticky="e")


if __name__ == "__main__":
    import main
    main.App("landing").mainloop()
