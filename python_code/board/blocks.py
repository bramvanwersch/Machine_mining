import pygame
from abc import ABC

from python_code.utility.constants import BLOCK_SIZE, MULTI_TASKS


class BaseBlock(ABC):
    """
    Base class for the blocks in image matrices
    """
    #all tasks types are allowed
    SIZE = BLOCK_SIZE
    ID = 0
    def __init__(self, pos, id=None, action=None):
        self.rect = pygame.Rect((*pos, *self.SIZE))
        self.__action_function = action
        if id == None:
            self.id = self.ID
            BaseBlock.ID += 1
        else:
            self.id = id

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

    @property
    def allowed_tasks(self):
        """
        Convenience method testing what tasks are allowed for a certain block

        :return: a list of strings of allowable tasks
        """
        return self.material.ALLOWED_TASKS

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

        :param other: anything. But the expected value is a string
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
        super().__init__(pos, **kwargs)
        self.material = material


class Block(BaseBlock):
    """
    A normal block containing anythin but air
    """
    def __init__(self, pos, material, **kwargs):
        super().__init__(pos, **kwargs)
        self.material = material
        self.surface = self.material.surface
        self.rect = self.surface.get_rect(topleft=pos)


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
