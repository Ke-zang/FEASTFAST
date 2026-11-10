"""Beverage menu category (page name: see main.PAGES)."""
from menu_page import MenuPage


class BeveragePage(MenuPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, category="Beverage")


if __name__ == "__main__":
    import main
    main.App("beverage").mainloop()
