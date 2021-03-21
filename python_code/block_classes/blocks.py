#!/usr/bin/python3

# library imports
import pygame
from typing import ClassVar, List, Tuple, Callable, TYPE_CHECKING, Union
from abc import ABC

# own imports
import utility.constants as con
import utility.utilities as util
from utility import inventories
if TYPE_CHECKING:
    import block_classes.materials as base_materials
    import block_classes.building_materials as building_materials



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

    @property
    def surface(self) -> pygame.Surface:
        """Make inheritance more apparent"""
        return self.material.surface

    @classmethod
    def size(cls) -> Union[Tuple[int, int], List[int], util.Size]:
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
    __slots__ = "current_item", "progress", "__push_priority_direction", "__item_surface",\
                "changed", "__exact_item_position", "incomming_item"

    material: "building_materials.ConveyorBelt"
    current_item: Union[inventories.TransportItem, None]
    progress: List[int]
    __push_prioity_direction: int
    __item_surface: [None, pygame.Surface]
    changed: bool

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        material: "building_materials.ConveyorBelt",
        **kwargs
    ):
        super().__init__(pos, material, **kwargs)
        self.current_item = None
        self.incomming_item = None
        self.progress = [0, self.material.TRANSFER_TIME]
        self.__push_priority_direction = 0  # value that tracks the previous pushed direction can be 0, 1 or 2
        self.__item_surface = None
        self.__exact_item_position = [0, 0]
        self.changed = False

    def put_current_item(
        self,
        item: inventories.TransportItem
    ):
        self.current_item = item
        if self.incomming_item is not None:
            fraction_distance_moved = item.rect.width / (item.rect.width + self.rect.width)
            self.progress = [fraction_distance_moved * self.material.TRANSFER_TIME, self.material.TRANSFER_TIME]
        else:
            self.progress = [0, self.material.TRANSFER_TIME]
        self.incomming_item = None
        self.__exact_item_position = [0, 0]
        self.__item_surface = None

    def put_incomming_item(self, item):
        self.incomming_item = item

    def remove_item(self):
        self.current_item = None
        self.progress = [0, self.material.TRANSFER_TIME]
        self.__exact_item_position = [0, 0]
        self.__item_surface = None
        self.changed = True

    def check_item_movement(
        self,
        surrounding_blocks: List[Union[None, Block]]
    ):
        """Move items within the conveyor belt"""
        if self.current_item is not None:
            self.__move_item(surrounding_blocks)
        elif self.incomming_item is not None:
            self.changed = True
        else:
            self.__take_item(surrounding_blocks)

    def __move_item(
        self,
        surrounding_blocks: List[Union[None, Block]]
    ):
        """Move an item within the belt or to the next belt when required"""
        # dont keep counting if there is no place to put the item

        if self.progress[0] <= self.progress[1]:
            self.__move_item_forward(surrounding_blocks)
        #     if new_location != self.__item_location:
        #         self.__item_location = new_location
        #         self.changed = True
        # if new_location[0] > self.rect.width:
        #
        # if self.progress[0] > self.progress[1]:
        #     elligable_blocks = [surrounding_blocks[self.material.image_key - 1],
        #                         surrounding_blocks[self.material.image_key],
        #                         surrounding_blocks[(self.material.image_key + 1) % 4]]
        #     for block in elligable_blocks[self.__push_priority_direction:] + \
        #             elligable_blocks[:self.__push_priority_direction]:
        #         if block is None:
        #             continue
        #         if isinstance(block, ConveyorNetworkBlock) and block.current_item is None:
        #             block.put_item(self.current_item)
        #             self.remove_item()
        #             break
        #         elif isinstance(block, ContainerBlock) and block.inventory.check_item_deposit(self.current_item.name):
        #             block.inventory.add_items(self.current_item)
        #             self.remove_item()
        #             break
        #     self.__push_priority_direction += 1

    def __move_item_forward(self, surrounding_blocks):
        # TODO make universal for all directions
        previous_position = self.current_item.rect.topleft
        if self.material.image_key == 1 and self.current_item.rect.centerx < self.rect.centerx:
            self.__set_item_position()
            self.progress[0] += con.GAME_TIME.get_time()
        else:
            elligable_blocks = self.__get_elligable_move_blocks(surrounding_blocks)
            if len(elligable_blocks) > 0:
                # TODO make sure that the item is pushed in the direction of next
                self.__set_item_position()
                self.progress[0] += con.GAME_TIME.get_time()
                # TODO save the elligable block and make the whole system more save
                if not self.rect.contains(self.current_item.rect):
                    elligable_blocks[0].put_incomming_item(self.current_item)
                if not self.rect.colliderect(self.current_item.rect):
                    elligable_blocks[0].put_current_item(self.current_item)
                    self.remove_item()
                    return
        if previous_position != self.current_item.rect.topleft:
            self.changed = True

    def __set_item_position(self):
        item_rect = self.current_item.rect
        progression_fraction = con.GAME_TIME.get_time() / self.progress[1]
        # from the start of the right to the end of the left
        location_x = progression_fraction * (self.rect.width + item_rect.width)
        # location_y = max(0, self.rect.height - item_rect.height - 3)
        self.__exact_item_position[0] += location_x
        while self.__exact_item_position[0] > 1:
            self.current_item.rect.left += 1
            self.__exact_item_position[0] -= 1
        # self.current_item.rect.top = location_y

    def __get_elligable_move_blocks(self, surrounding_blocks):
        elligible_blocks = []
        for i in range(-1, 2):
            block_index = (self.material.image_key - i) % 4
            block = surrounding_blocks[block_index]
            if isinstance(block, ContainerBlock) and block.inventory.check_item_deposit(self.current_item.name()) or \
                    (isinstance(block, ConveyorNetworkBlock) and block.material.image_key == block_index and
                     block.current_item is None):
                elligible_blocks.append(block)
        return elligible_blocks

    def __take_item(
        self,
        surrounding_blocks
    ):
        """Take an item from an inventory"""
        opposite_block = surrounding_blocks[self.material.image_key - 2]  # block that is opposite the belt direction
        if not isinstance(opposite_block, ContainerBlock):
            return
        item = opposite_block.get_transport_item(self.material.STACK_SIZE)
        if item is not None:
            self.current_item = item
            # TODO make a case for all directions
            if self.material.image_key == 1:
                self.current_item.rect.right = self.rect.left
            self.changed = True

    @property
    def surface(self) -> pygame.Surface:
        if self.current_item is None and self.incomming_item is None:
            return self.material.surface
        if self.changed:
            self.__item_surface = self.material.surface.copy()
            if self.current_item is not None:
                relative_position = (self.current_item.rect.left - self.rect.left,
                                     self.current_item.rect.top - self.rect.top)
                self.__item_surface.blit(self.current_item.material.transport_surface, relative_position)  # noqa
            if self.incomming_item is not None:
                relative_position = (self.incomming_item.rect.left - self.rect.left,
                                     self.incomming_item.rect.top - self.rect.top)
                self.__item_surface.blit(self.incomming_item.material.transport_surface, relative_position)  # noqa
        return self.__item_surface


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

    def get_transport_item(
        self,
        amnt: int
    ) -> Union[inventories.TransportItem, None]:
        """Get the first allowed item from an inventory and place it into a TransportItem object"""
        item = self.inventory.get_first(amnt)
        if item is None:
            return item
        transport_rect = pygame.Rect(0, 0, *item.material.transport_surface.get_size())
        transport_rect.center = self.rect.center
        return inventories.TransportItem(transport_rect, item.material, item.quantity)


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
