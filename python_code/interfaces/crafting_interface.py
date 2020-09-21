from python_code.interfaces.widgets import *
from python_code.interfaces.base_interface import Window
from python_code.board.materials import Air
from python_code.utility.image_handling import image_sheets
from python_code.inventories import Item
from python_code.recipes import RecipeBook


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
        Window.__init__(self, location, self.SIZE, *groups, title = "CRAFTING:", allowed_events=[1, 3, K_ESCAPE])
        self.static = True
        #TODO move this
        self.__recipe_book = RecipeBook()
        self._grid_pane = None

        #just ti signify that this exists
        self.__inventory_sp = None
        self._craftable_item_lbl = None
        self.__innitiate_widgets()

        self._craftable_item_recipe = None
        self.__crafting = False
        #current target
        self.__crafting_time = [0, 0]

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
            pass
        return leftovers

    def update(self, *args):
        super().update(*args)
        if self._craftable_item_recipe != None and not self.__crafting:
            self.__cancel_requested_items()
            self.__crafting_time[0] = 0
            self.__factory.requested_items = [item.copy() for item in self._craftable_item_recipe.needed_materials]
            self.__crafting = True
        elif self.__crafting and self.__check_materials():
            self.__crafting_time[0] += GAME_TIME.get_time()
            over_time = self.__crafting_time[1] - self.__crafting_time[0]
            if over_time <= 0:
                self.__crafting = False
                self.__crafting_time[0] = abs(over_time)
                item = Item(self._craftable_item_recipe._material(), self._craftable_item_recipe.quantity)
                self.__factory.inventory.add_items(item, ignore_filter=True)
                self.__factory.pushed_items.append(item)
                for item in self._craftable_item_recipe.needed_materials:
                    self.__factory.inventory.get(item.name(), item.quantity)

    def __check_materials(self):
        for n_item in self._craftable_item_recipe.needed_materials:
            present = False
            for item in self.__factory.inventory.items:
                if item.name() == n_item.name() and item.quantity >= n_item.quantity:
                    present = True
                    break
            if not present:
                return False
        return True

    def __cancel_requested_items(self):
        """
        Add items to a list that will remove items from the inventory regardless of
        filters
        """
        delivered_materials = [item.copy() for item in self._craftable_item_recipe.needed_materials]
        for index, item in enumerate(self.__factory.requested_items):
            for d_index, d_item in enumerate(delivered_materials):
                if d_item.name() == item.name():
                    delivered_materials[d_index].quantity -= self.__factory.requested_items[index].quantity
                    if delivered_materials[d_index].quantity > 0:
                        self.__factory.pushed_items.append(delivered_materials[d_index])

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

        #add label to display the possible item image
        self._craftable_item_lbl = ItemLabel((200, 50), (50, 50), None, border=False, color=self.COLOR[:-1])
        self.add_widget(self._craftable_item_lbl)
        self.add_border(self._craftable_item_lbl)

        s1 = SelectionGroup()
        for recipe in self.__recipe_book:
            #create an image with a background
            background = pygame.Surface((30, 30)).convert()
            background.fill(self.COLOR[:-1])
            image = pygame.transform.scale(recipe.get_image(), (26,26))
            background.blit(image, (2,2,26,26))

            lbl = Label((0,0), (30,30), color=self.COLOR[:-1], image=background)
            def recipe_action(self, recipe, lbl, s1):
                self.__crafting = False
                self._craftable_item_recipe = recipe
                s1.select(lbl, (0, 0, 0))
                self.grid_pane.add_recipe(recipe)
                self.__factory.inventory.in_filter.set_whitelist(*[item.name() for item in recipe.needed_materials])
                self.__factory.inventory.out_filter.set_whitelist(recipe._material.name())
                #show an item in the label
                if recipe._material.name() in self.__factory.inventory:
                    item = self.__factory.inventory.item_pointer(recipe._material.name())
                else:
                    item = Item(recipe._material(), 0)
                    self.__factory.inventory.add_items(item, ignore_filter=True)
                self._craftable_item_lbl.add_item(item)

                self.__crafting_time[1] = recipe.CRAFTING_TIME
            lbl.set_action(1, recipe_action, values=[self, recipe, lbl, s1], types=["unpressed"])
            s1.add(lbl)
            self._inventory_sp.add_widget(lbl)

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
        start_pos = [5,5]
        for row_i in range(self.GRID_SIZE.height):
            row = []
            for col_i in range(self.GRID_SIZE.width):
                pos = start_pos + self.GRID_SQUARE * (col_i, row_i) + (2, 2)
                lbl = Label(pos, self.GRID_SQUARE - (4, 4), color = self.COLOR)
                self.add_widget(lbl)
                row.append(lbl)
            self._crafting_grid.append(row)

    def add_recipe(self, recipe):
        self.reset()
        for row_i, row in enumerate(recipe.get_image_grid()):
            for col_i, image in enumerate(row):
                if image != None:
                    image = pygame.transform.scale(image, Size(*self._crafting_grid[row_i][col_i].rect.size) - (4,4))
                    self._crafting_grid[row_i][col_i].set_image(image)

    def reset(self):
        for row in self._crafting_grid:
            for lbl in row:
                lbl.set_image(None)


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

