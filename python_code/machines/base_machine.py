from typing import TYPE_CHECKING, Dict

import utility.utilities as util
import utility.constants as con
import block_classes.machine_blocks

if TYPE_CHECKING:
    import pygame
    from block_classes.blocks import Block


class Machine:

    rect: "pygame.Rect"
    blocks: Dict[int, Dict[int, "Block"]]

    def __init__(self, block):
        self.blocks = {}
        self.terminal_block = None
        self.rect = block.rect.copy()
        self.id = util.unique_id()
        self.size = 1
        self.add_block(block)

    def add_block(self, block):
        # it is very important that this block is connected, always make sure to check before with can_add()
        if block.coord[1] in self.blocks:
            if block.rect.left < self.rect.left:
                self.rect.left = block.rect.left
                self.rect.width += self.rect.left - block.rect.left
            elif block.rect.right > self.rect.right:
                self.rect.width += block.rect.right - self.rect.right
            self.blocks[block.coord[1]][block.coord[0]] = block
        else:
            if block.rect.top < self.rect.top:
                self.rect.top = block.rect.top
                self.rect.height += self.rect.top - block.rect.top
            elif block.rect.bottom > self.rect.bottom:
                self.rect.height += block.rect.bottom - self.rect.bottom
            self.blocks[block.coord[1]] = {block.coord[0]: block}
        if isinstance(block, block_classes.machine_blocks.MachineTerminalBlock):
            if self.terminal_block is None:
                self.terminal_block = block
                self.terminal_block.set_machine(self)
            else:
                block.interface = self.terminal_block.interface
        self.size += 1

    def remove_block(self, block):
        del self.blocks[block.coord[1]][block.coord[0]]

    def add_machine(self, machine):
        # it is assumed that machines are connected
        for y_dict in machine.blocks.values():
            for block in y_dict.values():
                self.add_block(block)

    def can_add(self, coord):
        # check if the coordinate is next to any of the blocks in the machine
        # given the assumption the coordinate is not within the machine
        if coord[1] in self.blocks:
            if coord[0] + con.BLOCK_SIZE.width in self.blocks[coord[1]]:
                return True
            elif coord[0] - con.BLOCK_SIZE.width in self.blocks[coord[1]]:
                return True
            return False
        elif coord[1] - con.BLOCK_SIZE.height in self.blocks and \
                coord[0] in self.blocks[coord[1] - con.BLOCK_SIZE.height]:
            return True
        elif coord[1] + con.BLOCK_SIZE.height in self.blocks and \
                coord[0] in self.blocks[coord[1] + con.BLOCK_SIZE.height]:
            return True
        return False

    def __contains__(self, block):
        return block.coord[1] in self.blocks and block.coord[0] in self.blocks[block.coord[1]]

