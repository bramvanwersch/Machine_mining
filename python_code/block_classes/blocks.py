#!/usr/bin/python3

# library imports
import pygame
from typing import ClassVar, List, Tuple, Callable, TYPE_CHECKING
from abc import ABC, abstractmethod

# own imports
import utility.constants as con
import utility.utilities as util
if TYPE_CHECKING:
    import block_classes.materials as base_materials
    import inventories


class Block(ABC):
    """
    Base class for the block_classes in image matrices
    """
    SIZE: ClassVar[util.Size] = con.BLOCK_SIZE
    __slots__ = "rect", "material", "_action_function", "id", "light_level"

    rect: pygame.Rect
    material: "base_materials.BaseMaterial"
    _action_function: Callable
    id: str
    light_level: int

    def __init__(
        self,
        pos: List[int],
        material: "base_materials.BaseMaterial",
        id_: str = None,
        action: Callable = None,
        light_level: int = 0
    ):
        self.rect = pygame.Rect((pos[0], pos[1], self.SIZE.width, self.SIZE.height))
        self.material = material
        self._action_function = action
        self.id = id_ if id_ else util.unique_id()
        self.light_level = light_level

    def __getattr__(self, item):
        return getattr(self.material, item)

    def action(self) -> None:
        """Trigger action defined in self._action_function"""
        if self._action_function is not None:
            self._action_function()

    @property
    def coord(self) -> Tuple[int, int]:
        """Convenience coordinate"""
        return self.rect.topleft

    @property
    def transparant_group(self):
        return self.material.transparant_group

    @transparant_group.setter
    def transparant_group(self, value):
        self.material.transparant_group = value

    def is_task_allowded(self, task_type: str) -> bool:
        """Check if the material allows a task to be performed"""
        return task_type in self.material.allowed_tasks

    def name(self) -> str:
        """name of material"""
        return self.material.name()

    def __eq__(self, other):
        """Compare this block instance with a string, comparing the name of this block with another"""
        if not isinstance(other, str) and other is not None:
            raise NotImplementedError("For comparissons with blocks use strings")
        return other == self.material.name()

    def __hash__(self):
        return hash((self.coord, self.name()))


class NetworkEdgeBlock(Block):
    """Block that is part of a network"""
    __slots__ = "network_group"

    network_group: int

    def __init__(
        self,
        pos: List[int],
        material: "base_materials.BaseMaterial",
        group: int = 1,
        **kwargs
    ):
        super().__init__(pos, material, **kwargs)
        self.network_group = group


class ContainerBlock(NetworkEdgeBlock):
    """
    Block that has an inventory
    """
    __slots__ = "inventory"

    inventory: "inventories.Inventory"

    def __init__(
        self,
        pos: List[int],
        material: "base_materials.BaseMaterial",
        inventory: "inventories.Inventory" = None,
        **kwargs
    ):
        super().__init__(pos, material, **kwargs)
        self.inventory = inventory


class MultiBlock(Block, ABC):
    # have this here since you are technically allowed to call the size
    MULTIBLOCK_DIMENSION: ClassVar[util.Size] = util.Size(1, 1)
    SIZE = Block.SIZE * MULTIBLOCK_DIMENSION
    __slots__ = "blocks"

    blocks: List[List[Block]]

    def __init__(
        self,
        pos: List[int],
        material: "base_materials.BaseMaterial",
        **kwargs
    ):
        super().__init__(pos, material, **kwargs)
        self.blocks = self._get_blocks()

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def MULTIBLOCK_DIMENSION(self) -> ClassVar[util.Size]:
        pass

    def _get_blocks(self) -> List[List[Block]]:
        # has to be the case to prevent circular imports
        import block_classes.block_utility as block_utility
        blocks = []
        topleft = self.rect.topleft
        image_key_count = 1
        for row_i in range(self.MULTIBLOCK_DIMENSION.height):
            block_row = []
            for column_i in range(self.MULTIBLOCK_DIMENSION.width):
                material = block_utility.material_instance_from_string(self.material.name(), image_key=image_key_count)
                image_key_count += 1
                pos = [topleft[0] + column_i * con.BLOCK_SIZE.width, topleft[1] + row_i * con.BLOCK_SIZE.height]
                block_row.append(material.to_block(pos, id_=self.id, action=self._action_function))
            blocks.append(block_row)
        return blocks
