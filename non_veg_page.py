"""Non-vegetarian menu category (page name: see main.PAGES)."""
from menu_page import MenuPage


class NonVegPage(MenuPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, category="Non-Veg")


if __name__ == "__main__":
    import main
    main.App("non_veg").mainloop()
