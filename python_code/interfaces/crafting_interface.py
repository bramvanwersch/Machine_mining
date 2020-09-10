from python_code.interfaces.widgets import *
from python_code.interfaces.base_interface import Window
from python_code.board.materials import Air
from python_code.utility.image_handling import image_sheets
from python_code.inventories import Item
from python_code.recipes import RecipeBook

#crafting globals
#this is for managing a selected item. I am not super happy with it.
SELECTED_LABEL = None

def select_a_widget(widget):
    """
    Select a widget from ScrollPane

    :param widget: a subclass of Widget object
    :return:
    """
    global SELECTED_LABEL
    if SELECTED_LABEL and widget != SELECTED_LABEL:
        SELECTED_LABEL.set_selected(False)
    SELECTED_LABEL = widget

class CraftingWindow(Window):
    """
    A Frame for the crafting GUI
    """
    CLOSE_LIST = ["BuildingWindow"]
    SIZE = Size(300, 250)
    def __init__(self, factory, *groups):
        self.__factory = factory
        fr = self.__factory.rect
        location = fr.bottomleft
        Window.__init__(self, location, self.SIZE,
                       *groups, title = "CRAFTING:", allowed_events=[1, 3, K_ESCAPE])
        self.static = True
        #TODO move this
        self.__recipe_book = RecipeBook()
        self._grid_pane = None

        #just ti signify that this exists
        self.__inventory_sp = None
        self._craftable_item_lbl = None
        self.__innitiate_widgets()

        self._craftable_item_recipe = None

    def update(self, *args):
        """
        Entity update method, add labels to the scroll pane when needed.

        :See: Entity.update()
        """
        super().update(*args)

    def handle_events(self, events):
        """
        Handle events issued by the user not consumed by the Main module. This
        function can also be used as an update method for all things that only
        need updates with new inputs.

        Note: this will trager quite often considering that moving the mouse is
        also considered an event.

        :param events: a list of events
        """
        leftovers = super().handle_events(events)
        if self.visible:
            #check if the recipe changed. If that is the case update the crafting window
            new_recipe_grid = self.grid_pane.get_new_recipe_grid()
            if new_recipe_grid:
                recipe = self.__recipe_book.get_recipe(new_recipe_grid)
                if recipe != None:
                    self._craftable_item_lbl.set_display(recipe.material)
                    self._craftable_item_recipe = recipe
                else:
                    self._craftable_item_lbl.set_display(None)
        return leftovers

    def __add_item_labels(self):
        """
        When more different items are encountered then previously in the
        inventory a new label is added for an item. The labels are added to the
        scrollpane

        First it is figured out what items are new and then a label for each is
        constructed
        """
        covered_items = [widget.item.name() for widget in self._inventory_sp.widgets]
        for item in self.__inventory.items:
            if item.name() not in covered_items:
                #remove the alpha channel
                lbl = ItemLabel((0, 0), item, color=self.COLOR[:-1])
                def set_selected(self, selected):
                    self.set_selected(selected)
                    if selected:
                        select_a_widget(self)
                lbl.set_action(1, set_selected, [lbl, True], ["pressed"])
                self._inventory_sp.add_widget(lbl)

    def __innitiate_widgets(self):
        """
        Innitiate all the widgets neccesairy for the crafting window at the
        start
        """
        #create material_grid
        self.grid_pane = CraftingGrid((10, 10), (125, 125), color = (50, 50, 50))
        self.add_widget(self.grid_pane)


        # #create scrollable inventory
        self._inventory_sp  = ScrollPane((10, 150), (280, 90), color=self.COLOR[:-1])
        self.add_widget(self._inventory_sp)
        self.add_border(self._inventory_sp)
        for recipe in self.__recipe_book:
            dl = Label((0,0), (30,30))
            dl.set_image(image=recipe.get_image(), size= (27, 27))
            self._inventory_sp.add_widget(dl)

        #add label to display the possible item image
        self._craftable_item_lbl = DisplayLabel((200, 50), (50, 50), color=self.COLOR[:-1])
        self.add_widget(self._craftable_item_lbl)
        self.add_border(self._craftable_item_lbl)

        #add arrow pointing from grid to display
        arrow_image = image_sheets["general"].image_at((0, 0), size=(20, 20), color_key=(255, 255, 255))
        arrow_image = pygame.transform.scale(arrow_image, (50,50))
        a_lbl = Label((140, 50), (50, 50), color=INVISIBLE_COLOR)
        a_lbl.set_image(arrow_image)
        self.add_widget(a_lbl)


class CraftingGrid(Pane):
    """
    Contains lables that are the represnetation of the crafting grid that can
    contain materials
    """
    COLOR = (173, 94, 29)
    GRID_SIZE = Size(4, 4)
    GRID_PIXEL_SIZE = Size(120, 120)
    # take the border into account
    GRID_SQUARE = Size(*(GRID_PIXEL_SIZE / GRID_SIZE)) - (1, 1)
    def __init__(self, pos, size, **kwargs):
        super().__init__(pos, size, **kwargs)
        self._crafting_grid = []

        #variables that track a recipe material_grid and if it is changed
        self._recipe_grid = []
        self.__recipe_changed = False

        self.__init_grid()
        self.size = Size(len(self._crafting_grid[0]), len(self._crafting_grid))

    def __init_grid(self):
        """
        Innitialize the crafting grid and fill it with CraftingLabels
        """
        start_pos= [5,5]
        for row_i in range(self.GRID_SIZE.height):
            row = []
            for col_i in range(self.GRID_SIZE.width):
                pos = start_pos + self.GRID_SQUARE * (col_i, row_i) + (2, 2)
                lbl = CraftingLabel(pos, self.GRID_SQUARE - (4, 4), color = self.COLOR)
                self.add_widget(lbl)
                row.append(lbl)
            self._crafting_grid.append(row)

    def wupdate(self, *args):
        """
        Trigger for updating widgets. Checks all the CraftingLabels for changes
        and finds a rectangle of selected labels when changes where made

        :param args: optional arguments
        """
        super().wupdate()
        updated_recipe = False
        for row in self._crafting_grid:
            for lbl in row:
                if lbl.changed_item and not updated_recipe:
                    self._recipe_grid = self._get_recipe_grid()
                    self.__recipe_changed = True
                lbl.changed_item = False

    def get_new_recipe_grid(self):
        """
        Get a new recipe grid, called when crafting labels change

        :return: a recipe grid or None when there is no change
        """
        if self.__recipe_changed:
            self.__recipe_changed = False
            return self._recipe_grid
        return None

    def _get_recipe_grid(self):
        """
        Get the recipe grid by finding a square of CraftingLabels that are have
        items in them

        :return: return a matrix of  CraftingLabels potentially with items in
        them
        """
        col_start = self.size.width
        col_end = 0
        row_start = self.size.height
        row_end = 0
        recipe_grid = []
        for row_i, row in enumerate(self._crafting_grid):
            material_row = [Air for _ in range(len(row))]
            material_present = False
            for col_i, lbl in enumerate(row):
                if lbl.item != None:
                    material_present = True
                    material_row[col_i] = type(lbl.item.material)
                    # figure out the start end end inxed of the items in the row
                    if col_i < col_start:
                        col_start = col_i
                        col_end = col_i
                    elif col_i > col_end:
                        col_end = col_i

            recipe_grid.append(material_row)
            if material_present:
                if row_i < row_start:
                    row_start = row_i
                    row_end = row_i
                elif row_i > row_end:
                    row_end = row_i

        #cut the material_grid to the right size
        reduced_recipe_grid = []
        for row_i in range(row_start, row_end + 1):
            reduced_recipe_grid.append(recipe_grid[row_i][col_start:col_end + 1])

        return reduced_recipe_grid


class CraftingLabel(Label):
    """
    Labels that can hold items as pictures in them
    """
    def __init__(self, pos, size, **kwargs):
        Label.__init__(self, pos, size, **kwargs)
        self.set_action(1, self.set_image, types=["pressed"])
        self.set_action(3, self.set_image, values=[False], types=["pressed"])
        self.changed_item = False
        self.item = None

    def set_image(self, add = True):
        """
        Change the image of the label
        
        :param add: boolean. If true the image of the self.item is added otherwise
        remove any image
        """
        if SELECTED_LABEL== None:
            return
        image = self.item = None
        if add:
            self.item = SELECTED_LABEL.item
            image = SELECTED_LABEL.item_image
        super().set_image(image)
        self.changed_item = True

class DisplayLabel(Label):
    """
    a label to display an image
    """
    def __init__(self, pos, size, **kwargs):
        super().__init__(pos, size, **kwargs)
        self.selected = True

    def set_display(self, material):
        """
        Set the display with a material image

        :param material: the material, can be None to clear the image
        :return:
        """
        if material == None:
            self.set_image(None)
        elif material != None:
            image = pygame.transform.scale(material.surface, Size(*self.rect.size) - (3,3))
            # text = self._create_text(block_inst)
            self.set_image(image)
            # self.set_image(text, pos=(100, 0))

    # def _create_text(self, block_inst):
    #     text_image = pygame.Surface((200, 75))
    #     text_image.fill(self.COLOR)
    #     name = FONTS[22].render("Name: {}".format(block_inst.MATERIAL.name().replace("Material", "")), True, (0,0,0))
    #     size = FONTS[22].render("Size: {} by {}".format(len(block_inst.blocks[0]), len(block_inst.blocks)), True, (0,0,0))
    #     text_image.blit(name, (0,0))
    #     text_image.blit(size, (0, 18))
    #     return text_image

