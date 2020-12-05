import pygame
from abc import ABC

from utility.constants import BLOCK_SIZE, MULTI_TASKS


class BaseBlock(ABC):
    """
    Base class for the block_classes in image matrices
    """
    SIZE = BLOCK_SIZE
    ID = 0
    def __init__(self, pos, material, id=None, action=None):
        self.rect = pygame.Rect((*pos, *self.SIZE))
        self.material = material
        self.__action_function = action
        if id == None:
            self.id = self.ID
            BaseBlock.ID += 1
        else:
            self.id = id
        self.light_level = 0

    def __getattr__(self, item):
        return getattr(self.material, item)

    def action(self):
        """
        Function to allow a action being triggered when needed
        """
        if self.__action_function != None:
            self.__action_function()

    @property
    def coord(self):
        """
        Simplify getting the coordinate of a block

        :return: the topleft cooridnate of the block rectangle.
        """
        return self.rect.topleft

    def is_task_allowded(self, task_type: str) -> bool:
        return task_type in self.allowed_tasks

    @property
    def transparant_group(self):
        return self.material.transparant_group

    @transparant_group.setter
    def transparant_group(self, value):
        self.material.transparant_group = value

    def name(self):
        """
        The name of the material of the block

        :return: a string
        """
        return self.material.name()

    def __eq__(self, other):
        """
        Method used when == is called using this object

        :param other: a string that is the name of a block
        :return: a boolean
        """
        return other == self.material.name()

    def __hash__(self):
        """
        Function for hashing a block. Kind of obsolote
        TODO check how usefull this is and if neccesairy
        :return: a hash
        """
        return hash(str(self.rect.topleft))


class AirBlock(BaseBlock):
    """
    Special case of a block class that is an empty block with no surface
    """
    def __init__(self, pos, material, **kwargs):
        super().__init__(pos, material, **kwargs)


class Block(BaseBlock):
    """
    A normal block containing anythin but air
    """
    def __init__(self, pos, material, **kwargs):
        super().__init__(pos, material, **kwargs)
        self.rect = self.surface.get_rect(topleft=pos)

    @property
    def surface(self):
        return self.material.surface


class NetworkBlock(Block):
    def __init__(self, pos, material, **kwargs):
        super().__init__(pos, material, **kwargs)
        self.network_group = 1


class ContainerBlock(NetworkBlock):
    """
    Block that has an inventory
    """
    #TODO take a critical look at this block and inheritance to container Inventory
    def __init__(self, pos, material, **kwargs):
        super().__init__(pos, material, **kwargs)
        #how full the terminal is does not matter
        self.inventory = None

    def add(self, *items):
        if self.inventory != None:
            self.inventory.add_items(*items)
