#!/usr/bin/python3

# library imports
import pygame
from typing import ClassVar, List, Tuple, Callable, TYPE_CHECKING, Union, Hashable
from abc import ABC

# own imports
import utility.constants as con
import utility.utilities as util
from utility import inventories, game_timing
if TYPE_CHECKING:
    import block_classes.materials as base_materials
    import block_classes.building_materials as building_materials


class Block(ABC):
    """
    Base class for the block_classes in image matrices
    """
    __slots__ = "rect", "material", "_action_function", "id", "light_level"

    SIZE: ClassVar[util.Size] = con.BLOCK_SIZE

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
    def transparant_group(
        self,
        value: int
    ):
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

    def destroy(self) -> List[inventories.Item]:
        """Get items returned by this block when destroyed and do actions neccesairy before destroying"""
        return [inventories.Item(self.material, 1)]

    def set_active(
        self,
        value: bool
    ):
        """Set the underlying material in an active state. This means that the surface that is returned will be
        different this does not directly reflect on the board, that has to be done separately"""
        if isinstance(self, VariableSurfaceBlock):
            self._set_changed(True)
        self.material.set_active(value)


class VariableSurfaceBlock(ABC):

    __changed: bool

    def __init__(self):
        self.__changed = False

    def update(self):
        """Function to be called when updating the surface"""
        pass

    def _set_changed(
        self,
        value: bool
    ):
        self.__changed = value

    @property
    def changed(self):
        """Check if the block image has changed and flip the flag if that is the case"""
        changed = self.__changed
        if changed is True:
            self.__changed = False
        return changed


class SurroundableBlock(Block, ABC):
    """Abstraction level for a Block that has surrounding blocks, to make sure that gets configured when adding"""
    __slots__ = "surrounding_blocks"
    surrounding_blocks: Tuple[Union[None, util.BlockPointer], Union[None, util.BlockPointer],
                              Union[None, util.BlockPointer], Union[None, util.BlockPointer]]

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        material: "building_materials.ConveyorBelt",
        **kwargs
    ):
        super().__init__(pos, material, **kwargs)
        self.surrounding_blocks = (None, None, None, None)


class ConveyorNetworkBlock(SurroundableBlock, VariableSurfaceBlock):
    """Conveyor bloks that transport items"""
    __slots__ = "current_item", "__current_push_direction", "__item_surface", "__exact_item_position",\
                "incomming_item", "next_block", "__previous_incomming_position", "_previous_surrounding_block_names"

    material: "building_materials.ConveyorBelt"
    current_item: Union[inventories.TransportItem, None]
    incomming_item: Union[inventories.TransportItem, None]
    __current_push_direction: int
    __item_surface: [None, pygame.Surface]
    __exact_item_position: List[int]
    __previous_incomming_position: Tuple[int, int]
    next_block: Union[Block, None]

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        material: "building_materials.ConveyorBelt",
        **kwargs
    ):
        SurroundableBlock.__init__(self, pos, material, **kwargs)
        VariableSurfaceBlock.__init__(self)
        self.current_item = None
        self.incomming_item = None
        self.__current_push_direction = 0  # value that tracks the previous pushed direction can be 0, 1 or 2
        self.__item_surface = None  # surface tracking for efficiency
        self.__exact_item_position = [0, 0]
        self.__previous_incomming_position = (0, 0)  # track the previous position of the incomming item for efficiency
        self.next_block = None  # the block selected to push an item to
        # track the previous block names for updating reasons
        self._previous_surrounding_block_names = [None for _ in range(len(self.surrounding_blocks))]

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
        self._set_changed(True)

    def remove_item(self):
        """Remove the current item"""
        self.current_item = None
        self.__exact_item_position = [0, 0]
        self.__item_surface = None
        self._set_changed(True)

    def update(self):
        self.check_item_movement()
        if [block.name() for block in self.surrounding_blocks] != self._previous_surrounding_block_names:
            self._previous_surrounding_block_names = [block.name() for block in self.surrounding_blocks]
            self.__change_material_image_key()

    def check_item_movement(self):
        """Move items within the conveyor belt"""
        if self.current_item is not None:
            self.__move_item_forward()
        elif self.incomming_item is not None:
            if self.incomming_item.rect.topleft != self.__previous_incomming_position:
                self.__previous_incomming_position = self.incomming_item.rect.topleft
                self._set_changed(True)
        else:
            self.__take_item()

    @game_timing.time_function("conveyor calcluation update", "move forward")
    def __move_item_forward(self):
        """Determine if an item needs to move to the center or to the next block"""
        previous_position = self.current_item.rect.topleft
        if self.material.direction == 0:
            if self.current_item.rect.centery > self.rect.centery:
                self.__move_towards_center()
            else:
                self.__move_towards_next_block()
        elif self.material.direction == 1:
            if self.current_item.rect.centerx < self.rect.centerx:
                self.__move_towards_center()
            else:
                self.__move_towards_next_block()
        elif self.material.direction == 2:
            if self.current_item.rect.centery < self.rect.centery:
                self.__move_towards_center()
            else:
                self.__move_towards_next_block()
        elif self.material.direction == 3:
            if self.current_item.rect.centerx > self.rect.centerx:
                self.__move_towards_center()
            else:
                self.__move_towards_next_block()

        if self.current_item is not None and previous_position != self.current_item.rect.topleft and \
                con.DEBUG.SHOW_BELT_ITEMS:
            self._set_changed(True)

    def __move_towards_center(self):
        """Move toward the center of a belt"""
        self.__set_item_position(self.material.direction)

    def __move_towards_next_block(self):
        """Move from the center of belt to an other belt of inventory"""
        self.__set_next_block()
        if self.next_block is not None:
            self.__check_next_block()
            if self.current_item is not None:
                self.__set_item_position(self.__get_next_block_direction())
        else:
            self.current_item.rect.center = self.rect.center

    def __set_next_block(self):
        """Set the value for the next block. This will be chosen dependant on the __current_push_direction. If the
        next_block is None as a result of the push direction then the push direction is cycled next."""
        elligable_blocks = self.__get_elligable_move_blocks()
        if self.next_block is None:
            self.__current_push_direction = (self.__current_push_direction + 1) % 3
        self.next_block = elligable_blocks[self.__current_push_direction]

    def __check_next_block(self):
        """Check of the block that is marked as next block needs to receibe a incomming item or a current item"""
        current_item_rect = self.current_item.rect
        direction = self.__get_next_block_direction()
        if not self.rect.contains(current_item_rect) and isinstance(self.next_block.block, ConveyorNetworkBlock) and \
                self.next_block.incomming_item is None:
            self.next_block.put_incomming_item(self.current_item)
        if (direction == 0 and self.next_block.rect.bottom >= current_item_rect.bottom) or \
                (direction == 1 and self.next_block.rect.left <= current_item_rect.left) or \
                (direction == 2 and self.next_block.rect.top <= current_item_rect.top) or \
                (direction == 3 and self.next_block.rect.right >= current_item_rect.right):
            if isinstance(self.next_block.block, ConveyorNetworkBlock):
                self.next_block.put_current_item(self.current_item)
            elif isinstance(self.next_block.block, ContainerBlock):
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

    def __set_y_item_position(
        self,
        sign: int
    ):
        """Change the y-coordinate of the the current_item"""
        item_rect = self.current_item.rect
        progression_fraction = con.GAME_TIME.get_time() / self.material.TRANSFER_TIME
        location_y = progression_fraction * (self.rect.height + item_rect.height)
        self.__exact_item_position[1] += location_y
        while self.__exact_item_position[1] > 4:
            self.current_item.rect.top += 4 * sign
            self.__exact_item_position[1] -= 4

    def __set_x_item_position(
        self,
        sign: int
    ):
        """Change the x-coordinate of the the current_item"""
        item_rect = self.current_item.rect
        progression_fraction = con.GAME_TIME.get_time() / self.material.TRANSFER_TIME
        location_x = progression_fraction * (self.rect.width + item_rect.width)
        self.__exact_item_position[0] += location_x
        while self.__exact_item_position[0] > 4:
            self.current_item.rect.left += 4 * sign
            self.__exact_item_position[0] -= 4

    def __get_elligable_move_blocks(self) -> List[Union[int, None]]:
        """Get a list of length 3 with the 3 blocks that are checked around a belt that an item can be pushed to.

        The requirements for an elligable block is that the block has to be an inventory or a belt and a certain
        direction relative to the direction of this block. Inventories are prioritzed to make sure that items go into
        an inventory if possible"""
        elligible_blocks = [None, None, None]
        is_inventorys = [False, False, False]

        # block 1
        block_index = (self.material.direction - 1) % 4
        block = self.surrounding_blocks[block_index]
        if (isinstance(block.block, ContainerBlock) and block.inventory.check_item_deposit(self.current_item.name()) and
                self.material.direction == block_index):
            elligible_blocks[0] = block
            is_inventorys[0] = True
        elif (isinstance(block.block, ConveyorNetworkBlock) and block.current_item is None and
              (block.incomming_item is None or self.current_item == block.incomming_item)
              and block.material.direction == block_index):
            elligible_blocks[0] = block

        # block 2
        block_index = self.material.direction
        block = self.surrounding_blocks[block_index]
        if (isinstance(block.block, ContainerBlock) and block.inventory.check_item_deposit(self.current_item.name()) and
                self.material.direction == block_index):
            elligible_blocks[1] = block
            is_inventorys[1] = True
        if (isinstance(block.block, ConveyorNetworkBlock) and block.current_item is None and
                (block.incomming_item is None or self.current_item == block.incomming_item) and
                block.material.direction in [block_index, (block_index + 1) % 4, (block_index - 1) % 4]):
            elligible_blocks[1] = block

        # block 3
        block_index = (self.material.direction + 1) % 4
        block = self.surrounding_blocks[block_index]
        if (isinstance(block.block, ContainerBlock) and block.inventory.check_item_deposit(self.current_item.name()) and
                self.material.direction == block_index):
            elligible_blocks[2] = block
            is_inventorys[2] = True
        if (isinstance(block.block, ConveyorNetworkBlock) and block.current_item is None and
                (block.incomming_item is None or self.current_item == block.incomming_item)
                and block.material.direction == block_index):
            elligible_blocks[2] = block

        # check if an inventory was encountered and if so make sure to set all non-inventories as invalid (None)
        if any(is_inventorys):
            for index in range(len(elligible_blocks)):
                if not is_inventorys[index]:
                    elligible_blocks[index] = None
        return elligible_blocks

    @game_timing.time_function("conveyor calcluation update", "take item")
    def __take_item(self):
        """Take an item from an inventory and set it as the current_item"""
        opposite_block = self.surrounding_blocks[self.material.direction - 2]  # block that is opposite belt direction
        if not isinstance(opposite_block.block, ContainerBlock):
            return
        item = opposite_block.get_transport_item(self.material.STACK_SIZE)
        if item is not None:
            self.current_item = item
            if self.material.direction == 0:
                self.current_item.rect.top = self.rect.bottom
            elif self.material.direction == 1:
                self.current_item.rect.right = self.rect.left
            elif self.material.direction == 2:
                self.current_item.rect.bottom = self.rect.top
            elif self.material.direction == 3:
                self.current_item.rect.left = self.rect.right
            if con.DEBUG.SHOW_BELT_ITEMS:
                self._set_changed(True)

    @property
    def surface(self) -> pygame.Surface:
        """Overwrite the surface return of this block by dynamically assigning a new value based on the item that is
        held"""
        if (self.current_item is None and self.incomming_item is None) or not con.DEBUG.SHOW_BELT_ITEMS:
            return self.material.surface
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

    def __change_material_image_key(self):
        """Set the image key of the material to match the surrounding conveyorbelts"""
        belt_directions = [None for _ in range(4)]
        belt_directions[(self.material.direction + 2) % 4] = self.material.direction  # noqa --> very weird typing error that makes not sense
        own_direction = self.material.direction
        for index, block in enumerate(self.surrounding_blocks):
            if isinstance(block.block, ContainerBlock) and \
                    (index == self.material.direction or index == (self.material.direction + 2) % 4):
                belt_directions[index] = index  # noqa --> very weird typing error that makes not sense
            elif isinstance(block.block, ConveyorNetworkBlock):
                # only save a direction when there is potential for a continuation
                if index == own_direction and block.direction != (own_direction + 2) % 4:
                    belt_directions[index] = index  # noqa
                elif index == (own_direction + 1) % 4 or index == (own_direction + 3) % 4:
                    if block.direction == (own_direction + 1) % 4 or block.direction == (own_direction + 3) % 4:
                        belt_directions[index] = block.direction
        total_valid_surrounding = len([direction for direction in belt_directions if direction is not None])
        if total_valid_surrounding > 2:
            self.__change_material_key_to_intersection(belt_directions, total_valid_surrounding)
        elif total_valid_surrounding == 2:
            self.__change_material_key_to_corner(belt_directions)
        else:
            self.__change_material_key_to_straight()

    def __change_material_key_to_intersection(
        self,
        belt_directions: List[Union[int, None]],
        total_valid_surrounding: int
    ):
        """Add an intersection between 3 or 4 belts based on surrounding belt connections"""
        second_part = [str(index) for index in range(len(belt_directions)) if belt_directions[index] is not None]
        self.material.image_key = f"{total_valid_surrounding}_{''.join(second_part)}_{self.material.direction}"
        self._set_changed(True)

    def __change_material_key_to_corner(
        self,
        belt_directions: List[Union[int, None]]
    ):
        """Add a corner connection between 2 belts based on belt direction"""
        own_direction = self.material.direction
        # get the belt that continues the conveyorline
        next_connecting_direction = [index for index, direction in enumerate(belt_directions)
                                     if direction is not None and
                                     index not in [(own_direction + 2) % 4, own_direction]]
        # no valid connector simply keep the image that was present
        if len(next_connecting_direction) == 0:
            self.__change_material_key_to_straight()
            return
        connecting_index = next_connecting_direction[0]
        # if the belt points into this belt then it is an intersection
        if connecting_index == (belt_directions[connecting_index] + 2) % 4:
            belt_directions[self.material.direction] = self.material.direction
            self.__change_material_key_to_intersection(belt_directions, 3)
        else:
            self.material.image_key = f"2_{(own_direction + 2) % 4}{connecting_index}"
            self._set_changed(True)

    def __change_material_key_to_straight(self):
        """Add a simple straigh piece of belt"""
        self.material.image_key = f"1_{self.material.direction}"
        self._set_changed(True)

    def destroy(self) -> List[inventories.Item]:
        items = super().destroy()
        if self.current_item is not None:
            items.append(self.current_item)
        return items


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
        item = self.inventory.get_random_item(amnt)
        if item is None:
            return item
        transport_rect = pygame.Rect(0, 0, *item.material.transport_surface.get_size())  # noqa
        transport_rect.center = self.rect.center
        return inventories.TransportItem(transport_rect, item.material, item.quantity)

    def destroy(self) -> List[inventories.Item]:
        items = super().destroy()
        items.extend(self.inventory.get_all_items(ignore_filter=True))
        return items


class MultiBlock(Block, ABC):
    MULTIBLOCK_LAYOUT: List[List[Hashable]] = [[1]]
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
        return cls.SIZE * (len(cls.MULTIBLOCK_LAYOUT[0]), len(cls.MULTIBLOCK_LAYOUT))

    def _get_blocks(self) -> List[List[Block]]:
        # has to be the case to prevent circular imports
        import block_classes.block_utility as block_utility

        blocks = []
        topleft = self.rect.topleft
        for row_i, row in enumerate(self.MULTIBLOCK_LAYOUT):
            block_row = []
            for column_i, image_key in enumerate(row):
                material = block_utility.material_instance_from_string(self.material.name(), image_key=image_key)
                pos = [topleft[0] + column_i * con.BLOCK_SIZE.width, topleft[1] + row_i * con.BLOCK_SIZE.height]
                block_row.append(material.to_block(pos, id_=self.id, action=self._action_function))
            blocks.append(block_row)
        return blocks

    def destroy(self) -> List[inventories.Item]:
        items = self.blocks[0][0].destroy()
        return items

    def set_active(
        self,
        value: bool
    ):
        if isinstance(self, VariableSurfaceBlock):
            self._set_changed(True)
        for row in self.blocks:
            for block in row:
                block.material.set_active(value)
