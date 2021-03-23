import pygame
from abc import ABC, abstractmethod
from typing import Union, List, Tuple, TYPE_CHECKING, ClassVar

import interfaces.widgets as widgets
import interfaces.base_interface as base_interface
import utility.constants as con
import utility.utilities as util
from utility import image_handling
import block_classes.block_utility as block_util
from utility import inventories
if TYPE_CHECKING:
    from recipes import base_recipes


class CraftingWindow(base_interface.Window, ABC):
    SIZE = util.Size(300, 250)
    RECIPE_LABEL_SIZE: util.Size = util.Size(30, 30)

    def __init__(self, craft_building, *groups, recipes=None, **kwargs):
        self._craft_building = craft_building
        fr = self._craft_building.rect
        location = fr.bottomleft
        base_interface.Window.__init__(self, location, self.SIZE, *groups, static=True, **kwargs)

        self._recipe_book = recipes

        self._craftable_item_recipe = None
        self._crafting = False
        self._crafting_time = [0, 1]

        self.crafting_grid = self.create_crafting_grid()
        self.crafting_result_lbl = self.create_crafting_result_lbl()

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def CRAFT_GRID_SIZE(self) -> util.Size:
        pass

    def create_crafting_grid(self) -> "CraftingGrid":
        return CraftingGrid(self.CRAFT_GRID_SIZE, self._craft_building.inventory)

    @abstractmethod
    def create_crafting_result_lbl(self) -> widgets.ItemDisplay:
        pass

    def update(self, *args):
        super().update(*args)
        if self._craftable_item_recipe is not None:
            self._crafting = self._check_materials()

            self._craft_item()

    def _craft_item(self):
        if not self._crafting:
            return
        self._crafting_time[0] += con.GAME_TIME.get_time()
        over_time = self._crafting_time[1] - self._crafting_time[0]
        if over_time > 0:
            return
        self._crafting_time[0] = abs(over_time)
        item = inventories.Item(self._craftable_item_recipe.material(), self._craftable_item_recipe.quantity)

        # add the crated item
        self._craft_building.inventory.add_items(item, ignore_filter=True)

        # remove all items
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

    def _create_recipe_selector(
        self,
        loc: Union[Tuple[int, int], List[int]],
        size: Union[util.Size, Tuple[int, int], List[int]],
        color: Union[Tuple[int, int, int, int], Tuple[int, int, int], List[int]]
    ):
        recipe_scrollpane = widgets.ScrollPane(size, color=color)
        self.add_widget(loc, recipe_scrollpane)
        self.add_border(recipe_scrollpane)

        selection_group = widgets.SelectionGroup()
        for recipe in self._recipe_book:
            # create an image with a background
            background = pygame.Surface(self.RECIPE_LABEL_SIZE.size).convert()
            background.fill(self.COLOR[:-1])
            recipe_img_size = self.RECIPE_LABEL_SIZE - (4, 4)
            image = pygame.transform.scale(recipe.get_image(), recipe_img_size)
            background.blit(image, ((self.RECIPE_LABEL_SIZE.width - recipe_img_size.width) / 2,
                                    (self.RECIPE_LABEL_SIZE.height - recipe_img_size.height) / 2, *recipe_img_size))

            tooltip = widgets.Tooltip(self.groups()[0], text=recipe.get_tooltip_text())
            recipe_lbl = widgets.Label(self.RECIPE_LABEL_SIZE, color=color, image=background, tooltip=tooltip)

            recipe_lbl.add_key_event_listener(1, self.set_recipe, values=[recipe, recipe_lbl, selection_group],
                                              types=["unpressed"])
            selection_group.add(recipe_lbl)
            recipe_scrollpane.add_widget(recipe_lbl)

    def set_recipe(
        self,
        recipe: "base_recipes.BaseRecipe",
        lbl: widgets.Label,
        selection_group: widgets.SelectionGroup
    ):
        """Set a recipe as active recipe"""
        self._craftable_item_recipe = recipe
        selection_group.select(lbl, color=(0, 0, 0))
        self.crafting_grid.add_recipe(recipe)
        self._craft_building.inventory.in_filter.set_whitelist(*[item.name() for item in recipe.needed_items])
        self._craft_building.inventory.out_filter.set_whitelist(recipe.material.name())
        if recipe.material.name() in self._craft_building.inventory:
            item = self._craft_building.inventory.item_pointer(recipe.material.name())
        else:
            item = inventories.Item(recipe.material(), 0)
            self._craft_building.inventory.add_items(item, ignore_filter=True)
        self.crafting_result_lbl.add_item(item)
        self._crafting_time[1] = recipe.CRAFTING_TIME


class FactoryWindow(CraftingWindow):
    SIZE = util.Size(300, 250)
    CRAFT_GRID_SIZE: util.Size = util.Size(4, 4)

    def __init__(self, craft_building, *groups, recipes=None):
        super().__init__(craft_building, *groups, recipes=recipes, title="CRAFTING:")
        self.__init_widgets()

    def create_crafting_result_lbl(self) -> widgets.ItemDisplay:
        return widgets.ItemDisplay((50, 50), None, border=False, color=self.COLOR[:-1], selectable=False)

    def __init_widgets(self):
        """Innitiate all the widgets neccesairy for the crafting window at the start"""
        # create material_grid
        self.add_widget((10, 10), self.crafting_grid)

        # add label to display the possible item image
        self.add_widget((200, 50), self.crafting_result_lbl)
        self.add_border(self.crafting_result_lbl)

        self._create_recipe_selector((10, 150), (280, 90), self.COLOR[:-1])

        # add arrow pointing from grid to display
        arrow_lbl = ProgressArrow((50, 50), self._crafting_time, color=con.INVISIBLE_COLOR)
        self.add_widget((140, 50), arrow_lbl)


class FurnaceWindow(CraftingWindow):
    SIZE = util.Size(240, 220)
    CRAFT_GRID_SIZE: util.Size = util.Size(2, 2)

    def __init__(self, furnace_object, *groups, recipes=None):
        super().__init__(furnace_object, *groups, recipes=recipes, title="FURNACE")
        self.__fuel_meter = None
        self.__init_widgets()

    def create_crafting_result_lbl(self) -> widgets.ItemDisplay:
        return widgets.ItemDisplay((50, 50), None, border=False, color=(150, 150, 150), selectable=False)

    def __init_widgets(self):
        # create material_grid
        self.add_widget((40, 28), self.crafting_grid)

        self.__fuel_meter = FuelMeter((25, 100))
        self.add_widget((10, 10), self.__fuel_meter)

        # add arrow pointing from grid to displa
        arrow_lbl = ProgressArrow((50, 50), self._crafting_time, color=con.INVISIBLE_COLOR)
        self.add_widget((110, 35), arrow_lbl)

        self.add_widget((170, 32), self.crafting_result_lbl)
        self.add_border(self.crafting_result_lbl, color=(75, 75, 75))

        self._create_recipe_selector((10, 120), (220, 90), self.COLOR[:-1])

    def update(self):
        super().update()
        # configure fuel based on inventory fuel items.
        total_fuel = 0
        for mat_name in [f.name() for f in block_util.fuel_materials]:
            fuel_pointer = self._craft_building.inventory.item_pointer(mat_name)
            if fuel_pointer is not None and fuel_pointer.quantity > 0:
                total_fuel += fuel_pointer.FUEL_VALUE * fuel_pointer.quantity
                # remove the fuel
                fuel_pointer.quantity = 0
        self.__fuel_meter.add_fuel(total_fuel)

    def set_recipe(
        self,
        recipe: "base_recipes.BaseRecipe",
        lbl: widgets.Label,
        selection_group: widgets.SelectionGroup
    ):
        super().set_recipe(recipe, lbl, selection_group)
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
                item = inventories.Item(self._craftable_item_recipe.material(), self._craftable_item_recipe.quantity)
                self._craft_building.inventory.add_items(item, ignore_filter=True)
                self._craft_building.pushed_items.append(item)
                self.__fuel_meter.add_fuel(-1 * self._craftable_item_recipe.FUEL_CONSUMPTION)
                for item in self._craftable_item_recipe.needed_items:
                    self._craft_building.inventory.get(item.name(), item.quantity, ignore_filter=True)


class CraftingGrid(widgets.Pane):
    """Crafting grid for displaying recipes and the presence of items of those recipes"""
    COLOR: ClassVar[Union[Tuple[int, int, int], List[int]]] = (173, 94, 29)
    BORDER_DISTANCE: ClassVar[util.Size] = util.Size(5, 5)
    GRID_LABEL_SIZE: ClassVar[util.Size] = util.Size(25, 25)
    INBETWEEN_LABEL_SPACE: ClassVar[int] = 3

    _crafting_grid: List[List["_GridLabel"]]
    __watching_inventory: inventories.Inventory
    _recipe: Union[None, "base_recipes.BaseRecipe"]

    def __init__(self, grid_size, inventory, **kwargs):
        size = util.Size(self.BORDER_DISTANCE.width * 2 + self.GRID_LABEL_SIZE.width * grid_size.width +
                         (grid_size.width - 1) * self.INBETWEEN_LABEL_SPACE,
                         self.BORDER_DISTANCE.height * 2 + self.GRID_LABEL_SIZE.height * grid_size.height +
                         (grid_size.height - 1) * self.INBETWEEN_LABEL_SPACE)
        super().__init__(size, color=(50, 50, 50), **kwargs)
        self._crafting_grid = []
        self.__watching_inventory = inventory
        self._recipe = None

        self.__init_grid(grid_size)

    def __init_grid(
        self,
        grid_size: util.Size
    ):
        """Innitialize the crafting grid and fill it with CraftingLabels"""
        for row_i in range(grid_size.height):
            row = []
            for col_i in range(grid_size.width):
                pos = self.BORDER_DISTANCE + self.GRID_LABEL_SIZE * (col_i, row_i) + \
                      (self.INBETWEEN_LABEL_SPACE * col_i, self.INBETWEEN_LABEL_SPACE * row_i)
                lbl = _GridLabel(self.GRID_LABEL_SIZE, color=self.COLOR)
                self.add_widget(pos, lbl)
                row.append(lbl)
            self._crafting_grid.append(row)

    def wupdate(self, *args):
        super().wupdate()
        if self._recipe is not None:
            self._add_material_presence_indicators()

    def add_recipe(
        self,
        recipe: "base_recipes.BaseRecipe"
    ):
        """Add a recipe to the grid"""
        self.reset()
        self._recipe = recipe
        for row_i, row in enumerate(recipe.get_image_grid()):
            for col_i, name_image in enumerate(row):
                name, image = name_image
                if image is not None and name != "Air":
                    self._crafting_grid[row_i][col_i].set_item_image(image)

    def _add_material_presence_indicators(self):
        """Add small indicators to the grid labels that tell the user if certain items are present in the crafting
        station"""
        already_present = {}
        for row_i, row in enumerate(self._recipe.get_image_grid()):
            for col_i, name_image in enumerate(row):
                name, image = name_image
                needed_item = self.__watching_inventory.item_pointer(name)
                if needed_item is None:
                    self._crafting_grid[row_i][col_i].set_item_presence(False)
                elif name in already_present and needed_item.quantity > already_present[name]:
                    already_present[name] += 1
                    self._crafting_grid[row_i][col_i].set_item_presence(True)
                elif needed_item.quantity > 0 and name not in already_present:
                    already_present[name] = 1
                    self._crafting_grid[row_i][col_i].set_item_presence(True)
                else:
                    self._crafting_grid[row_i][col_i].set_item_presence(False)

    def reset(self):
        """Reset all the labels in the crafting grid for the indicators and the items"""
        for row in self._crafting_grid:
            for lbl in row:
                lbl.set_item_image(None)
                lbl.set_item_presence(False)


class _GridLabel(widgets.Label):
    POSITIVE_MARK: ClassVar[image_handling.ImageDefinition] = \
        image_handling.ImageDefinition("general", (80, 0), size=util.Size(10, 10))
    NEGATIVE_MARK: ClassVar[image_handling.ImageDefinition] = \
        image_handling.ImageDefinition("general", (70, 0), size=util.Size(10, 10))

    __item_image: Union[None, pygame.Surface]
    __positive_mark: pygame.Surface
    __negative_mark: pygame.Surface

    def __init__(
        self,
        size: Union[Tuple[int, int], List[int], util.Size],
        **kwargs
    ):
        super().__init__(size, selectable=False, **kwargs)
        self.__positive_mark = self.POSITIVE_MARK.images()[0]

        self.__negative_mark = self.NEGATIVE_MARK.images()[0]
        self.__item_image = None

    def set_item_image(
        self,
        item_image: Union[pygame.Surface, None]
    ):
        """Set the image of this label as the image of an item scaled to the label size"""
        if item_image is not None:
            item_image = pygame.transform.scale(item_image, util.Size(*self.rect.size) - (4, 4))
            self.set_image(item_image)
        else:
            self.clean_surface()
        self.__item_image = item_image

    def set_item_presence(
        self,
        value: bool
    ):
        """Change a mark in the cornor of the image that displayes if the item is present in the tracked inventory of
        the GridPane that holds this label"""
        if self.__item_image is None:
            return
        if value is True:
            image = self.__item_image.copy()
            image.blit(self.__positive_mark, (self.rect.width - 10 - 4, 0))
            self.set_image(image)
        else:
            image = self.__item_image.copy()
            image.blit(self.__negative_mark, (self.rect.width - 10 - 4, 0))
            self.set_image(image)


class ProgressArrow(widgets.Label):

    __arrow_image: pygame.Surface
    __full_progress_arrow: pygame.Surface
    __progress: List[int]
    __previous_progress: int

    def __init__(
        self,
        size: Union[Tuple[int, int], List[int], util.Size],
        crafting_progress: List[int],
        **kwargs
    ):
        super().__init__(size, selectable=False, **kwargs)
        self.__arrow_image = image_handling.image_sheets["general"].image_at((0, 0), size=(20, 20))
        self.__full_progress_arrow = image_handling.image_sheets["general"].image_at((0, 20), size=(20, 20))
        self.__arrow_image = pygame.transform.scale(self.__arrow_image, size)
        self.__full_progress_arrow = pygame.transform.scale(self.__full_progress_arrow, size)

        self.__progress = crafting_progress  # the progress that the current crafting process has [current, max]
        self.__previous_progress = crafting_progress[0]
        self.__set_progress()

    def wupdate(self):
        super().wupdate()
        if self.__previous_progress != self.__progress[0]:
            self.__previous_progress = self.__progress[0]
            self.__set_progress()

    def __set_progress(self):
        """Set the progress of the arrow based on the progress of the crafting process"""
        full_rect = self.__full_progress_arrow.get_rect()
        try:
            fraction_progress = min(1.0, self.__progress[0] / self.__progress[1])
        except ZeroDivisionError:
            fraction_progress = 0.0
        width = int(fraction_progress * full_rect.width)
        actual_rect = pygame.Rect(*full_rect.topleft, width, full_rect.height)
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