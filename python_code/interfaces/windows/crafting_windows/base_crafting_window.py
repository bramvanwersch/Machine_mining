import pygame
from abc import ABC, abstractmethod
from typing import Union, List, Tuple, TYPE_CHECKING, ClassVar, Callable

import interfaces.widgets as widgets
import interfaces.windows.base_window as base_interface
import utility.constants as con
import utility.utilities as util
from utility import image_handling
from utility import inventories
if TYPE_CHECKING:
    from recipes import base_recipes, recipe_utility
    from block_classes import buildings
    from board import sprite_groups


class CraftingWindow(base_interface.Window, ABC):
    """Window has a crafting grid and a resulting label and """
    SIZE: util.Size = util.Size(300, 250)
    RECIPE_LABEL_SIZE: util.Size = util.Size(30, 30)
    MAX_ITEM_STACK: int = 2

    _recipe_book: "recipe_utility.RecipeBook"
    _craftable_item_recipe: Union["CraftingItem", None]
    _crafting: bool
    _crafting_time: List[int]
    _crafting_grid: Union["CraftingGrid", None]
    crafting_results_lbl: Union[widgets.ItemDisplay, None]
    _current_crafting_item: Union["CraftingItem", None]

    def __init__(
        self,
        craft_building: "buildings.Building",
        recipes: "recipe_utility.RecipeBook",
        *sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        self._craft_building = craft_building
        fr = self._craft_building.rect
        location = fr.bottomleft
        super().__init__(location, self.SIZE, *sprite_group, static=True, **kwargs)

        self._craftable_item_recipe = None
        self._crafting = False
        self._crafting_time = [0, 1]

        self.__max_allowed_items = dict()
        self._crafting_grid = None
        self._crafting_result_lbl = None
        self._current_crafting_item = None
        self._init_widgets(recipes)

    def _init_widgets(self, recipe_book):
        selector = self._get_recipe_selector(recipe_book)
        self.add_widget(self.RECIPE_SELECTOR_LOCATION, selector)
        self.add_border(selector)

        # create a pane were labels can be centered in above the recipe selector
        pane = widgets.Pane(util.Size(self.rect.width, self.rect.height - selector.rect.top + self.TOP_SIZE.height),
                            color=con.INVISIBLE_COLOR)
        self.add_widget((0, 10), pane)

        self._crafting_grid = self._get_crafting_grid()
        pane.add_widget(self.CRAFT_GRID_LOCATION, self._crafting_grid)

        self._crafting_result_lbl = self._get_crafting_result_label()
        pane.add_widget(self.CRAFT_RESULT_LABEL_LOCATION, self._crafting_result_lbl)
        pane.add_border(self._crafting_result_lbl)

        arrow_lbl = ProgressArrow((50, 50), self._crafting_time, color=con.INVISIBLE_COLOR)
        pos = (self._crafting_grid.rect.right + 25, "center")
        pane.add_widget(pos, arrow_lbl)

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def CRAFT_GRID_SIZE(self) -> util.Size:
        pass

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def CRAFT_GRID_LOCATION(self) -> Union[Tuple[int, int], List[int]]:
        pass

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def RECIPE_SELECTOR_LOCATION(self) -> Union[Tuple[int, int], List[int]]:
        pass

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def CRAFT_RESULT_LABEL_LOCATION(self) -> Union[Tuple[int, int], List[int]]:
        pass

    def _get_crafting_grid(self):
        """Create the grid where the recipes are shown and if materials are present"""
        return CraftingGrid(self.CRAFT_GRID_SIZE, self._craft_building.inventory)

    def _get_recipe_selector(self, recipe_book):
        if len(self.COLOR) == 4:
            color = self.COLOR[:-1]
        else:
            color = self.COLOR
        return RecipeSelector(util.Size(self.rect.width - 20, 90), recipe_book, color,
                              self.groups()[0], self.set_recipe)

    def _get_crafting_result_label(self):
        """Create the label that will hold the result of a crafting job"""
        if len(self.COLOR) == 4:
            color = self.COLOR[:-1]
        else:
            color = self.COLOR
        return widgets.ItemDisplay((50, 50), None, border=False, color=color, selectable=False)

    def update(self, *args):
        super().update(*args)
        if self._craftable_item_recipe is not None:
            self._craftable_item_recipe.update()
            if self._craftable_item_recipe.crafting:
                self._craft_building.set_active(self._crafting)

    def set_recipe(
        self,
        recipe: "base_recipes.BaseRecipe",
    ):
        """Set a recipe as active recipe invoked by clicking a recipe in the recipe selector"""
        # create craftable item
        self._craftable_item_recipe = CraftingItem(recipe, self._craft_building.inventory)

        self._crafting_grid.add_recipe(recipe)
        self._craft_building.inventory.in_filter.set_whitelist(*[item.name() for item in recipe.needed_items])

        # allow removal of all items except for the ones that are required for the crafting
        self._craft_building.inventory.out_filter.set_blacklist(*[item.name() for item in recipe.needed_items])
        if recipe.material.name() in self._craft_building.inventory:
            item = self._craft_building.inventory.item_pointer(recipe.material.name())
        else:
            item = inventories.Item(recipe.material(), 0)
            self._craft_building.inventory.add_items(item, ignore_filter=True)
        self._crafting_result_lbl.add_item(item)


class RecipeSelector(widgets.ScrollPane):
    RECIPE_LABEL_SIZE: util.Size = util.Size(30, 30)

    def __init__(
        self,
        size,
        recipe_book,
        color,
        sprite_group,
        select_recipe_function: Callable,
        **kwargs
    ):
        super().__init__(size, color=color, **kwargs)
        self._recipe_book = recipe_book
        self.selected_recipe = None
        self._create_recipe_selector(color, sprite_group)
        # function object passed by the crafting window to affect the crafting window
        self._select_recipe_function = select_recipe_function

    def select_recipe(
        self,
        recipe: "base_recipes.BaseRecipe",
        lbl: widgets.Label,
        selection_group: widgets.SelectionGroup
    ):
        self.selected_recipe = recipe
        selection_group.select(lbl, color=(0, 0, 0))
        self._select_recipe_function(recipe)

    def _create_recipe_selector(
        self,
        color: Union[Tuple[int, int, int, int], Tuple[int, int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates"
    ):
        """Create a scroll pane where the user can select recipes"""

        selection_group = widgets.SelectionGroup()
        for recipe in self._recipe_book:
            # create an image with a background
            background = pygame.Surface(self.RECIPE_LABEL_SIZE.size).convert()
            background.fill(color)
            recipe_img_size = self.RECIPE_LABEL_SIZE - (4, 4)
            image = pygame.transform.scale(recipe.get_image(), recipe_img_size)
            background.blit(image, ((self.RECIPE_LABEL_SIZE.width - recipe_img_size.width) / 2,
                                    (self.RECIPE_LABEL_SIZE.height - recipe_img_size.height) / 2, *recipe_img_size))

            tooltip = widgets.Tooltip(sprite_group, text=recipe.get_tooltip_text())
            recipe_lbl = widgets.Label(self.RECIPE_LABEL_SIZE, color=color, image=background, tooltip=tooltip)

            recipe_lbl.add_key_event_listener(1, self.select_recipe, values=[recipe, recipe_lbl, selection_group],
                                              types=["unpressed"])
            selection_group.add(recipe_lbl)
            self.add_widget(recipe_lbl)


class CraftingItem:
    """Item that is currently being crafted"""
    MAX_ITEM_STACK: int = 100

    recipe: "base_recipes.BaseRecipe"
    _source_inventory: inventories.Inventory

    def __init__(self, recipe, associated_inventory):
        self.recipe = recipe
        self._source_inventory = associated_inventory
        self.__max_allowed_items = self.__get_max_allowed_items()
        self.crafting = False
        self.time_crafted = 0

    def update(self):
        self.crafting = self._check_materials()
        if self.crafting:
            self._craft_item()
        # making sure that the inventory is not overfilled
        self.__configure_filters()

    def __get_max_allowed_items(self):
        """Configure the maximum allowed item of a certain type in order to not infinitally fill the inventory"""
        max_allowed_items = dict()
        for item in self.recipe.needed_items:
            max_allowed_items[item.name()] = item.quantity * self.MAX_ITEM_STACK
        return max_allowed_items

    def _craft_item(self):
        """Count the time an item is crafted for and finished when appropriate"""
        self.time_crafted += con.GAME_TIME.get_time()
        if self.time_crafted > self.recipe.CRAFTING_TIME:
            self._finish_item_crafting()

    def _finish_item_crafting(self):
        """Finish the crafting of an item, remove the items used for crafting and add the final product"""
        item = inventories.Item(self.recipe.material(), self.recipe.quantity)

        # add the crated item
        self._source_inventory.add_items(item, ignore_filter=True)

        # remove all items
        for item in self.recipe.needed_items:
            self._source_inventory.get(item.name(), item.quantity, ignore_filter=True)

    def _check_materials(self) -> bool:
        """Check if all materials are present to start crafting"""
        for n_item in self.recipe.needed_items:
            present = False
            for item in self._source_inventory.items:
                if item.name() == n_item.name() and item.quantity >= n_item.quantity:
                    present = True
                    break
            if not present:
                return False
        return True

    def __configure_filters(self):
        """set the item filters of the inventory of the building so that not to much items are taken from the belts and
        machines are not infinitally loaded with items"""
        for item_name, max_item_quantity in self.__max_allowed_items.items():
            inventory_item_pointer = self._source_inventory.item_pointer(item_name)
            if inventory_item_pointer is None:
                self._source_inventory.in_filter.add_whitelist(item_name)
            elif inventory_item_pointer.quantity >= max_item_quantity:
                self._source_inventory.in_filter.remove_from_whitelist(item_name)
            else:
                self._source_inventory.in_filter.add_whitelist(item_name)


class CraftingGrid(widgets.Pane):
    """Crafting grid for displaying recipes and the presence of items of those recipes"""
    COLOR: ClassVar[Union[Tuple[int, int, int], List[int]]] = (173, 94, 29)
    BORDER_DISTANCE: ClassVar[util.Size] = util.Size(5, 5)
    GRID_LABEL_SIZE: ClassVar[util.Size] = util.Size(25, 25)
    INBETWEEN_LABEL_SPACE: ClassVar[int] = 3

    _crafting_grid: List[List["_GridLabel"]]
    __watching_inventory: inventories.Inventory
    _recipe: Union[None, "base_recipes.BaseRecipe"]

    def __init__(
        self,
        grid_size: util.Size,
        inventory: inventories.Inventory,
        **kwargs
    ):
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
    """Label that for within a CraftingGrid"""
    POSITIVE_MARK: ClassVar[image_handling.ImageDefinition] = \
        image_handling.ImageDefinition("general", (80, 0), size=util.Size(10, 10), image_size=util.Size(10, 10))
    NEGATIVE_MARK: ClassVar[image_handling.ImageDefinition] = \
        image_handling.ImageDefinition("general", (70, 0), size=util.Size(10, 10), image_size=util.Size(10, 10))

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
    """Arrow that will fill with a color indicating how far a certain crafting process has come along"""
    __arrow_image: pygame.Surface
    __full_progress_arrow: pygame.Surface
    __crafting_progress: List[int]
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

        self.__crafting_progress = crafting_progress  # the progress in form [current, max]
        self.__previous_progress = crafting_progress[0]
        self.__set_progress()

    def wupdate(self):
        super().wupdate()
        if self.__previous_progress != self.__crafting_progress[0]:
            self.__previous_progress = self.__crafting_progress[0]
            self.__set_progress()

    def __set_progress(self):
        """Set the progress of the arrow based on the progress of the crafting process"""
        full_rect = self.__full_progress_arrow.get_rect()
        try:
            fraction_progress = min(1.0, self.__crafting_progress[0] / self.__crafting_progress[1])
        except ZeroDivisionError:
            fraction_progress = 0.0
        width = int(fraction_progress * full_rect.width)
        actual_rect = pygame.Rect(*full_rect.topleft, width, full_rect.height)
        progress_arrow = self.__arrow_image.copy()
        progress_arrow.blit(self.__full_progress_arrow, actual_rect, actual_rect)
        self.set_image(progress_arrow)
