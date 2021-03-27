# !/usr/bin/python3

# library imports
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING, Tuple, Union, Set, Type

# own imports
import block_classes.building_materials as build_materials
import block_classes.materials as base_materials
import block_classes.blocks as block_classes
from utility import inventories
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


class Building(block_classes.MultiBlock, util.ConsoleReadable, ABC):
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
        **kwargs
    ):
        self.inventory = inventories.Inventory(size, in_filter=in_filter, out_filter=out_filter)
        Building.__init__(self, pos, action=self.__select_buidling_action, **kwargs)
        from interfaces.managers import game_window_manager
        self.window_manager = game_window_manager

        self.interface = self.create_interface(sprite_group)

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def INTERFACE_TYPE(self) -> type:
        pass

    def create_interface(
        self,
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
    ) -> base_interface.Window:
        """Innitiate the interface window"""
        return self.INTERFACE_TYPE(self, sprite_group)

    def printables(self) -> Set[str]:
        attributes = super().printables()
        attributes.remove("window_manager")
        attributes.remove("interface")
        return attributes

    def __select_buidling_action(self) -> None:
        # make sure to update the window manager when needed
        if self.window_manager is None:
            from interfaces.managers import game_window_manager
            self.window_manager = game_window_manager
        self.window_manager.add(self.interface)

    def _get_blocks(self) -> List[List[block_classes.Block]]:
        blocks_ = super()._get_blocks()
        for row in blocks_:
            for block in row:
                block.inventory = self.inventory
        return blocks_


class CraftingInterfaceBuilding(InterfaceBuilding, ABC):
    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        recipes: r_constants.RecipeBook,
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        size: int = -1,
        in_filter: inventories.Filter = None,
        out_filter: inventories.Filter = None,
        **kwargs
    ):
        self.__recipes = recipes
        super().__init__(pos, sprite_group, size, in_filter, out_filter, **kwargs)

    def create_interface(
        self,
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
    ) -> base_interface.Window:
        return self.INTERFACE_TYPE(self, self.__recipes, sprite_group)


class Terminal(InterfaceBuilding):
    """
    Terminal building. The main interaction centrum for the workers
    """
    MATERIAL: Type[base_materials.BaseMaterial] = build_materials.TerminalMaterial
    MULTIBLOCK_DIMENSION: util.Size = util.Size(2, 2)
    INTERFACE_TYPE: base_interface.Window = small_interfaces.InventoryWindow

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        spite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        InterfaceBuilding.__init__(self, pos, spite_group, size=-1, **kwargs)

    def create_interface(
        self,
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ) -> base_interface.Window:
        """Innitiate the interface window"""
        return self.INTERFACE_TYPE(self, sprite_group, title="TERMINAL", **kwargs)


class StoneChest(InterfaceBuilding):
    """
    Terminal building. The main interaction centrum for the workers
    """
    MATERIAL: Type[base_materials.BaseMaterial] = build_materials.StoneChestMaterial
    MULTIBLOCK_DIMENSION: util.Size = util.Size(1, 1)
    INTERFACE_TYPE: base_interface.Window = small_interfaces.InventoryWindow

    def __init__(
            self,
            pos: Union[Tuple[int, int], List[int]],
            spite_group: "sprite_groups.CameraAwareLayeredUpdates",
            **kwargs
    ):
        InterfaceBuilding.__init__(self, pos, spite_group, size=100, **kwargs)

    def create_interface(
        self,
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ) -> base_interface.Window:
        """Innitiate the interface window"""
        return self.INTERFACE_TYPE(self, sprite_group, title="STONE CHEST", **kwargs)


class Furnace(CraftingInterfaceBuilding):
    """
    Terminal building. The main interaction centrum for the workers
    """
    MATERIAL: Type[base_materials.BaseMaterial] = build_materials.FurnaceMaterial
    MULTIBLOCK_DIMENSION: util.Size = util.Size(2, 2)
    INTERFACE_TYPE: base_interface.Window = craft_interfaces.FurnaceWindow

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        super().__init__(pos, r_constants.recipe_books["furnace"], sprite_group,
                         in_filter=inventories.Filter(whitelist=[]), size=200, **kwargs)


class Factory(CraftingInterfaceBuilding):
    MATERIAL: Type[base_materials.BaseMaterial] = build_materials.FactoryMaterial
    MULTIBLOCK_DIMENSION: util.Size = util.Size(2, 2)
    INTERFACE_TYPE: base_interface.Window = craft_interfaces.FactoryWindow

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        super().__init__(pos, r_constants.recipe_books["factory"], sprite_group, size=300,
                         in_filter=inventories.Filter(whitelist=[]), **kwargs)


material_mapping = {"TerminalMaterial": Terminal,
                    "FurnaceMaterial": Furnace,
                    "FactoryMaterial": Factory,
                    "StoneChestMaterial": StoneChest}
