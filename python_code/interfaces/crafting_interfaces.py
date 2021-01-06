import pygame

import interfaces.widgets as widgets
import interfaces.base_interface as base_interface
import utility.constants as con
import utility.utilities as util
import utility.image_handling as image_handlers
import block_classes.block_utility as block_util
import inventories


class CraftingWindow(base_interface.Window):
    """
    A Frame for the crafting GUI
    """
    SIZE = util.Size(300, 250)

    def __init__(self, craft_building, *groups, recipes=None, **kwargs):
        self._craft_building = craft_building
        fr = self._craft_building.rect
        location = fr.bottomleft
        base_interface.Window.__init__(self, location, self.SIZE, *groups, static=True, **kwargs)

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
            self._crafting_time[0] += con.GAME_TIME.get_time()
            over_time = self._crafting_time[1] - self._crafting_time[0]
            if over_time <= 0:
                self._crafting = False
                self._crafting_time[0] = abs(over_time)
                item = inventories.Item(self._craftable_item_recipe._material(), self._craftable_item_recipe.quantity)
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

    def _create_recipe_selector(self, loc, size, color):
        # #create scrollable inventory
        inventory_s = widgets.ScrollPane(size, color=color)
        self.add_widget(loc, inventory_s)
        self.add_border(inventory_s)

        s1 = widgets.SelectionGroup()
        for recipe in self._recipe_book:
            # create an image with a background
            background = pygame.Surface((30, 30)).convert()
            background.fill(self.COLOR[:-1])
            image = pygame.transform.scale(recipe.get_image(), (26, 26))
            background.blit(image, (2, 2, 26, 26))

            tooltip = widgets.Tooltip(self.groups()[0], text=recipe.get_tooltip_text())
            lbl = widgets.Label((30, 30), color=color, image=background, tooltip=tooltip)

            lbl.add_key_event_listener(1, self.recipe_action, values=[recipe, lbl, s1], types=["unpressed"])
            s1.add(lbl)
            inventory_s.add_widget(lbl)

    def recipe_action(self, recipe, lbl, s1):
        self._crafting = False
        self._craftable_item_recipe = recipe
        s1.select(lbl, (0, 0, 0))
        self.grid_pane.add_recipe(recipe)
        self._craft_building.inventory.in_filter.set_whitelist(*[item.name() for item in recipe.needed_items])
        self._craft_building.inventory.out_filter.set_whitelist(recipe._material.name())
        if recipe._material.name() in self._craft_building.inventory:
            item = self._craft_building.inventory.item_pointer(recipe._material.name())
        else:
            item = inventories.Item(recipe._material(), 0)
            self._craft_building.inventory.add_items(item, ignore_filter=True)
        self._craftable_item_lbl.add_item(item)
        self._crafting_time[1] = recipe.CRAFTING_TIME


class FactoryWindow(CraftingWindow):
    SIZE = util.Size(300, 250)

    def __init__(self, craft_building, *groups, recipes=None):
        super().__init__(craft_building, *groups, recipes=recipes, title = "CRAFTING:")
        self._grid_pane = None
        self._craftable_item_lbl = None
        self.__init_widgets()

    def __init_widgets(self):
        """
        Innitiate all the widgets neccesairy for the crafting window at the
        start
        """
        #create material_grid
        self.grid_pane = CraftingGrid((125, 125), util.Size(4, 4), self._craft_building.inventory, color = (50, 50, 50))
        self.add_widget((10, 10), self.grid_pane)

        #add label to display the possible item image
        self._craftable_item_lbl = widgets.ItemDisplay((50, 50), None, border=False, color=self.COLOR[:-1], selectable=False)
        self.add_widget((200, 50), self._craftable_item_lbl)
        self.add_border(self._craftable_item_lbl)

        self._create_recipe_selector((10, 150), (280, 90), self.COLOR[:-1])

        #add arrow pointing from grid to display
        a_lbl = ProgressArrow((50, 50), self._crafting_time, color=con.INVISIBLE_COLOR)
        self.add_widget((140, 50), a_lbl)


class FurnaceWindow(CraftingWindow):
    SIZE = util.Size(240, 220)

    def __init__(self, furnace_object, *groups, recipes=None):
        super().__init__(furnace_object, *groups, recipes=recipes, title="FURNACE")
        self.__init_widgets()
        self.__requested_fuel = False

    def update(self):
        super().update()
        #configure fuel based on inventory fuel items.
        total_fuel = 0
        for mat_name in [f.name() for f in block_util.fuel_materials]:
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
            self._crafting_time[0] += con.GAME_TIME.get_time()
            over_time = self._crafting_time[1] - self._crafting_time[0]
            if over_time <= 0:
                self._crafting = False
                self.__requested_fuel = False
                self._crafting_time[0] = abs(over_time)
                item = inventories.Item(self._craftable_item_recipe._material(), self._craftable_item_recipe.quantity)
                self._craft_building.inventory.add_items(item, ignore_filter=True)
                self._craft_building.pushed_items.append(item)
                self.__fuel_meter.add_fuel(-1 * self._craftable_item_recipe.FUEL_CONSUMPTION)
                for item in self._craftable_item_recipe.needed_items:
                    self._craft_building.inventory.get(item.name(), item.quantity, ignore_filter=True)

    def __init_widgets(self):
        #create material_grid
        self.grid_pane = CraftingGrid((64, 64), util.Size(2, 2), self._craft_building.inventory, color = (50, 50, 50))
        self.add_widget((40, 28), self.grid_pane)

        self.__fuel_meter = FuelMeter((25, 100))
        self.add_widget((10,10), self.__fuel_meter)

        # add arrow pointing from grid to displa
        a_lbl = ProgressArrow((50, 50), self._crafting_time, color=con.INVISIBLE_COLOR)
        self.add_widget((110, 35), a_lbl)

        self._craftable_item_lbl = widgets.ItemDisplay((50, 50), None, border=False, color=(150, 150, 150), selectable=False)
        self.add_widget((170, 32), self._craftable_item_lbl)
        self.add_border(self._craftable_item_lbl, color=(75, 75, 75))

        self._create_recipe_selector((10, 120), (220, 90), self.COLOR[:-1])


class CraftingGrid(widgets.Pane):
    """
    Contains lables that are the represnetation of the crafting grid that can
    contain materials
    """
    COLOR = (173, 94, 29)
    BORDER_DISTANCE = 5
    def __init__(self, size, grid_size, inventory, **kwargs):
        super().__init__(size, **kwargs)
        self._crafting_grid = []
        self.__watching_inventory = inventory
        self.__prev_no_items = -1

        #variables that track a recipe material_grid and if it is changed
        self._recipe_grid = []
        self.__needed_materials = []
        self.__recipe_changed = False

        self.__init_grid(grid_size)
        self.size = util.Size(len(self._crafting_grid[0]), len(self._crafting_grid))

    def wupdate(self, *args):
        super().wupdate()
        self.add_present_material_indicator()

    def __init_grid(self, grid_size):
        """
        Innitialize the crafting grid and fill it with CraftingLabels
        """
        start_pos = [5,5]
        #size of a grid square
        total_size = util.Size(*self.rect.size) - (self.BORDER_DISTANCE, self.BORDER_DISTANCE)
        grid_square = util.Size(*(total_size / grid_size)) - (1, 1)
        for row_i in range(grid_size.height):
            row = []
            for col_i in range(grid_size.width):
                pos = start_pos + grid_square * (col_i, row_i) + (2, 2)
                lbl = GridLabel(grid_square - (4, 4), color = self.COLOR)
                self.add_widget(pos, lbl)
                row.append(lbl)
            self._crafting_grid.append(row)

    def add_recipe(self, recipe):
        self.reset()
        self._recipe_grid = recipe.get_image_grid()
        self.__needed_materials = recipe.needed_items
        for row_i, row in enumerate(self._recipe_grid):
            for col_i, name_image in enumerate(row):
                name, image = name_image
                if image is not None:
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


class GridLabel(widgets.Label):
    POS_COLOR = (0, 255, 0, 100)
    NEG_COLOR = (255, 0, 0, 100)
    def __init__(self, size, **kwargs):
        super().__init__(size, selectable=False, **kwargs)
        self.__item_present = None
        self.__positive_mark = image_handlers.image_sheets["general"].image_at((80, 0), size=(10, 10))

        self.__negative_mark = image_handlers.image_sheets["general"].image_at((70, 0), size=(10, 10))
        self.__item_image = None

    def set_item(self, item_image):
        if item_image is not None:
            item_image = pygame.transform.scale(item_image, util.Size(*self.rect.size) - (4, 4))
            self.set_image(item_image)
        else:
            self.clean_surface()
        self.__item_image = item_image

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


class ProgressArrow(widgets.Label):
    def __init__(self, size, progress_list, **kwargs):
        super().__init__(size, selectable=False, **kwargs)
        self.__arrow_image = image_handlers.image_sheets["general"].image_at((0, 0), size=(20, 20))
        self.__full_progress_arrow = image_handlers.image_sheets["general"].image_at((0, 20), size=(20, 20))
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
        try:
            fraction_progress = min(1.0, self.__progress[0] / self.__progress[1])
        except ZeroDivisionError:
            fraction_progress = 0.0
        width = int(fraction_progress * full_rect.width)
        actual_rect = (*full_rect.topleft, width, full_rect.height)
        progress_arrow = self.__arrow_image.copy()
        progress_arrow.blit(self.__full_progress_arrow, actual_rect, actual_rect)
        self.set_image(progress_arrow)


class FuelMeter(widgets.Pane):
    MAX_FUEL = 100
    def __init__(self, size, max_fuel=MAX_FUEL, **kwargs):
        super().__init__(size, color=con.INVISIBLE_COLOR, **kwargs)
        self._fuel_lvl = 0
        self.__max_fuel = max_fuel

        self.__init_widgets()

    def __init_widgets(self):
        text_lbl = widgets.Label((25, 10), color=con.INVISIBLE_COLOR, selectable=False)
        text_lbl.set_text("Fuel", (0,0), font_size=16)
        self.add_widget((0,0), text_lbl)

        self.fuel_indicator = widgets.Label((20, self.rect.height - 20), color=con.INVISIBLE_COLOR, selectable=False)
        self.add_border(self.fuel_indicator)
        self.add_widget((2, 15), self.fuel_indicator)

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