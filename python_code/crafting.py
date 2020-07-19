import pygame

from python_code.entities import Entity
from python_code.constants import CRAFTING_LAYER, CRAFTING_WINDOW_SIZE, SCREEN_SIZE, CRAFTING_WINDOW_POS
from python_code.utilities import Size
from python_code.event_handling import EventHandler

class CraftingInterface(EventHandler):
    def __init__(self, *groups):
        EventHandler.__init__(self, [])
        self.__window = CraftingWindow(*groups)

    def show(self, value):
        self.__window.visible = value

    def handle_events(self, events):
        pass

class CraftingWindow(Entity):
    COLOR = (173, 94, 29, 150)
    GRID_SIZE = Size(9, 9)
    GRID_PIXEL_SIZE = Size(450, 450)
    GRID_SQUARE = Size(*GRID_PIXEL_SIZE / GRID_SIZE)
    def __init__(self, *groups):
        print(self.GRID_SQUARE)

        super().__init__(CRAFTING_WINDOW_POS, CRAFTING_WINDOW_SIZE, *groups,
                         layer=CRAFTING_LAYER, color=self.COLOR)
        self.visible = False
        self.static = False

    def _create_image(self, size, color, **kwargs):
        start_pos = (25,50)
        crafting_image = pygame.Surface(size).convert_alpha()
        crafting_image.fill(color)
        for row_i in range(self.GRID_SIZE.height):
            for col_i in range(self.GRID_SIZE.width):
                #this is still a little wonky and does not work completely like you want
                pos = Size(*self.GRID_SQUARE * (col_i, row_i)) + start_pos
                rect = pygame.Rect((*pos, *self.GRID_SQUARE))
                pygame.draw.rect(crafting_image, (0,0,0, 150), rect, 3)
        return crafting_image

