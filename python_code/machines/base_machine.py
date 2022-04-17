from typing import TYPE_CHECKING, Dict, Union, List, Type, Tuple

import utility.utilities as util
import utility.constants as con
import block_classes.machine_blocks

if TYPE_CHECKING:
    import pygame
    from block_classes.blocks import Block
    from block_classes.materials.materials import BaseMaterial

# TODO section
#  1: make sure that disconecting large parts works properly
#  2: have a max size
#  3: have other machine additions not exceed max size
#  4: make sure that replaced blocks are handled well


class Machine:

    _blocks: Dict[int, Dict[int, "Block"]]  # save _blocks by y_coord then by x_coord in a dict
    _sorted__blocks: List["Block"]
    terminal_block: Union[block_classes.machine_blocks.MachineTerminalBlock, None]
    rect: "pygame.Rect"
    id: str
    size: int

    def __init__(self, block):
        self._blocks = {}
        self._sorted__blocks = []
        self.terminal_block = None
        self.rect = block.rect.copy()
        self.id = util.unique_id()
        self.size = 0
        self.add_block(block)

    def update(self):
        pass

    def add_block(self, block):
        # it is very important that this block is connected, always make sure to check before with can_add()
        if block.coord[1] in self._blocks:
            if block.rect.left < self.rect.left:
                self.rect.width += self.rect.left - block.rect.left
                self.rect.left = block.rect.left
            elif block.rect.right > self.rect.right:
                self.rect.width += block.rect.right - self.rect.right
            self._blocks[block.coord[1]][block.coord[0]] = block
        else:
            if block.rect.top < self.rect.top:
                self.rect.height += self.rect.top - block.rect.top
                self.rect.top = block.rect.top
            elif block.rect.bottom > self.rect.bottom:
                self.rect.height += block.rect.bottom - self.rect.bottom
            self._blocks[block.coord[1]] = {block.coord[0]: block}
        if isinstance(block, block_classes.machine_blocks.MachineTerminalBlock):
            if self.terminal_block is None:
                self._set_terminal_block(block)
            else:
                block.interface = self.terminal_block.interface
        self.size += 1

    def remove_block(self, block):
        if block.id == self.terminal_block.id:
            self.terminal_block = None
        del self._blocks[block.coord[1]][block.coord[0]]
        self.size -= 1

    def add_machine(self, machine: "Machine", connecting_block_coord):
        # it is assumed that machines are connected
        for y_dict in machine._blocks.values():
            for block in y_dict.values():
                self.add_block(block)

    def _set_terminal_block(self, terminal_block: block_classes.machine_blocks.MachineTerminalBlock):
        self.terminal_block = terminal_block
        self.terminal_block.set_machine(self)

    def can_add(self, coord: Union[Tuple[int, int], List[int]]):
        # check if the coordinate is next to any of the _blocks in the machine
        # given the assumption the coordinate is not within the machine
        if coord[1] in self._blocks:
            if coord[0] + con.BLOCK_SIZE.width in self._blocks[coord[1]]:
                return True
            elif coord[0] - con.BLOCK_SIZE.width in self._blocks[coord[1]]:
                return True
            return False
        elif coord[1] - con.BLOCK_SIZE.height in self._blocks and \
                coord[0] in self._blocks[coord[1] - con.BLOCK_SIZE.height]:
            return True
        elif coord[1] + con.BLOCK_SIZE.height in self._blocks and \
                coord[0] in self._blocks[coord[1] + con.BLOCK_SIZE.height]:
            return True
        return False

    def get_blocks(
        self,
        wanted_type: Type["BaseMaterial"] = None
    ) -> List["MachineBlock"]:
        # iter all parts of the machine first x then y and return parts
        all_blocks = []
        y_keys = list(self._blocks.keys())
        # have the y-axis in the matematical expected direction
        y_keys.sort(reverse=True)
        all_x_coords = set()
        for y_coord, y_key in enumerate(y_keys):
            x_dict = self._blocks[y_key]
            x_keys = list(x_dict.keys())
            x_keys.sort()
            for x_key in x_keys:
                all_x_coords.add(x_key)
                block = x_dict[x_key]
                if wanted_type is None or isinstance(block.material, wanted_type):
                    mblock = MachineBlock(block, (x_key, y_coord))
                    all_blocks.append(mblock)
        # map the x_keys to proper coordinates
        sorted_x_coords = sorted(list(all_x_coords))
        x_map = {coord: index for index, coord in enumerate(sorted_x_coords)}
        for index in range(len(all_blocks)):
            block = all_blocks[index]
            block.coordinate[0] = x_map[block.coordinate[0]]
            all_blocks[index] = block
        return all_blocks

    def __contains__(self, block):
        return block.coord[1] in self._blocks and block.coord[0] in self._blocks[block.coord[1]]


class MachineBlock:
    """Wrapper around a block that allows for restricted acces and has the machine coordinate"""

    def __init__(self, block: "Block", coord: Union[Tuple[int, int], List[int]]):
        self.type = type(block.material).__name__
        self.coordinate = list(coord)

    def get_letter(self) -> str:
        return self.type.replace("Machine", "")[0]

    def activate(self):
        return "needs implementation"

    @property
    def x_coordinate(self):
        return self.coordinate[0]

    @property
    def y_coordinate(self):
        return self.coordinate[1]

    def __repr__(self):
        return f"MachineBlock<({self.x_coordinate}, {self.y_coordinate}), {self.type}>"
