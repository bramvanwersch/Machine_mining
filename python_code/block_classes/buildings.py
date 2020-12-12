from block_classes.building_materials import BuildingMaterial, TerminalMaterial, FurnaceMaterial, FactoryMaterial
from block_classes.materials import *
from block_classes.blocks import *
from inventories import Inventory, Filter
from utility.utilities import Size
from interfaces.small_interfaces import TerminalWindow, Window
from interfaces.crafting_interfaces import FactoryWindow, FurnaceWindow
import recipes.recipe_constants as r_constants
from network.pipes import NetworkNode


def block_i_from_material(material):
    if isinstance(material, BuildingMaterial):
        name = material.name().replace("Material", "")
        building_block_i = globals()[name]
    else:
        building_block_i = material.BLOCK_TYPE
    return building_block_i


def building_type_from_material(material):
    return material_mapping[material.name()]


class Building(MultiBlock, ABC):
    """
    Abstract class for buildings. Buildings are multiblock (can be 1) structures
    that contain an image
    """
    ID = 0

    def __init__(self, pos, **kwargs):
        MultiBlock.__init__(self, pos, self.MATERIAL, **kwargs)
        self.id = "Building{}".format(self.ID)
        Building.ID += 1

    @property
    @abstractmethod
    def MATERIAL(self) -> BaseMaterial:
        """
        Specify a material class. The material class should be called
        NameOfBuildingMaterial and the name of the building cannot contain the
        word Material

        :return: material class
        """
        pass


class InterfaceBuilding(Building, ABC):
    def __init__(self, pos, sprite_group, size=-1, in_filter=None, out_filter=None, recipes=None, **kwargs):
        self.inventory = Inventory(size, in_filter=in_filter, out_filter=out_filter)
        Building.__init__(self, pos, action=self.__select_buidling_action, **kwargs)
        from interfaces.managers import game_window_manager
        self.window_manager = game_window_manager

        self.interface = self.INTERFACE_TYPE(self, sprite_group, recipes=recipes)

    @property
    @abstractmethod
    def INTERFACE_TYPE(self):
        pass

    def __select_buidling_action(self):
        # make sure to update the window manager when needed
        if self.window_manager is None:
            from interfaces.managers import game_window_manager
            self.window_manager = game_window_manager
        self.window_manager.add(self.interface)

    def _get_blocks(self):
        blocks = super()._get_blocks()
        for row in blocks:
            for block in row:
                block.inventory = self.inventory
        return blocks


class Terminal(InterfaceBuilding, NetworkNode):
    """
    Terminal building. The main interaction centrum for the workers
    """
    MATERIAL: BaseMaterial = TerminalMaterial
    MULTIBLOCK_DIMENSION: Size = Size(2, 2)
    INTERFACE_TYPE: Window = TerminalWindow

    def __init__(self, pos, spite_group, **kwargs):
        InterfaceBuilding.__init__(self, pos, spite_group, size=-1, **kwargs)
        NetworkNode.__init__(self)


class Furnace(InterfaceBuilding, NetworkNode):
    """
    Terminal building. The main interaction centrum for the workers
    """
    MATERIAL = FurnaceMaterial
    MULTIBLOCK_DIMENSION: Size = Size(2, 2)
    INTERFACE_TYPE: Window = FurnaceWindow

    def __init__(self, pos, spite_group, **kwargs):
        InterfaceBuilding.__init__(self, pos, spite_group, in_filter=Filter(whitelist=[None]),
                                   out_filter=Filter(whitelist=[None]), size=200,
                                   recipes=r_constants.recipe_books["furnace"], **kwargs)
        NetworkNode.__init__(self)


class Factory(InterfaceBuilding, NetworkNode):
    MATERIAL = FactoryMaterial
    MULTIBLOCK_DIMENSION: Size = Size(2, 2)
    INTERFACE_TYPE: Window = FactoryWindow

    def __init__(self, pos, spite_group, **kwargs):
        InterfaceBuilding.__init__(self, pos, spite_group, size=300, in_filter=Filter(whitelist=[None]),
                                   out_filter=Filter(whitelist=[None]),
                                   recipes=r_constants.recipe_books["factory"], **kwargs)
        NetworkNode.__init__(self)


material_mapping = {"TerminalMaterial" : Terminal,
                    "FurnaceMaterial" : Furnace,
                    "FactoryMaterial" : Factory}
