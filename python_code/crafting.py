import pygame

from python_code.constants import CRAFTING_LAYER, CRAFTING_WINDOW_SIZE, SCREEN_SIZE, CRAFTING_WINDOW_POS, FONT30
from python_code.utilities import Size
from python_code.event_handling import EventHandler
from python_code.widgets import Frame, Label, ScrollPane

class CraftingInterface(EventHandler):
    def __init__(self, board_inventories, *groups):
        EventHandler.__init__(self, [])
        self.__window = CraftingWindow(board_inventories, *groups)

    def show(self, value):
        self.__window.visible = value

    def handle_events(self, events):
        leftovers = super().handle_events(events)
        if self.__window.visible:
            self.__window.handle_events(events)

class CraftingWindow(Frame):
    COLOR = (173, 94, 29, 150)
    GRID_SIZE = Size(9, 9)
    GRID_PIXEL_SIZE = Size(450, 450)
    #take the border into account
    GRID_SQUARE = Size(*(GRID_PIXEL_SIZE / GRID_SIZE )) - (1, 1)
    def __init__(self, board_inventories, *groups):
        Frame.__init__(self, CRAFTING_WINDOW_POS, CRAFTING_WINDOW_SIZE,
                        *groups, layer=CRAFTING_LAYER, color=self.COLOR, title = "CRAFTING:")
        self.visible = False
        self.static = False
        self._crafting_grid = [[]]
        self.__innitiate_widgets()
        # self.__crafting_inventory = ScrollableInventory((525, 50), (250, 450), board_inventories, *groups)

    def update(self, *args):
        super().update(*args)
        if self.visible:
            pass

    def __innitiate_widgets(self):

        #create grid
        start_pos = [25, 50]
        background_lbl = Label(start_pos, self.GRID_PIXEL_SIZE, color = (0,0,0, 150))
        self.add_widget(background_lbl)
        start_pos[0] += 5; start_pos[1] += 5
        for row_i in range(self.GRID_SIZE.height):
            row = []
            for col_i in range(self.GRID_SIZE.width):
                #this is still a little wonky and does not work completely like you want
                pos = start_pos + self.GRID_SQUARE * (col_i, row_i) + (2, 2)
                lbl = Label(pos, self.GRID_SQUARE - (4, 4), color = self.COLOR)
                self.add_widget(lbl)
                row.append(lbl)
            self._crafting_grid.append(row)

        #create scrollable inventory
        sp  = ScrollPane((500, 50), (175, 450), (175, 800))
        self.add_widget(sp)
        lbl = Label((0,0), (100,100), (255,255,255))
        sp.add_widget(lbl)



# class ScrollableInventory(Entity):
#     def __init__(self, pos, size, board_inventories, *groups):
#         Entity.__init__(self, pos, size, *groups)
#         self.inventories = board_inventories
#         self.static = False
#
#     # def _create_image(self, size, color, **kwargs):



