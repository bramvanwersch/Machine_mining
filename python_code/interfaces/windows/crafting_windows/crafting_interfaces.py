import pygame
from typing import Union, List, Tuple, TYPE_CHECKING

import interfaces.widgets as widgets
import utility.constants as con
import utility.utilities as util
import block_classes.block_utility as block_util
from utility import inventories
from interfaces.windows.crafting_windows.base_crafting_window import CraftingWindow, CraftingItem
if TYPE_CHECKING:
    from recipes import base_recipes, recipe_utility, furnace_recipes
    from block_classes import buildings
    from board import sprite_groups


class FactoryWindow(CraftingWindow):
    """Interface for factory buildings"""
    CRAFT_GRID_SIZE: util.Size = util.Size(4, 4)
    CRAFT_GRID_LOCATION: Union[Tuple[Union[int, str], Union[int, str]], List[Union[int, str]]] = (10, "center")
    RECIPE_SELECTOR_LOCATION: Union[Tuple[Union[int, str], Union[int, str]], List[Union[int, str]]] = (10, 150)
    CRAFT_RESULT_LABEL_LOCATION: Union[Tuple[Union[int, str], Union[int, str]], List[Union[int, str]]] = (220, "center")


class FurnaceWindow(CraftingWindow):
    """Interface for Furnace buildings"""
    CRAFT_GRID_SIZE: util.Size = util.Size(2, 2)
    CRAFT_GRID_LOCATION:  Union[Tuple[Union[int, str], Union[int, str]], List[Union[int, str]]] = (40, "center")
    RECIPE_SELECTOR_LOCATION: Union[Tuple[Union[int, str], Union[int, str]], List[Union[int, str]]] = (10, 150)
    CRAFT_RESULT_LABEL_LOCATION: Union[Tuple[Union[int, str], Union[int, str]], List[Union[int, str]]] = (200, "center")

    __fuel_meter: Union["FuelMeter", None]
    _craftable_item_recipe: Union["furnace_recipes.BaseFurnaceRecipe", None]

    def __init__(
        self,
        craft_building: "buildings.Building",
        recipes: "recipe_utility.RecipeBook",
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        self.__fuel_meter = None
        super().__init__(craft_building, recipes, sprite_group, **kwargs)

    def _init_widgets(self, recipe_book):
        super()._init_widgets(recipe_book)
        self.__fuel_meter = FuelMeter((25, 100), self._craft_building.inventory)
        self.add_widget((10, 10), self.__fuel_meter)

    def update(self):
        super().update()
        if not self.__fuel_meter.full():
            self._craft_building.inventory.in_filter.add_whitelist(*[fuel.name() for fuel in block_util.fuel_materials])
        else:
            self._craft_building.inventory.in_filter.remove_from_whitelist(*[fuel.name() for
                                                                             fuel in block_util.fuel_materials])

    def set_recipe(
        self,
        recipe: "base_recipes.BaseRecipe",
    ):
        super().set_recipe(recipe)
        self._craft_building.inventory.out_filter.add_blacklist(*[fuel.name() for fuel in block_util.fuel_materials])
        if not self.__fuel_meter.full():
            self._craft_building.inventory.in_filter.add_whitelist(*[fuel.name() for fuel in block_util.fuel_materials])


class FurnaceCraftingItem(CraftingItem):

    recipe: "furnace_recipes.BaseFurnaceRecipe"
    __fuel_meter: "FuelMeter"

    def __init__(self, recipe, associated_inventory, fuel_meter):
        super().__init__(recipe, associated_inventory)
        self.__fuel_meter = fuel_meter

    def _check_materials(self) -> bool:
        result = super()._check_materials()
        needed_fuel = self.recipe.FUEL_CONSUMPTION - self.__fuel_meter.fuel_lvl
        return result and needed_fuel <= 0

    def _finish_item_crafting(self):
        super()._finish_item_crafting()
        self.__fuel_meter.remove_fuel(self.recipe.FUEL_CONSUMPTION)


class FuelMeter(widgets.Pane):
    """Monitors the fuel present in the watching inventory and displays it accordingly"""

    fuel_lvl: int
    __source_inventory: inventories.Inventory
    __max_fuel: int
    __leftover_fuel: int
    fuel_indicator: Union[None, widgets.Label]

    def __init__(
        self,
        size: Union[util.Size, Tuple[int, int], List[int]],
        watching_inventory: inventories.Inventory,
        max_fuel: int = 100,
        **kwargs
    ):
        super().__init__(size, color=con.INVISIBLE_COLOR, **kwargs)
        self.fuel_lvl = 0  # the fuel that is currently present
        self.__source_inventory = watching_inventory  # furnace inventory that is monitored for total fuel
        self.__max_fuel = max(1, max_fuel)
        self.__leftover_fuel = 0  # value tracking fuel that was leftover from a previous smelting job

        self.fuel_indicator = None  # the image showing the amount of fuel
        self.__init_widgets()

    def __init_widgets(self):
        text_lbl = widgets.Label((25, 10), color=con.INVISIBLE_COLOR, selectable=False)
        text_lbl.set_text("Fuel", (0, 0), font_size=16)
        self.add_widget((0, 0), text_lbl)

        self.fuel_indicator = widgets.Label((20, self.rect.height - 20), color=con.INVISIBLE_COLOR, selectable=False)
        self.add_border(self.fuel_indicator)
        self.add_widget((2, 15), self.fuel_indicator)
        self.__change_fuel_indicator()

    def wupdate(self, *args):
        super().wupdate(*args)
        self.__configure_fuel_level()

    def __configure_fuel_level(self):
        """Calculate the total fuel in the inventory and adjust the fuel level if needed"""
        total_fuel = 0
        for mat_name in [f.name() for f in block_util.fuel_materials]:
            fuel_pointer = self.__source_inventory.item_pointer(mat_name)
            if fuel_pointer is not None and fuel_pointer.quantity > 0:
                total_fuel += fuel_pointer.FUEL_VALUE * fuel_pointer.quantity
        if total_fuel != self.fuel_lvl:
            self.fuel_lvl = total_fuel
            self.__change_fuel_indicator()

    def full(self) -> bool:
        return self.fuel_lvl >= self.__max_fuel

    def remove_fuel(
        self,
        needed_fuel: int
    ):
        """Remove fuel from the watched_inventory based on the needed value"""
        needed_fuel -= self.__leftover_fuel
        if needed_fuel <= 0:
            self.__leftover_fuel = abs(needed_fuel)
        for mat_name in [f.name() for f in block_util.fuel_materials]:
            fuel_pointer = self.__source_inventory.item_pointer(mat_name)
            if fuel_pointer is None:
                continue
            while fuel_pointer.quantity > 0 and needed_fuel > 0:
                needed_fuel -= fuel_pointer.FUEL_VALUE
                fuel_pointer.quantity -= 1
            if needed_fuel <= 0:
                self.__leftover_fuel = abs(needed_fuel)
                break
        if needed_fuel > 0:
            raise util.GameException("It should not be allowed to craft when there is not enough fuel.")

    def __change_fuel_indicator(self):
        """Change the level of the fuel indicator based on the present fuel in the inventory"""
        full_image = pygame.Surface(self.fuel_indicator.rect.size).convert()
        full_image.fill((150, 150, 150))
        # a value that is inbetween 0 and max_fuel to make sure that the indicator does not look weird
        capped_fuel_level = min(max(self.fuel_lvl, 0), self.__max_fuel)
        img_height = int(self.fuel_indicator.rect.height * (capped_fuel_level / self.__max_fuel))
        fuel_image = pygame.Surface((self.fuel_indicator.rect.width, img_height))
        fuel_image.fill((0, 255, 0))
        full_image.blit(fuel_image, (0, self.fuel_indicator.rect.height - img_height, self.fuel_indicator.rect.width,
                                     img_height))

        self.fuel_indicator.set_image(full_image, pos=(0, 0))
        self.add_border(self.fuel_indicator)
