import pygame
from abc import ABC, abstractmethod

from python_code.constants import CRAFTING_LAYER, CRAFTING_WINDOW_SIZE, SCREEN_SIZE, CRAFTING_WINDOW_POS
from python_code.utilities import Size
from python_code.event_handling import EventHandler
from python_code.widgets import Frame, Label, ScrollPane, Button
from python_code import materials


#crafting globals
#this is for managing a selected item. I am not super happy with it.
SELECTED_LABEL = None

def select_a_widget(widget):
    global SELECTED_LABEL
    if SELECTED_LABEL and widget != SELECTED_LABEL:
        SELECTED_LABEL.set_selected(False)
    SELECTED_LABEL = widget


class CraftingInterface(EventHandler):
    """
    Contains all the crafting GUI and all associated methods
    """
    def __init__(self, terminal_inventory, *groups):
        EventHandler.__init__(self, [])
        self.__window = CraftingWindow(terminal_inventory, *groups)

    def show(self, value):
        """
        Toggle showing the crafting window or not. This also makes sure that no
        real updates are pushed while the window is invisible

        :param value: a boolean
        """
        self.__window.visible = value

    def handle_events(self, events):
        """
        Handle events issued by the user not consumed by the Main module

        :param events: a list of events
        """
        leftovers = super().handle_events(events)
        if self.__window.visible:
            self.__window.handle_events(events)

class CraftingWindow(Frame):
    """
    A Frame for the crafting GUI
    """
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

        #just ti signify that this exists
        self.__inventory_sp = None
        self.__innitiate_widgets()

    def update(self, *args):
        """
        Entity update method, add labels to the scroll pane when needed.

        :See: Entity.update()
        """
        super().update(*args)
        if self.__no_items < self.__inventory.number_of_items:
            self.__no_items = self.__inventory.number_of_items
            self.__add_item_labels()

    def __add_item_labels(self):
        """
        When more different items are encountered then previously in the
        inventory a new label is added for an item. The labels are added to the
        scrollpane

        First it is figured out what items are new and then a label for each is
        constructed
        """
        covered_items = [widget.item.NAME for widget in self._inventory_sp.widgets]
        for item in self.__inventory.items:
            if item.NAME not in covered_items:
                #remove the alpha channel
                lbl = ItemLabel((0, 0), item, color=self.COLOR[:-1])
                self._inventory_sp.add_widget(lbl)

    def __innitiate_widgets(self):
        """
        Innitiate all the widgets neccesairy for the crafting window at the
        start
        """
        #create grid
        start_pos = [25, 50]
        background_lbl = Label(start_pos, self.GRID_PIXEL_SIZE, color = (0,0,0))
        self.add_widget(background_lbl)
        start_pos[0] += 5; start_pos[1] += 5
        for row_i in range(self.GRID_SIZE.height):
            row = []
            for col_i in range(self.GRID_SIZE.width):
                #this is still a little wonky and does not work completely like you want
                pos = start_pos + self.GRID_SQUARE * (col_i, row_i) + (2, 2)
                lbl = CraftingLabel(pos, self.GRID_SQUARE - (4, 4), color = self.COLOR[:-1])
                self.add_widget(lbl)
                row.append(lbl)
            self._crafting_grid.append(row)

        #create scrollable inventory
        self._inventory_sp  = ScrollPane((500, 50), (175, 450), color=self.COLOR[:-1])
        self.add_widget(self._inventory_sp)
        self.add_border(self._inventory_sp)

        craft_button = Button((25, 525), (100, 40), text="CRAFT", border=True)
        self.add_widget(craft_button)


class CraftingLabel(Label):
    def __init__(self, pos, size, **kwargs):
        Label.__init__(self, pos, size, **kwargs)
        self.set_action(1, self.set_image, types=["pressed"])
        self.set_action(3, self.set_image, values=[False], types=["pressed"])

    def set_image(self, add = True):
        if SELECTED_LABEL == None:
            return
        image = None
        if add:
            image = SELECTED_LABEL.item_image
        super().set_image(image)


class ItemLabel(Label):
    """
    Specialized label specifically for displaying items
    """
    SIZE = Size(42, 42)
    ITEM_SIZE = Size(30, 30)
    def __init__(self, pos, item, **kwargs):
        self.item = item
        #is set when innitailising label, just to make sure
        self.item_image = None
        Label.__init__(self, pos, self.SIZE, **kwargs)
        self.previous_total = self.item.quantity
        # when innitiating make sure the number is displayed
        self.set_text(str(self.previous_total), (10, 10),
                      color=self.item.TEXT_COLOR)
        self.set_action(1, self.set_selected, [True], ["pressed"])

    def _create_image(self, size, color, **kwargs):
        """
        Customized image which is an image containing a block and a border

        :See: Label._create_image()
        :return: pygame Surface object
        """
        # create a background surface
        image = pygame.Surface(self.SIZE)
        image.fill(color)

        # get the item image and place it in the center
        self.item_image = pygame.transform.scale(self.item.surface, self.ITEM_SIZE)
        image.blit(self.item_image, (self.SIZE.width / 2 - self.ITEM_SIZE.width / 2,
                            self.SIZE.height / 2 - self.ITEM_SIZE.height / 2))

        # draw rectangle slightly smaller then image
        rect = image.get_rect()
        rect.inflate_ip(-4, -4)
        pygame.draw.rect(image, (0, 0, 0), rect, 3)
        return image

    def set_selected(self, selected):
        super().set_selected(selected)
        if selected:
            select_a_widget(self)

    def wupdate(self):
        """
        Make sure to update the amount whenever it changes.
        """
        if self.previous_total != self.item.quantity:
            self.previous_total = self.item.quantity
            self.set_text(str(self.previous_total), (10, 10), color=self.item.TEXT_COLOR)


class RecipeGrid:
    def __init__(self, rows, columns):
        self.size = Size(columns, rows)
        self.grid = [[[None] for _ in range(columns)] for _ in range(rows)]

    def add_all_rows(self, *values):
        for index, row in enumerate(values):
            self.add_row(row, index)

    def add_row(self, value, row_i):
        self.grid[row_i] = value

    def add_value(self, value, column_i, row_i):
        self.grid[row_i][column_i] = value

    def __getitem__(self, item):
        return self.grid[item]

    def __len__(self):
        return len(self.grid)

    def print(self, attribute):
        for row in self.grid:
            attr_values = [getattr(value, attribute) for value in row]
            str_values = list(map(str, attr_values))
            value_format = "{:" + str(self.__longest_string(str_values) + 2) + "}"
            s = (value_format * self.size.width)
            str_row = s.format(*str_values)
            print(str_row)

    def __longest_string(self, strings):
        longest = 0
        for string in strings:
            if len(string) > longest:
                longest = len(string)
        return longest


class RMat:
    def __init__(self, name, group):
        self._material_type = getattr(materials, name)
        self.name = name
        #add the materials to groups that tell what group is required. Group 0
        #is always required
        self.group = group

    @property
    def required(self):
        return self.group == 0

    def __getattr__(self, item):
        return getattr(self.__material, item)


class BaseRecipe:
    def __init__(self):
        self.recipe_grid = self._create_recipe_grid()

    @abstractmethod
    def _create_recipe_grid(self):
        """
        Method to define a recipe grid
        :return: a RecipeGrid object
        """
        return None

    def size(self):
        return Size(len(self.recipe_grid[0]),len(self.recipe_grid))


class FurnaceRecipe(BaseRecipe):
    def __init__(self):
        BaseRecipe.__init__(self)

    def _create_recipe_grid(self):
        grid = RecipeGrid(7,7)

        top_row = [RMat("Stone", 5), RMat("Stone", 5), RMat("Stone", 3), RMat("Stone", 3), RMat("Stone", 3), RMat("Stone", 5), RMat("Stone", 5)]
        second_row = [RMat("Stone", 5), RMat("Ore", 5), RMat("Ore", 3), RMat("Ore", 3), RMat("Ore", 3), RMat("Ore", 5), RMat("Stone", 5)]
        third_row = [RMat("Stone", 2),RMat("Ore", 2),RMat("Stone", 0),RMat("Stone", 0),RMat("Stone", 0),RMat("Ore", 1),RMat("Stone", 1)]
        fourth_row = [RMat("Stone", 2), RMat("Ore", 2), RMat("Stone", 0), RMat("Coal", 0), RMat("Stone", 0), RMat("Ore", 1), RMat("Stone", 1)]
        fifth_row = [RMat("Stone", 2),RMat("Ore", 2),RMat("Stone", 0),RMat("Stone", 0),RMat("Stone", 0),RMat("Ore", 1),RMat("Stone", 1)]
        sixt_row = [RMat("Stone", 5), RMat("Ore", 5), RMat("Ore", 4), RMat("Ore", 4), RMat("Ore", 4), RMat("Ore", 5), RMat("Stone", 5)]
        last_row = [RMat("Stone", 5), RMat("Stone", 5), RMat("Stone", 4), RMat("Stone", 4), RMat("Stone", 4), RMat("Stone", 5), RMat("Stone", 5)]

        grid.add_all_rows(top_row, second_row, third_row, fourth_row,
                          fifth_row, sixt_row, last_row)
        return grid
