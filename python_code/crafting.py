import pygame

from python_code.constants import CRAFTING_LAYER, CRAFTING_WINDOW_SIZE, SCREEN_SIZE, CRAFTING_WINDOW_POS, FONT30
from python_code.utilities import Size
from python_code.event_handling import EventHandler
from python_code.widgets import Frame, Label, ScrollPane, ItemLabel

class CraftingInterface(EventHandler):
    def __init__(self, terminal_inventory, *groups):
        EventHandler.__init__(self, [])
        self.__window = CraftingWindow(terminal_inventory, *groups)

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
    def __init__(self, terminal_inventory, *groups):
        Frame.__init__(self, CRAFTING_WINDOW_POS, CRAFTING_WINDOW_SIZE,
                       *groups, layer=CRAFTING_LAYER, color=self.COLOR,
                       title = "CRAFTING:")
        self.visible = False
        self.static = False
        self._crafting_grid = [[]]
        self.__inventory = terminal_inventory
        self.__no_items = self.__inventory.number_of_items
        self.__inventory_sp = None
        self.__innitiate_widgets()


    def update(self, *args):
        super().update(*args)
        if not self.visible:
            return
        if self.__no_items != self.__inventory.number_of_items:
            self.__no_items = self.__inventory.number_of_items
            self.__check_item_labels()

    def __check_item_labels(self):
        covered_items = [widget.item.name for widget in self._inventory_sp.widgets]
        for item in self.__inventory.items:
            if item.name not in covered_items:
                image = pygame.Surface((88, 88))
                image.fill(self.COLOR[:-1])
                center = pygame.transform.scale(item.surface, (75,75))
                image.blit(center, (88 / 2 - 75 / 2, 88 / 2 - 75 / 2))
                lbl = ItemLabel((0, 0), (88, 88), item, image=image)
                self._inventory_sp.add_widget(lbl)


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
        self._inventory_sp  = ScrollPane((500, 50), (175, 450), (175, 800), color=self.COLOR)
        self.add_widget(self._inventory_sp)
        # for item in self.__get_unique_items():
        #     print(item)
        #     lbl = Label((0, 0), (100, 100), (255, 255, 255))
        #     sp.add_widget(lbl)



# class ScrollableInventory(Entity):
#     def __init__(self, pos, size, board_inventories, *groups):
#         Entity.__init__(self, pos, size, *groups)
#         self.inventorie_blocks = board_inventories
#         self.static = False
#
#     # def _create_image(self, size, color, **kwargs):



