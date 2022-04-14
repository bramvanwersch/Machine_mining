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

    _blocks: Dict[int, Dict[int, "Block"]]  # save blocks by y_coord then by x_coord in a dict
    _sorted_blocks: List["Block"]
    terminal_block: Union[block_classes.machine_blocks.MachineTerminalBlock, None]
    rect: "pygame.Rect"
    id: str
    size: int

    def __init__(self, block):
        self._blocks = {}
        self._sorted_blocks = []
        self.terminal_block = None
        self.rect = block.rect.copy()
        self.id = util.unique_id()
        self.size = 1
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
        if self.terminal_block is not None:
            self.terminal_block.add_block_to_interface(block)
        if isinstance(block, block_classes.machine_blocks.MachineTerminalBlock):
            if self.terminal_block is None:
                self._set_terminal_block(block)
            else:
                block.interface = self.terminal_block.interface
        self.size += 1

    def remove_block(self, block):
        if block.id == self.terminal_block.id:
            self.terminal_block = None
        if self.terminal_block is not None:
            self.terminal_block.remove_block_from_interface(block)
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
        # check if the coordinate is next to any of the blocks in the machine
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
    ) -> List["Block"]:
        # iter all parts of the machine first x then y and return parts
        all_blocks = []
        y_keys = list(self._blocks.keys())
        # have the y-axis in the matematical expected direction
        y_keys.sort(reverse=True)
        for y_key in y_keys:
            x_dict = self._blocks[y_key]
            x_keys = list(x_dict.keys())
            x_keys.sort()
            for x_key in x_keys:
                block = x_dict[x_key]
                if wanted_type is None or isinstance(block.material, wanted_type):
                    all_blocks.append(block)
        return all_blocks

    def __contains__(self, block):
        return block.coord[1] in self._blocks and block.coord[0] in self._blocks[block.coord[1]]
