from python_code.entities import Entity
from python_code.constants import CRAFTING_LAYER, CRAFTING_WINDOW_SIZE, SCREEN_SIZE, CRAFTING_WINDOW_POS

class CraftingInterface:
    def __init__(self, *groups):
        self.__window = CraftingWindow(*groups)

    def show(self, value):
        self.__window.visible = value

class CraftingWindow(Entity):
    COLOR = (173, 94, 29, 150)
    def __init__(self, *groups):
        super().__init__(CRAFTING_WINDOW_POS, CRAFTING_WINDOW_SIZE, *groups, layer=CRAFTING_LAYER, color=self.COLOR)
        self.visible = False
        self.static = False
