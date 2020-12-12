import pygame
from typing import ClassVar, List
from abc import ABC, abstractmethod

from utility.constants import BLOCK_SIZE
from utility.utilities import Size


class BaseBlock(ABC):
    """
    Base class for the block_classes in image matrices
    """
    SIZE = BLOCK_SIZE
    ID = 0

    def __init__(self, pos, material, id=None, action=None):
        self.rect = pygame.Rect((*pos, *self.SIZE))
        self.material = material
        self._action_function = action
        if id is None:
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
        if self._action_function is not None:
            self._action_function()

    @property
    def coord(self):
        """
        Simplify getting the coordinate of a block

        :return: the topleft cooridnate of the block rectangle.
        """
        return self.rect.topleft

    def is_task_allowded(self, task_type: str) -> bool:
        return task_type in self.allowed_tasks

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
        if self.inventory is not None:
            self.inventory.add_items(*items)


class MultiBlock(BaseBlock, ABC):
    # have this here since you are technically allowed to call the size
    MULTIBLOCK_DIMENSION: ClassVar[Size] = Size(1, 1)
    SIZE = BaseBlock.SIZE * MULTIBLOCK_DIMENSION

    def __init__(self, pos, material, **kwargs):
        super().__init__(pos, material, **kwargs)
        self.blocks = self._get_blocks()

    @property
    @abstractmethod
    def MULTIBLOCK_DIMENSION(self) -> ClassVar[Size]:
        pass

    def _get_blocks(self) -> List[List[BaseBlock]]:
        # TODO this is not great
        import block_classes.block_utility as block_utility
        blocks = []
        topleft = self.rect.topleft
        image_key_count = 1
        for row_i in range(self.MULTIBLOCK_DIMENSION.height):
            block_row = []
            for column_i in range(self.MULTIBLOCK_DIMENSION.width):
                material = block_utility.material_instance_from_string(self.material.name(), image_key=image_key_count)
                image_key_count += 1
                pos = (topleft[0] + column_i * BLOCK_SIZE.width, topleft[1] + row_i * BLOCK_SIZE.height)
                block_row.append(material.to_block(pos, id=self.id, action=self._action_function))
            blocks.append(block_row)
        return blocks
