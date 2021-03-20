#!/usr/bin/python3

# library imports
import pygame
from typing import ClassVar, List, Tuple, Callable, TYPE_CHECKING, Union
from abc import ABC

# own imports
import utility.constants as con
import utility.utilities as util
if TYPE_CHECKING:
    import block_classes.materials as base_materials, building_materials
    from utility import inventories


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
        pos: Union[Tuple[int, int], List[int]],
        material: "base_materials.BaseMaterial",
        id_: str = None,
        action: Callable = None,
        light_level: int = 0
    ):
        self.rect = pygame.Rect((pos[0], pos[1], self.size().width, self.size().height))
        self.material = material
        self._action_function = action
        self.id = id_ if id_ else util.unique_id()
        self.light_level = light_level

    def __getattr__(self, item):
        return getattr(self.material, item)

    @classmethod
    def size(cls):
        """Allow inheriting classes to modify this value in a flexible way"""
        return cls.SIZE

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

    def is_task_allowded(
        self,
        task_type: str
    ) -> bool:
        """Check if the material allows a task to be performed"""
        return task_type in self.material.allowed_tasks

    def is_solid(self) -> bool:
        """Convenience method to test if a block is solid"""
        return self.transparant_group == 0

    def name(self) -> str:
        """name of material"""
        return self.material.name()


class ConveyorNetworkBlock(Block):
    """Conveyor bloks that transport items"""
    __slots__ = "current_item", "progress", "__push_priority_direction"

    material: "building_materials.ConveyorBelt"
    current_item: Union["inventories.Item", None]
    progress: List[int]
    __push_prioity_direction: int

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        material: "building_materials.ConveyorBelt",
        **kwargs
    ):
        super().__init__(pos, material, **kwargs)
        self.current_item = None
        self.progress = [0, self.material.TRANSFER_TIME]
        self.__push_priority_direction = 0  # value that tracks the previous pushed direction can be 0, 1 or 2

    def put_item(
        self,
        item: "inventories.Item"
    ):
        self.current_item = item
        self.progress = [0, self.material.TRANSFER_TIME]

    def check_item_movement(
        self,
        surrounding_blocks: List[Union[None, Block]]
    ):
        if self.current_item is not None:
            self.__move_item(surrounding_blocks)
        else:
            self.__take_item(surrounding_blocks)

    def __move_item(
        self,
        surrounding_blocks: List[Union[None, Block]]
    ):
        """Move an item within the belt or to the next belt when required"""
        # dont keep counting if there is no place to put the item
        if self.progress[0] <= self.progress[1]:
            self.progress[0] += con.GAME_TIME.get_time()
        if self.progress[0] > self.progress[1]:
            elligable_blocks = [surrounding_blocks[self.material.image_key - 1],
                                surrounding_blocks[self.material.image_key],
                                surrounding_blocks[(self.material.image_key + 1) % 4]]
            for block in elligable_blocks[self.__push_priority_direction:] + \
                    elligable_blocks[:self.__push_priority_direction]:
                if block is None:
                    continue
                if isinstance(block, ConveyorNetworkBlock) and block.current_item is None:
                    block.put_item(self.current_item)
                    self.current_item = None
                    break
                elif isinstance(block, ContainerBlock) and block.inventory.check_item_deposit(self.current_item.name):
                    block.inventory.add_items(self.current_item)
                    self.current_item = None
                    break
            self.__push_priority_direction += 1

    def __take_item(
        self,
        surrounding_blocks
    ):
        opposite_block = surrounding_blocks[self.material.image_key - 2]  # block that is opposite the belt direction
        if not isinstance(opposite_block, ContainerBlock):
            return
        item = opposite_block.inventory.get_first(self.material.STACK_SIZE)
        if item is not None:
            self.current_item = item


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
    """Block that has an inventory"""
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
    MULTIBLOCK_DIMENSION: ClassVar[util.Size] = util.Size(1, 1)
    # this works fine with inheritance
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

    @classmethod
    def size(cls) -> ClassVar[util.Size]:
        return cls.SIZE * cls.MULTIBLOCK_DIMENSION

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
