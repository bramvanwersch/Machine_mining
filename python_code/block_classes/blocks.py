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
    __slots__ = "current_item", "__current_push_direction", "__item_surface", "changed", "__exact_item_position",\
                "incomming_item", "next_block", "__previous_incomming_position"

    material: "building_materials.ConveyorBelt"
    current_item: Union[inventories.TransportItem, None]
    incomming_item: Union[inventories.TransportItem, None]
    __current_push_direction: int
    __item_surface: [None, pygame.Surface]
    __exact_item_position: List[int]
    __previous_incomming_position: Tuple[int, int]
    changed: bool
    next_block: Union[Block, None]

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        material: "building_materials.ConveyorBelt",
        **kwargs
    ):
        super().__init__(pos, material, **kwargs)
        self.current_item = None
        self.incomming_item = None
        self.__current_push_direction = 0  # value that tracks the previous pushed direction can be 0, 1 or 2
        self.__item_surface = None  # surface tracking for efficiency
        self.__exact_item_position = [0, 0]
        self.__previous_incomming_position = (0, 0)  # track the previous position of the incomming item for efficiency
        self.changed = False  # flag for changes
        self.next_block = None  # the block selected to push an item to

    def put_current_item(
        self,
        item: inventories.TransportItem
    ):
        """Put an item at the current_item value and reset all relevant values"""
        self.current_item = item
        self.incomming_item = None
        self.__exact_item_position = [0, 0]
        self.__previous_incomming_position = (0, 0)
        self.__item_surface = None
        self.next_block = None

    def put_incomming_item(
        self,
        item: inventories.TransportItem
    ):
        """Add an incomming item to allow it to be drawn"""
        self.incomming_item = item
        self.__previous_incomming_position = item.rect.topleft

    def remove_item(self):
        """Remove the current item"""
        self.current_item = None
        self.__exact_item_position = [0, 0]
        self.__item_surface = None
        self.changed = True

    def check_item_movement(
        self,
        surrounding_blocks: List[Union[None, Block]]
    ):
        """Move items within the conveyor belt"""
        if self.current_item is not None:
            self.__move_item_forward(surrounding_blocks)
        elif self.incomming_item is not None:
            if self.incomming_item.rect.topleft != self.__previous_incomming_position:
                self.__previous_incomming_position = self.incomming_item.rect.topleft
                self.changed = True
        else:
            self.__take_item(surrounding_blocks)

    def __set_item_position(
        self,
        direction: int
    ):
        """Set the position of an item based on the direction an item is moving. With 0-3 representing north, east,
         south, west"""
        if direction == 0:
            self.__set_y_item_position(-1)
        elif direction == 1:
            self.__set_x_item_position(1)
        elif direction == 2:
            self.__set_y_item_position(1)
        elif direction == 3:
            self.__set_x_item_position(-1)

    def __move_item_forward(
        self,
        surrounding_blocks: List[Union[None, Block]]
    ):
        previous_position = self.current_item.rect.topleft
        if self.material.image_key == 0:
            if self.current_item.rect.centery > self.rect.centery:
                self.__move_towards_center()
                if self.current_item.rect.centery < self.rect.centery:
                    self.current_item.rect.center = self.rect.center
            else:
                self.__move_towards_next_block(surrounding_blocks)
        elif self.material.image_key == 1:
            if self.current_item.rect.centerx < self.rect.centerx:
                self.__move_towards_center()
                if self.current_item.rect.centerx > self.rect.centerx:
                    self.current_item.rect.center = self.rect.center
            else:
                self.__move_towards_next_block(surrounding_blocks)
        elif self.material.image_key == 2:
            if self.current_item.rect.centery < self.rect.centery:
                self.__move_towards_center()
                if self.current_item.rect.centery > self.rect.centery:
                    self.current_item.rect.center = self.rect.center
            else:
                self.__move_towards_next_block(surrounding_blocks)
        elif self.material.image_key == 3:
            if self.current_item.rect.centerx > self.rect.centerx:
                self.__move_towards_center()
                if self.current_item.rect.centerx < self.rect.centerx:
                    self.current_item.rect.center = self.rect.center
            else:
                self.__move_towards_next_block(surrounding_blocks)

        if self.current_item is not None and previous_position != self.current_item.rect.topleft:
            self.changed = True

    def __move_towards_center(self):
        """Move toward the center of a belt"""
        self.__set_item_position(self.material.image_key)

    def __move_towards_next_block(
        self,
        surrounding_blocks: List[Union[None, Block]]
    ):
        """Move from the center of belt to an other belt of inventory"""
        self.__set_next_block(surrounding_blocks)
        if self.next_block is not None:
            self.__check_next_block()
            if self.current_item is not None:
                self.__set_item_position(self.__get_next_block_direction())
        else:
            self.current_item.rect.center = self.rect.center

    def __set_next_block(
        self,
        surrounding_blocks: List[Union[None, Block]]
    ):
        """Set the value for the next block. This will be chosen dependant on the __current_push_direction. If the
        next_block is None as a result of the push direction then the push direction is cycled next."""
        elligable_blocks = self.__get_elligable_move_blocks(surrounding_blocks)
        if self.next_block is None:
            self.__current_push_direction = (self.__current_push_direction + 1) % 3
        self.next_block = elligable_blocks[self.__current_push_direction]

    def __check_next_block(self):
        """Check of the block that is marked as next block needs to receibe a incomming item or a current item"""
        current_item_rect = self.current_item.rect
        direction = self.__get_next_block_direction()
        if not self.rect.contains(current_item_rect) and isinstance(self.next_block, ConveyorNetworkBlock):
            self.next_block.put_incomming_item(self.current_item)
        if (direction == 0 and self.next_block.rect.bottom >= current_item_rect.bottom) or \
                (direction == 1 and self.next_block.rect.left <= current_item_rect.left) or \
                (direction == 2 and self.next_block.rect.top <= current_item_rect.top) or \
                (direction == 3 and self.next_block.rect.right >= current_item_rect.right):
            if isinstance(self.next_block, ConveyorNetworkBlock):
                self.next_block.put_current_item(self.current_item)
            elif isinstance(self.next_block, ContainerBlock):
                self.next_block.inventory.add_items(self.current_item)
            self.remove_item()

    def __get_next_block_direction(self) -> int:
        """Determine what direction the next_block is compared to the current_item"""
        if self.next_block.coord[1] < self.coord[1]:
            return 0  # north direction
        if self.next_block.coord[0] > self.coord[0]:
            return 1  # east direction
        if self.next_block.coord[1] > self.coord[1]:
            return 2  # south direction
        if self.next_block.coord[0] < self.coord[0]:
            return 3  # west direction

    def __set_y_item_position(
        self,
        sign: int
    ):
        """Change the y-coordinate of the the current_item"""
        item_rect = self.current_item.rect
        progression_fraction = con.GAME_TIME.get_time() / self.material.TRANSFER_TIME
        location_y = progression_fraction * (self.rect.height + item_rect.height)
        self.__exact_item_position[1] += location_y
        while self.__exact_item_position[1] > 1:
            self.current_item.rect.top += 1 * sign
            self.__exact_item_position[1] -= 1

    def __set_x_item_position(
        self,
        sign: int
    ):
        """Change the x-coordinate of the the current_item"""
        item_rect = self.current_item.rect
        progression_fraction = con.GAME_TIME.get_time() / self.material.TRANSFER_TIME
        location_x = progression_fraction * (self.rect.width + item_rect.width)
        self.__exact_item_position[0] += location_x
        while self.__exact_item_position[0] > 1:
            self.current_item.rect.left += 1 * sign
            self.__exact_item_position[0] -= 1

    def __get_elligable_move_blocks(
        self,
        surrounding_blocks: List[Union[None, Block]]
    ) -> List[Union[int, None]]:
        """Get a list of length 3 with the 3 blocks that are checked around a belt that an item can be pushed to.

        The requirements for an elligable block is that the block has to be an inventory or a belt and a certain
        direction"""
        elligible_blocks = [None, None, None]

        # block 1
        block_index = (self.material.image_key - 1) % 4
        block = surrounding_blocks[block_index]
        if (isinstance(block, ContainerBlock) and block.inventory.check_item_deposit(self.current_item.name()) and
                self.material.image_key == block_index):
            elligible_blocks[0] = block
        elif (isinstance(block, ConveyorNetworkBlock) and block.current_item is None and
              (block.incomming_item is None or self.current_item == block.incomming_item)
              and block.material.image_key == block_index):
            elligible_blocks[0] = block

        # block 2
        block_index = self.material.image_key
        block = surrounding_blocks[block_index]
        if (isinstance(block, ContainerBlock) and block.inventory.check_item_deposit(self.current_item.name()) and
                self.material.image_key == block_index):
            elligible_blocks[1] = block
        if (isinstance(block, ConveyorNetworkBlock) and block.current_item is None and
                (block.incomming_item is None or self.current_item == block.incomming_item) and
                block.material.image_key in [block_index, (block_index + 1) % 4, (block_index - 1) % 4]):
            elligible_blocks[1] = block

        # block 3
        block_index = (self.material.image_key + 1) % 4
        block = surrounding_blocks[block_index]
        if (isinstance(block, ContainerBlock) and block.inventory.check_item_deposit(self.current_item.name()) and
                self.material.image_key == block_index):
            elligible_blocks[2] = block
        if (isinstance(block, ConveyorNetworkBlock) and block.current_item is None and
                (block.incomming_item is None or self.current_item == block.incomming_item)
                and block.material.image_key == block_index):
            elligible_blocks[2] = block
        return elligible_blocks

    def __take_item(
        self,
        surrounding_blocks: List[Union[None, Block]]
    ):
        """Take an item from an inventory and set it as the current_item"""
        opposite_block = surrounding_blocks[self.material.image_key - 2]  # block that is opposite the belt direction
        if not isinstance(opposite_block, ContainerBlock):
            return
        item = opposite_block.get_transport_item(self.material.STACK_SIZE)
        if item is not None:
            self.current_item = item
            if self.material.image_key == 0:
                self.current_item.rect.top = self.rect.bottom
            elif self.material.image_key == 1:
                self.current_item.rect.right = self.rect.left
            elif self.material.image_key == 2:
                self.current_item.rect.bottom = self.rect.top
            elif self.material.image_key == 3:
                self.current_item.rect.left = self.rect.right
            self.changed = True

    @property
    def surface(self) -> pygame.Surface:
        """Overwrite the surface return of this block by dynamically assigning a new value based on the item that is
        held"""
        if self.current_item is None and self.incomming_item is None:
            return self.material.surface
        if self.changed:
            self.__item_surface = self.material.surface.copy()
            if self.current_item is not None:
                relative_position = (self.current_item.rect.left - self.rect.left,
                                     self.current_item.rect.top - self.rect.top)
                self.__item_surface.blit(self.current_item.material.transport_surface, relative_position)  # noqa
            elif self.incomming_item is not None:
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
