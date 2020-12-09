from block_classes.building_materials import BuildingMaterial, TerminalMaterial, FurnaceMaterial, FactoryMaterial
from block_classes.materials import *
from utility.image_handling import image_sheets
from block_classes.blocks import *
from inventories import Inventory, Filter
from utility.utilities import Size
from interfaces.small_interfaces import TerminalWindow
from interfaces.crafting_interfaces import FactoryWindow, FurnaceWindow
import recipes.base_recipes
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


class Building(BaseBlock, ABC):
    """
    Abstract class for buildings. Buildings are multiblock (can be 1) structures
    that contain an image
    """
    BLOCK_TYPE = Block
    SIZE = Size(*(BLOCK_SIZE * (2, 2)))
    ID = 0

    def __init__(self, pos, material):
        self.material = material
        self.pos = pos

        self.id = "Building{}".format(self.ID)
        Building.ID += 1

        self.blocks = self._get_blocks( self.BLOCK_TYPE, self.MATERIAL)
        self.rect = pygame.Rect((*pos, *self.SIZE))

    def _action_function(self, *args):
        """
        Can be overwritten to trigger an action on all block_classes of the building
        when requested.

        :param args: optional arguments.
        """
        pass

    @property
    @abstractmethod
    def IMAGE_SPECIFICATIONS(self):
        """
        Each building should have image specifications
        :return: a list of lenght 3 containing; [name of sprite_sheet,
        rectangle containing images, **kwargs arguments or empty dict]
        """
        return []

    @property
    @abstractmethod
    def MATERIAL(self):
        """
        Specify a material class. The material class should be called
        NameOfBuildingMaterial and the name of the building cannot contain the
        word Material

        :return: material class
        """
        return None

    def _images(self):
        """
        Retrieve an image from a sprite sheet using image specifications
        """
        return image_sheets[self.IMAGE_SPECIFICATIONS[0]].images_at_rectangle(
            self.IMAGE_SPECIFICATIONS[1])

    @classmethod
    def full_image(self):
        return image_sheets[self.IMAGE_SPECIFICATIONS[0]].image_at(self.IMAGE_SPECIFICATIONS[1][0:2],
                            size = self.IMAGE_SPECIFICATIONS[1][2:4])

    def _get_blocks(self, block_class, material_class):
        """
        Create block_classes of a given class and type for each block that the image
        of the block occupies

        :param depth: an integer signifying how deep the material is
        :param block_class: an instance of a class inheriting from Block
        :return: a matrix of block_classes in the shape of the image
        """
        blocks = []
        for row_i, row in enumerate(self._images()):
            block_row = []
            for column_i, image in enumerate(row):
                material = material_class(image = image)
                pos = (self.pos[0] + column_i * BLOCK_SIZE.width, self.pos[1] + row_i * BLOCK_SIZE.height)
                block_row.append(block_class(pos, material, id=self.id, action=self._action_function))
            blocks.append(block_row)
        return blocks


class InterafaceBuilding(Building, ABC):
    def __init__(self, pos, *groups, **kwargs):
        Building.__init__(self, pos, **kwargs)
        from interfaces.managers import game_window_manager
        self.window_manager = game_window_manager
        self.sprite_groups = groups

        #make sure that this is reaised when not defined in a subclass when calling the interface
        self._interface = NotImplementedError

    @property
    def interface(self):
        return self._interface

    def _action_function(self, *args):
        #make sure to update the window manager when needed
        if self.window_manager == None:
            from interfaces.managers import game_window_manager
            self.window_manager = game_window_manager
        self.window_manager.add(self.interface)


class Terminal(InterafaceBuilding, NetworkNode):
    """
    Terminal building. The main interaction centrum for the workers
    """
    IMAGE_SPECIFICATIONS = ["buildings", (0, 0, 20, 20)]
    BLOCK_TYPE = ContainerBlock
    MATERIAL = TerminalMaterial

    def __init__(self, pos, *groups, **kwargs):
        self.inventory = Inventory(-1)
        InterafaceBuilding.__init__(self, pos, *groups, **kwargs)
        NetworkNode.__init__(self)
        self._interface = TerminalWindow(self, self.sprite_groups)

    def _get_blocks(self, block_class, material_class):
        blocks = super()._get_blocks(block_class, material_class)
        for row in blocks:
            for block in row:
                block.inventory = self.inventory
        return blocks


class Furnace(InterafaceBuilding, NetworkNode):
    """
    Terminal building. The main interaction centrum for the workers
    """
    IMAGE_SPECIFICATIONS = ["buildings", (20, 0, 20, 20)]
    BLOCK_TYPE = ContainerBlock
    MATERIAL = FurnaceMaterial

    def __init__(self, pos, *groups, **kwargs):
        self.inventory = Inventory(200, in_filter=Filter(whitelist=[None]), out_filter=Filter(whitelist=[None]))
        InterafaceBuilding.__init__(self, pos, *groups, **kwargs)
        NetworkNode.__init__(self)
        self._interface = FurnaceWindow(self, recipes.recipe_constants.recipe_books["furnace"], self.sprite_groups)

    def _get_blocks(self, block_class, material_class):
        blocks = super()._get_blocks(block_class, material_class)
        for row in blocks:
            for block in row:
                block.inventory = self.inventory
        return blocks


class Factory(InterafaceBuilding, NetworkNode):
    IMAGE_SPECIFICATIONS = ["buildings", (40, 0, 20, 20)]
    BLOCK_TYPE = ContainerBlock
    MATERIAL = FactoryMaterial

    def __init__(self, pos, *groups, **kwargs):
        self.inventory = Inventory(300, in_filter=Filter(whitelist=[None]), out_filter=Filter(whitelist=[None]))
        InterafaceBuilding.__init__(self, pos, *groups, **kwargs)
        NetworkNode.__init__(self)
        self._interface = FactoryWindow(self, recipes.recipe_constants.recipe_books["factory"], self.sprite_groups)

    def _get_blocks(self, block_class, material_class):
        blocks = super()._get_blocks(block_class, material_class)
        for row in blocks:
            for block in row:
                block.inventory = self.inventory
        return blocks

material_mapping = {"TerminalMaterial" : Terminal,
                    "FurnaceMaterial" : Furnace,
                    "FactoryMaterial" : Factory}
