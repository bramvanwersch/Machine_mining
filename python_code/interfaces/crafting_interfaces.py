from python_code.interfaces.widgets import *
from python_code.interfaces.base_interface import Window
from python_code.interfaces.widgets import Label
from python_code.utility.constants import INTERFACE_LAYER
from python_code.utility.image_handling import image_sheets
from python_code.inventories import Item
from python_code.utility.utilities import Size
from python_code.board.materials import fuel_values


class CraftingWindow(Window):
    """
    A Frame for the crafting GUI
    """
    SIZE = Size(300, 250)

    def __init__(self, craft_building, recipes, *groups, **kwargs):
        self._craft_building = craft_building
        fr = self._craft_building.rect
        location = fr.bottomleft
        Window.__init__(self, location, self.SIZE, *groups, static=True, **kwargs)

        self._recipe_book = recipes

        self._craftable_item_recipe = None
        self._crafting = False
        #current target
        self._crafting_time = [0, 1]

    def update(self, *args):
        super().update(*args)
        self._set_recipe()
        self._craft_item()

    def _set_recipe(self):
        if self._craftable_item_recipe != None and not self._crafting:
            self._crafting_time[0] = 0
            needed_items = [item.copy() for item in self._craftable_item_recipe.needed_items]
            for index, item in enumerate(needed_items):
                inventory_pointer = self._craft_building.inventory.item_pointer(item.name())
                if inventory_pointer == None:
                    continue
                item.quantity -= inventory_pointer.quantity
                if item.quantity <= 0:
                    del needed_items[index]
            self._craft_building.requested_items = needed_items
            self._crafting = True

    def _craft_item(self):
        if self._craftable_item_recipe != None and self._crafting and self._check_materials():
            self._crafting_time[0] += GAME_TIME.get_time()
            over_time = self._crafting_time[1] - self._crafting_time[0]
            if over_time <= 0:
                self._crafting = False
                self._crafting_time[0] = abs(over_time)
                item = Item(self._craftable_item_recipe._material(), self._craftable_item_recipe.quantity)
                self._craft_building.inventory.add_items(item, ignore_filter=True)
                self._craft_building.pushed_items.append(item)
                for item in self._craftable_item_recipe.needed_items:
                    self._craft_building.inventory.get(item.name(), item.quantity, ignore_filter=True)

    def _check_materials(self):
        for n_item in self._craftable_item_recipe.needed_items:
            present = False
            for item in self._craft_building.inventory.items:
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
        if self._craftable_item_recipe == None:
            return
        delivered_materials = [item.copy() for item in self._craftable_item_recipe.needed_items]
        for index, item in enumerate(self._craft_building.requested_items):
            for d_index, d_item in enumerate(delivered_materials):
                if d_item.name() == item.name():
                    delivered_materials[d_index].quantity -= self._craft_building.requested_items[index].quantity
                    if delivered_materials[d_index].quantity > 0:
                        self._craft_building.pushed_items.append(delivered_materials[d_index])

    def _create_recipe_selector(self, loc, size, color):
        # #create scrollable inventory
        inventory_s  = ScrollPane(loc, size, color=color)
        self.add_widget(inventory_s)
        self.add_border(inventory_s)

        s1 = SelectionGroup()
        for recipe in self._recipe_book:
            # create an image with a background
            background = pygame.Surface((30, 30)).convert()
            background.fill(self.COLOR[:-1])
            image = pygame.transform.scale(recipe.get_image(), (26, 26))
            background.blit(image, (2, 2, 26, 26))

            lbl = Label((0, 0), (30, 30), color=color, image=background)

            lbl.set_action(1, self.recipe_action, values=[recipe, lbl, s1], types=["unpressed"])
            s1.add(lbl)
            inventory_s.add_widget(lbl)

    def recipe_action(self, recipe, lbl, s1):
        self._crafting = False
        self.__cancel_requested_items()
        self._craftable_item_recipe = recipe
        s1.select(lbl, (0, 0, 0))
        self.grid_pane.add_recipe(recipe)
        self._craft_building.inventory.in_filter.set_whitelist(*[item.name() for item in recipe.needed_items])
        self._craft_building.inventory.out_filter.set_whitelist(recipe._material.name())
        if recipe._material.name() in self._craft_building.inventory:
            item = self._craft_building.inventory.item_pointer(recipe._material.name())
        else:
            item = Item(recipe._material(), 0)
            self._craft_building.inventory.add_items(item, ignore_filter=True)
        self._craftable_item_lbl.add_item(item)
        self._crafting_time[1] = recipe.CRAFTING_TIME


class FactoryWindow(CraftingWindow):
    SIZE = Size(300, 250)

    def __init__(self, craft_building, recipes, *groups):
        super().__init__(craft_building, recipes, *groups, title = "CRAFTING:", allowed_events=[1, K_ESCAPE])
        self._grid_pane = None
        self._craftable_item_lbl = None
        self.__init_widgets()

    def __init_widgets(self):
        """
        Innitiate all the widgets neccesairy for the crafting window at the
        start
        """
        #create material_grid
        self.grid_pane = CraftingGrid((10, 10), (125, 125), Size(4, 4), self._craft_building.inventory, color = (50, 50, 50))
        self.add_widget(self.grid_pane)

        #add label to display the possible item image
        self._craftable_item_lbl = ItemLabel((200, 50), (50, 50), None, border=False, color=self.COLOR[:-1])
        self.add_widget(self._craftable_item_lbl)
        self.add_border(self._craftable_item_lbl)

        self._create_recipe_selector((10, 150), (280, 90), self.COLOR[:-1])

        #add arrow pointing from grid to display
        a_lbl = ProgressArrow((140, 50), (50, 50), self._crafting_time, color=INVISIBLE_COLOR)
        self.add_widget(a_lbl)


class FurnaceWindow(CraftingWindow):
    SIZE = Size(240, 220)

    def __init__(self, furnace_object, recipes, *groups):
        super().__init__(furnace_object, recipes, *groups,layer=INTERFACE_LAYER, title = "FURNACE",
                        allowed_events=[1, K_ESCAPE])
        self.__init_widgets()
        self.__requested_fuel = False

    def update(self):
        super().update()
        #configure fuel based on inventory fuel items.
        total_fuel = 0
        for mat_name in fuel_values:
            fuel_pointer = self._craft_building.inventory.item_pointer(mat_name)
            if fuel_pointer != None and fuel_pointer.quantity > 0:
                total_fuel += fuel_pointer.FUEL_VALUE * fuel_pointer.quantity
                #remove the fuel
                fuel_pointer.quantity = 0
        self.__fuel_meter.add_fuel(total_fuel)

    def _set_recipe(self):
        super()._set_recipe()
        if self._craftable_item_recipe != None and not self.__requested_fuel:
            needed_fuel = self._craftable_item_recipe.FUEL_CONSUMPTION - self.__fuel_meter._fuel_lvl
            if needed_fuel > 0 and needed_fuel > self._craft_building.requested_fuel:
                self._craft_building.requested_fuel += needed_fuel
            self.__requested_fuel = True

    def _craft_item(self):
        if self._crafting and self._check_materials() and self.__fuel_meter._fuel_lvl >= self._craftable_item_recipe.FUEL_CONSUMPTION:
            self._crafting_time[0] += GAME_TIME.get_time()
            over_time = self._crafting_time[1] - self._crafting_time[0]
            if over_time <= 0:
                self._crafting = False
                self.__requested_fuel = False
                self._crafting_time[0] = abs(over_time)
                item = Item(self._craftable_item_recipe._material(), self._craftable_item_recipe.quantity)
                self._craft_building.inventory.add_items(item, ignore_filter=True)
                self._craft_building.pushed_items.append(item)
                self.__fuel_meter.add_fuel(-1 * self._craftable_item_recipe.FUEL_CONSUMPTION)
                for item in self._craftable_item_recipe.needed_items:
                    self._craft_building.inventory.get(item.name(), item.quantity, ignore_filter=True)

    def __init_widgets(self):
        #create material_grid
        self.grid_pane = CraftingGrid((40, 28), (64, 64), Size(2, 2), self._craft_building.inventory, color = (50, 50, 50))
        self.add_widget(self.grid_pane)

        self.__fuel_meter = FuelMeter((10,10), (25, 100))
        self.add_widget(self.__fuel_meter)

        # add arrow pointing from grid to displa
        a_lbl = ProgressArrow((110, 35), (50, 50), self._crafting_time, color=INVISIBLE_COLOR)
        self.add_widget(a_lbl)

        self._craftable_item_lbl = ItemLabel((170, 32), (50, 50), None, border=False, color=(150, 150, 150))
        self.add_widget(self._craftable_item_lbl)
        self.add_border(self._craftable_item_lbl, color=(75, 75, 75))

        self._create_recipe_selector((10, 120), (220, 90), self.COLOR[:-1])


class CraftingGrid(Pane):
    """
    Contains lables that are the represnetation of the crafting grid that can
    contain materials
    """
    COLOR = (173, 94, 29)
    BORDER_DISTANCE = 5
    def __init__(self, pos, size, grid_size, inventory, **kwargs):
        super().__init__(pos, size, **kwargs)
        self._crafting_grid = []
        self.__watching_inventory = inventory
        self.__prev_no_items = -1

        #variables that track a recipe material_grid and if it is changed
        self._recipe_grid = []
        self.__needed_materials = []
        self.__recipe_changed = False

        self.__init_grid(grid_size)
        self.size = Size(len(self._crafting_grid[0]), len(self._crafting_grid))

    def wupdate(self, *args):
        super().wupdate()
        self.add_present_material_indicator()

    def __init_grid(self, grid_size):
        """
        Innitialize the crafting grid and fill it with CraftingLabels
        """
        start_pos = [5,5]
        #size of a grid square
        total_size = Size(*self.rect.size) - (self.BORDER_DISTANCE, self.BORDER_DISTANCE)
        grid_square = Size(*(total_size / grid_size)) - (1, 1)
        for row_i in range(grid_size.height):
            row = []
            for col_i in range(grid_size.width):
                pos = start_pos + grid_square * (col_i, row_i) + (2, 2)
                lbl = GridLabel(pos, grid_square - (4, 4), color = self.COLOR)
                self.add_widget(lbl)
                row.append(lbl)
            self._crafting_grid.append(row)

    def add_recipe(self, recipe):
        self.reset()
        self._recipe_grid = recipe.get_image_grid()
        self.__needed_materials = recipe.needed_items
        for row_i, row in enumerate(self._recipe_grid):
            for col_i, name_image in enumerate(row):
                name, image = name_image
                if image != None:
                    self._crafting_grid[row_i][col_i].set_item(image)

    def add_present_material_indicator(self):
        already_present = {}
        for row_i, row in enumerate(self._recipe_grid):
            for col_i, name_image in enumerate(row):
                name, image = name_image
                needed_item = self.__watching_inventory.item_pointer(name)
                if needed_item == None:
                    self._crafting_grid[row_i][col_i].set_present(False)
                elif name in already_present and needed_item.quantity > already_present[name]:
                    already_present[name] += 1
                    self._crafting_grid[row_i][col_i].set_present(True)
                elif needed_item.quantity > 0 and name not in already_present:
                    already_present[name] = 1
                    self._crafting_grid[row_i][col_i].set_present(True)
                else:
                    self._crafting_grid[row_i][col_i].set_present(False)

    def reset(self):
        for row in self._crafting_grid:
            for lbl in row:
                lbl.set_item(None)
                lbl.set_present(None)


class GridLabel(Label):
    POS_COLOR = (0, 255, 0, 100)
    NEG_COLOR = (255, 0, 0, 100)
    def __init__(self, pos, size, **kwargs):
        super().__init__(pos, size, **kwargs)
        self.__item_present = None
        self.__positive_mark = image_sheets["general"].image_at((80, 0), size=(10, 10), color_key=(255, 255, 255))

        self.__negative_mark = image_sheets["general"].image_at((70, 0), size=(10, 10), color_key=(255, 255, 255))
        self.__item_image = None

    def set_item(self, item_image):
        if item_image != None:
            item_image = pygame.transform.scale(item_image, Size(*self.rect.size) - (4, 4))
        self.__item_image = item_image
        self.set_image(self.__item_image)

    def set_present(self, value):
        if value == self.__item_present:
            return
        self.__item_present = value
        if self.__item_image == None:
            return
        if value == True:
            image = self.__item_image.copy()
            image.blit(self.__positive_mark, (self.rect.width - 10 - 4, 0))
            self.set_image(image)
        else:
            image = self.__item_image.copy()
            image.blit(self.__negative_mark, (self.rect.width - 10 - 4, 0))
            self.set_image(image)


class ProgressArrow(Label):
    def __init__(self, pos, size, progress_list, **kwargs):
        super().__init__(pos, size, **kwargs)
        self.__arrow_image = image_sheets["general"].image_at((0, 0), size=(20, 20), color_key=(255, 255, 255))
        self.__full_progress_arrow = image_sheets["general"].image_at((0, 20), size=(20, 20), color_key=(255, 255, 255))
        self.__arrow_image = pygame.transform.scale(self.__arrow_image, size)
        self.__full_progress_arrow = pygame.transform.scale(self.__full_progress_arrow, size)
        self.__progress = progress_list
        self.__previous_progress = progress_list[0]
        self.__set_progress()

    def wupdate(self):
        super().wupdate()
        if self.__previous_progress != self.__progress[0]:
            self.__previous_progress = self.__progress[0]
            self.__set_progress()

    def __set_progress(self):
        full_rect = self.__full_progress_arrow.get_rect()
        fraction_progress = min(1, self.__progress[0] / self.__progress[1])
        width = int(fraction_progress * full_rect.width)
        actual_rect = (*full_rect.topleft, width, full_rect.height)
        progress_arrow = self.__arrow_image.copy()
        progress_arrow.blit(self.__full_progress_arrow, actual_rect, actual_rect)
        self.set_image(progress_arrow)


class FuelMeter(Pane):
    MAX_FUEL = 100
    def __init__(self, pos, size, max_fuel=MAX_FUEL, **kwargs):
        super().__init__(pos, size, color=INVISIBLE_COLOR, **kwargs)
        self._fuel_lvl = 0
        self.__max_fuel = max_fuel

        self.__init_widgets()

    def __init_widgets(self):
        text_lbl = Label((0,0), (25, 10), color=INVISIBLE_COLOR)
        text_lbl.set_text("Fuel", (0,0), font_size=16)
        self.add_widget(text_lbl)

        self.fuel_indicator = Label((2, 15), (20, self.rect.height - 20), color=INVISIBLE_COLOR)
        self.add_border(self.fuel_indicator)
        self.add_widget(self.fuel_indicator)

    def add_fuel(self, value):
        #dont allow above the max or under 0
        self._fuel_lvl = min(max(self._fuel_lvl + value, 0), self.MAX_FUEL)
        self.__change_fuel_indicator()

    def __change_fuel_indicator(self):
        full_image = pygame.Surface(self.fuel_indicator.rect.size)
        full_image.fill((150,150,150))
        img_height = int(self.fuel_indicator.rect.height * (self._fuel_lvl / self.__max_fuel))
        fuel_image = pygame.Surface((self.fuel_indicator.rect.width , img_height))
        fuel_image.fill((0,255,0))
        full_image.blit(fuel_image, (0, self.fuel_indicator.rect.height - img_height, self.fuel_indicator.rect.width , img_height))

        self.fuel_indicator.set_image(full_image, pos=(0, 0))
        self.add_border(self.fuel_indicator)