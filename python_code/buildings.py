from abc import ABC, abstractmethod

from python_code.materials import TerminalMaterial
from python_code.image_handling import image_sheets
from python_code.constants import BLOCK_SIZE
from python_code.blocks import *
from python_code.inventories import Inventory

class Building(ABC):
    """
    Abstract class for buildings. Buildings are multiblock (can be 1) structures
    that contain an image
    """
    BLOCK_TYPE = Block
    def __init__(self, pos):
        self.pos = pos
        self.blocks = self._get_blocks( self.BLOCK_TYPE, self.MATERIAL)

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
        Specify a material class

        :return: material class
        """
        return None

    def _images(self):
        """
        Retrieve an image from a sprite sheet using image specifications
        """
        return image_sheets[self.IMAGE_SPECIFICATIONS[0]].images_at_rectangle(
            self.IMAGE_SPECIFICATIONS[1], **self.IMAGE_SPECIFICATIONS[2])

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
                block_row.append(block_class(pos, BLOCK_SIZE, material))
            blocks.append(block_row)
        return blocks


class Terminal(Building):
    """
    Terminal building. The main interaction centrum for the workers
    """
    IMAGE_SPECIFICATIONS = ["buildings", (0, 0, 20, 20), {"color_key" : (255,255,255)}]
    BLOCK_TYPE = ContainerBlock
    MATERIAL = TerminalMaterial
    def __init__(self, pos):
        super().__init__(pos)

    def _get_blocks(self, block_class, material_class):
        blocks = super()._get_blocks(block_class, material_class)
        shared_inventory = Inventory(-1)
        for row in blocks:
            for block in row:
                block.inventory = shared_inventory
        return blocks

