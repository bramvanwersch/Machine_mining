from abc import abstractmethod
import pygame

from python_code.board.materials import *
from python_code.utility.image_handling import image_sheets
from python_code.utility.constants import BLOCK_SIZE
from python_code.board.blocks import *
from python_code.inventories import Inventory
from python_code.utility.utilities import Size


def block_i_from_material(material):
    if isinstance(material, BuildingMaterial):
        name = material.name().replace("Material", "")
        building_block_i = globals()[name]
    else:
        building_block_i = material.BLOCK_TYPE
    return building_block_i


class Building(BaseBlock, ABC):
    """
    Abstract class for buildings. Buildings are multiblock (can be 1) structures
    that contain an image
    """
    BLOCK_TYPE = Block
    SIZE = Size(*(BLOCK_SIZE * (2, 2)))
    ID = 0
    def __init__(self, pos, material=None, **kwargs):
        self.material = self.MATERIAL()
        self.pos = pos

        self.id = "Building{}".format(self.ID)
        Building.ID += 1

        self.blocks = self._get_blocks( self.BLOCK_TYPE, self.MATERIAL)
        self.rect = pygame.Rect((*pos, *self.SIZE))


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
            self.IMAGE_SPECIFICATIONS[1], **self.IMAGE_SPECIFICATIONS[2])

    def full_image(self):
        return image_sheets[self.IMAGE_SPECIFICATIONS[0]].image_at(self.IMAGE_SPECIFICATIONS[1][0:2],
                            size = self.IMAGE_SPECIFICATIONS[1][2:4], **self.IMAGE_SPECIFICATIONS[2])

    def _get_blocks(self, block_class, material_class):
        """
        Create blocks of a given class and type for each block that the image
        of the block occupies

        :param depth: an integer signifying how deep the material is
        :param block_class: an instance of a class inheriting from Block
        :return: a matrix of blocks in the shape of the image
        """
        blocks = []
        for row_i, row in enumerate(self._images()):
            block_row = []
            for column_i, image in enumerate(row):
                material = material_class(image = image)
                pos = (self.pos[0] + column_i * BLOCK_SIZE.width, self.pos[1] + row_i * BLOCK_SIZE.height)
                block_row.append(block_class(pos, material, id=self.id))
            blocks.append(block_row)
        return blocks


class Terminal(Building):
    """
    Terminal building. The main interaction centrum for the workers
    """
    IMAGE_SPECIFICATIONS = ["buildings", (0, 0, 20, 20), {"color_key" : (255,255,255)}]
    BLOCK_TYPE = ContainerBlock
    MATERIAL = TerminalMaterial

    def _get_blocks(self, block_class, material_class):
        blocks = super()._get_blocks(block_class, material_class)
        shared_inventory = Inventory(-1)
        for row in blocks:
            for block in row:
                block.inventory = shared_inventory
        return blocks


class Furnace(Building):
    """
    Terminal building. The main interaction centrum for the workers
    """
    IMAGE_SPECIFICATIONS = ["buildings", (20, 0, 20, 20), {"color_key" : (255,255,255)}]
    BLOCK_TYPE = Block
    MATERIAL = FurnaceMaterial

    def _get_blocks(self, block_class, material_class):
        blocks = super()._get_blocks(block_class, material_class)
        shared_inventory = Inventory(-1)
        for row in blocks:
            for block in row:
                block.inventory = shared_inventory
        return blocks
