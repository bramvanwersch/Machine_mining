from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

import block_classes.building_materials as build_materials
import block_classes.materials as base_materials
import block_classes.blocks as block_classes
import inventories
import utility.utilities as util
import interfaces.base_interface as base_interface
import interfaces.small_interfaces as small_interfaces
import interfaces.crafting_interfaces as craft_interfaces
import recipes.recipe_utility as r_constants
import network.pipes as network
if TYPE_CHECKING:
    import board.sprite_groups as sprite_groups
    from interfaces.managers import game_window_manager


def building_type_from_material(material):
    return material_mapping[material.name()]


class Building(block_classes.MultiBlock, ABC):
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
        super().__init__(pos, self.MATERIAL, **kwargs)

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def MATERIAL(self) -> base_materials.BaseMaterial:
        """
        Specify a material class. The material class should be called
        NameOfBuildingMaterial and the name of the building cannot contain the
        word Material

        :return: material class
        """
        pass


class InterfaceBuilding(Building, ABC):
    """abstraction level of buidlings with interfaces and inventory"""
    INTERFACE_TYPE: base_interface.Window
    inventory: inventories.Inventory
    window_manager: "game_window_manager"
    interface: base_interface.Window

    def __init__(
        self,
        pos: List[int],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        size: int = -1,
        in_filter: inventories.Filter = None,
        out_filter: inventories.Filter = None,
        recipes: r_constants.RecipeBook = None,
        **kwargs
    ):
        self.inventory = inventories.Inventory(size, in_filter=in_filter, out_filter=out_filter)
        Building.__init__(self, pos, action=self.__select_buidling_action, **kwargs)
        from interfaces.managers import game_window_manager
        self.window_manager = game_window_manager

        self.interface = self.INTERFACE_TYPE(self, sprite_group, recipes=recipes)

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def INTERFACE_TYPE(self) -> type:
        pass

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


class Terminal(InterfaceBuilding, network.NetworkNode):
    """
    Terminal building. The main interaction centrum for the workers
    """
    MATERIAL: base_materials.BaseMaterial = build_materials.TerminalMaterial
    MULTIBLOCK_DIMENSION: util.Size = util.Size(2, 2)
    INTERFACE_TYPE: base_interface.Window = small_interfaces.TerminalWindow

    def __init__(
        self,
        pos: List[int],
        spite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        InterfaceBuilding.__init__(self, pos, spite_group, size=-1, **kwargs)
        network.NetworkNode.__init__(self)


class Furnace(InterfaceBuilding, network.NetworkNode):
    """
    Terminal building. The main interaction centrum for the workers
    """
    MATERIAL = build_materials.FurnaceMaterial
    MULTIBLOCK_DIMENSION: util.Size = util.Size(2, 2)
    INTERFACE_TYPE: base_interface.Window = craft_interfaces.FurnaceWindow

    def __init__(
        self,
        pos: List[int],
        spite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        InterfaceBuilding.__init__(self, pos, spite_group, in_filter=inventories.Filter(whitelist=[None]),
                                   out_filter=inventories.Filter(whitelist=[None]), size=200,
                                   recipes=r_constants.recipe_books["furnace"], **kwargs)
        network.NetworkNode.__init__(self)


class Factory(InterfaceBuilding, network.NetworkNode):
    MATERIAL = build_materials.FactoryMaterial
    MULTIBLOCK_DIMENSION: util.Size = util.Size(2, 2)
    INTERFACE_TYPE: base_interface.Window = craft_interfaces.FactoryWindow

    def __init__(
        self,
        pos: List[int],
        spite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        InterfaceBuilding.__init__(self, pos, spite_group, size=300, in_filter=inventories.Filter(whitelist=[None]),
                                   out_filter=inventories.Filter(whitelist=[None]),
                                   recipes=r_constants.recipe_books["factory"], **kwargs)
        network.NetworkNode.__init__(self)


material_mapping = {"TerminalMaterial": Terminal,
                    "FurnaceMaterial": Furnace,
                    "FactoryMaterial": Factory}
