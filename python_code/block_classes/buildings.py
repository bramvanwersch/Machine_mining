# !/usr/bin/python3

# library imports
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING, Tuple, Union, Set, Type, Hashable, Dict, Any
import pygame

# own imports
import block_classes.materials.building_materials as build_materials
import block_classes.materials.materials as base_materials
import block_classes.blocks as block_classes
from utility import inventories, loading_saving
import utility.utilities as util
import interfaces.base_interface as base_interface
import interfaces.other_interfaces as small_interfaces
import interfaces.crafting_interfaces as craft_interfaces
import recipes.recipe_utility as r_constants
if TYPE_CHECKING:
    import board.sprite_groups as sprite_groups
    from interfaces.managers import game_window_manager


# TODO check the use of this
def building_type_from_material(material):
    return material_mapping[material.name()]


class Building(block_classes.MultiBlock, util.ConsoleReadable, loading_saving.Loadable, ABC):
    """
    Abstract class for buildings. Buildings are multiblock (can be 1) structures
    that contain an image
    """
    MATERIAL: base_materials.BaseMaterial

    def __init__(
        self,
        pos: List[int],
        **kwargs
    ):
        super().__init__(pos, self.MATERIAL(), **kwargs)

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def MATERIAL(self) -> Type[base_materials.BaseMaterial]:
        """
        Specify a material class. The material class should be called
        NameOfBuildingMaterial and the name of the building cannot contain the
        word Material

        :return: material class
        """
        pass

    def has_inventory(self) -> bool:
        """
        Check on the fly if any of the bocks of the building are a container block
        """
        for row in self.blocks:
            for block in row:
                if isinstance(block, block_classes.ContainerBlock):
                    return True
        return False


class InterfaceBuilding(Building, ABC):
    """abstraction level of buidlings with interfaces and inventory"""
    INTERFACE_TYPE: base_interface.Window

    inventory: inventories.Inventory
    window_manager: "game_window_manager"
    interface: base_interface.Window

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        size: int = -1,
        in_filter: inventories.Filter = None,
        out_filter: inventories.Filter = None,
        starting_items: inventories.Inventory = None,
        interface_title: str = "",
        **kwargs
    ):
        # this is here in order to get the rect before the MultiBlock instantiation to be able to make the interface
        self.rect = pygame.Rect((pos[0], pos[1], self.size().width, self.size().height))

        self.inventory = inventories.Inventory(size, in_filter=in_filter, out_filter=out_filter)
        self.interface = self.create_interface(sprite_group, interface_title)
        Building.__init__(self, pos, blocks_kwargs=[[{"inventory": self.inventory, "interface": self.interface},
                                                     {"inventory": self.inventory, "interface": self.interface}],
                                                    [{"inventory": self.inventory, "interface": self.interface},
                                                     {"inventory": self.inventory, "interface": self.interface}]],
                          **kwargs)
        self._add_starting_items(starting_items)

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def INTERFACE_TYPE(self) -> type:
        pass

    def _add_starting_items(
        self,
        starting_items: Union[None, inventories.Inventory]
    ):
        if starting_items is None:
            return
        for item in starting_items.get_all_items(ignore_filter=True):
            self.inventory.add_items(item)

    def create_interface(
        self,
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        title: str
    ) -> base_interface.Window:
        """Innitiate the interface window"""
        return self.INTERFACE_TYPE(self.rect, sprite_group=sprite_group, inventory=self.inventory, title=title)

    def printables(self) -> Set[str]:
        attributes = super().printables()
        attributes.remove("interface")
        return attributes


class Terminal(InterfaceBuilding):
    """
    Terminal building. The main interaction centrum for the workers
    """
    MATERIAL: Type[base_materials.BaseMaterial] = build_materials.TerminalMaterial
    MULTIBLOCK_LAYOUT: List[List[Hashable]] = [[1, 2], [3, 4]]
    INTERFACE_TYPE: base_interface.Window = small_interfaces.InventoryWindow

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        spite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        InterfaceBuilding.__init__(self, pos, spite_group, size=-1, interface_title="TERMINAL", **kwargs)


class StoneChest(InterfaceBuilding):

    MATERIAL: Type[base_materials.BaseMaterial] = build_materials.StoneChestMaterial
    MULTIBLOCK_LAYOUT: List[List[Hashable]] = [[1]]
    INTERFACE_TYPE: base_interface.Window = small_interfaces.InventoryWindow

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        spite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        InterfaceBuilding.__init__(self, pos, spite_group, size=100, interface_title="STONE CHEST", **kwargs)


class CraftingInterfaceBuilding(InterfaceBuilding, block_classes.VariableSurfaceBlock, ABC):
    __recipes: r_constants.RecipeBook

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        self.__recipes = type(self).get_recipe_book()
        super().__init__(pos, sprite_group, **kwargs)
        block_classes.VariableSurfaceBlock.__init__(self)

    @staticmethod
    @abstractmethod
    def get_recipe_book() -> r_constants.RecipeBook:
        # this method is here instead of a class value because it is loaded on startup of the game
        pass

    def create_interface(
        self,
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        title: str
    ) -> base_interface.Window:
        """Innitiate the interface window"""
        return self.INTERFACE_TYPE(self, sprite_group=sprite_group, recipes=self.__recipes, title=title)


class Furnace(CraftingInterfaceBuilding):

    MATERIAL: Type[base_materials.BaseMaterial] = build_materials.FurnaceMaterial
    MULTIBLOCK_LAYOUT: List[List[Hashable]] = [[1, 2], [3, 4]]
    INTERFACE_TYPE: base_interface.Window = craft_interfaces.FurnaceWindow

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        CraftingInterfaceBuilding.__init__(self, pos, sprite_group,
                                           in_filter=inventories.Filter(whitelist=[]), size=200,
                                           interface_title="FURNACE", **kwargs)

    def to_dict(self):
        d1 = super().to_dict()
        d2 = block_classes.VariableSurfaceBlock.to_dict(self)
        d1["block_kwargs"]["changed"] = d2["changed"]
        return d1

    @staticmethod
    def get_recipe_book():
        return r_constants.recipe_books["furnace"]


class Factory(CraftingInterfaceBuilding):
    MATERIAL: Type[base_materials.BaseMaterial] = build_materials.FactoryMaterial
    MULTIBLOCK_LAYOUT: List[List[Hashable]] = [[1, 2], [3, 4]]
    INTERFACE_TYPE: base_interface.Window = craft_interfaces.FactoryWindow

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        CraftingInterfaceBuilding.__init__(self, pos, sprite_group, size=300,
                                           in_filter=inventories.Filter(whitelist=[]),
                                           interface_title="FACTORY", **kwargs)

    def to_dict(self):
        d1 = super().to_dict()
        d2 = block_classes.VariableSurfaceBlock.to_dict(self)
        d1["block_kwargs"]["changed"] = d2["changed"]
        return d1

    @staticmethod
    def get_recipe_book():
        return r_constants.recipe_books["factory"]


material_mapping = {"TerminalMaterial": Terminal,
                    "FurnaceMaterial": Furnace,
                    "FactoryMaterial": Factory,
                    "StoneChestMaterial": StoneChest}
