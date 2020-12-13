from abc import ABC, abstractmethod


import block_classes.building_materials as build_materials
import block_classes.materials as base_materials
import block_classes.blocks as blocks
import inventories
import utility.utilities as util
import interfaces.base_interface as base_interface
import interfaces.small_interfaces as small_interfaces
import interfaces.crafting_interfaces as craft_interfaces
import recipes.recipe_utility as r_constants
import network.pipes as network


def block_i_from_material(material):
    if isinstance(material, build_materials.BuildingMaterial):
        name = material.name().replace("Material", "")
        building_block_i = globals()[name]
    else:
        building_block_i = material.BLOCK_TYPE
    return building_block_i


def building_type_from_material(material):
    return material_mapping[material.name()]


class Building(blocks.MultiBlock, ABC):
    """
    Abstract class for buildings. Buildings are multiblock (can be 1) structures
    that contain an image
    """
    ID = 0

    def __init__(self, pos, **kwargs):
        super().__init__(pos, self.MATERIAL, **kwargs)
        self.id = "Building{}".format(self.ID)
        Building.ID += 1

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
    def __init__(self, pos, sprite_group, size=-1, in_filter=None, out_filter=None, recipes=None, **kwargs):
        self.inventory = inventories.Inventory(size, in_filter=in_filter, out_filter=out_filter)
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


class Terminal(InterfaceBuilding, network.NetworkNode):
    """
    Terminal building. The main interaction centrum for the workers
    """
    MATERIAL: base_materials.BaseMaterial = build_materials.TerminalMaterial
    MULTIBLOCK_DIMENSION: util.Size = util.Size(2, 2)
    INTERFACE_TYPE: base_interface.Window = small_interfaces.TerminalWindow

    def __init__(self, pos, spite_group, **kwargs):
        InterfaceBuilding.__init__(self, pos, spite_group, size=-1, **kwargs)
        network.NetworkNode.__init__(self)


class Furnace(InterfaceBuilding, network.NetworkNode):
    """
    Terminal building. The main interaction centrum for the workers
    """
    MATERIAL = build_materials.FurnaceMaterial
    MULTIBLOCK_DIMENSION: util.Size = util.Size(2, 2)
    INTERFACE_TYPE: base_interface.Window = craft_interfaces.FurnaceWindow

    def __init__(self, pos, spite_group, **kwargs):
        InterfaceBuilding.__init__(self, pos, spite_group, in_filter=inventories.Filter(whitelist=[None]),
                                   out_filter=inventories.Filter(whitelist=[None]), size=200,
                                   recipes=r_constants.recipe_books["furnace"], **kwargs)
        network.NetworkNode.__init__(self)


class Factory(InterfaceBuilding, network.NetworkNode):
    MATERIAL = build_materials.FactoryMaterial
    MULTIBLOCK_DIMENSION: util.Size = util.Size(2, 2)
    INTERFACE_TYPE: base_interface.Window = craft_interfaces.FactoryWindow

    def __init__(self, pos, spite_group, **kwargs):
        InterfaceBuilding.__init__(self, pos, spite_group, size=300, in_filter=inventories.Filter(whitelist=[None]),
                                   out_filter=inventories.Filter(whitelist=[None]),
                                   recipes=r_constants.recipe_books["factory"], **kwargs)
        network.NetworkNode.__init__(self)


material_mapping = {"TerminalMaterial" : Terminal,
                    "FurnaceMaterial" : Furnace,
                    "FactoryMaterial" : Factory}
