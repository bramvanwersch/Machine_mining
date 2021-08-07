import utility.utilities as util
import utility.constants as con
import block_classes.machine_blocks


class Machine:
    def __init__(self, block):
        self.blocks = {block.coord[1]: {block.coord[0]: block}}
        self.terminal_block = block if isinstance(block, block_classes.machine_blocks.MachineTerminalBlock) else None
        self.rect = block.rect
        self.id = util.unique_id()
        self.size = 1

    def add_block(self, block):
        # make sure to check befoerhand
        if self.can_add(block.coord):
            if block.coord[1] in self.blocks:
                self.blocks[block.coord[1]][block.coord[0]] = block
            else:
                self.blocks[block.coord[1]] = {block.coord[0]: block}
            if isinstance(block, block_classes.machine_blocks.MachineTerminalBlock):
                if self.terminal_block is None:
                    self.terminal_block = block
                else:
                    block.interface = self.terminal_block.interface
            self.size += 1
        else:
            print("Warning: Can not add block to machine, not adjacent.")

    def remove_block(self, block):
        del self.blocks[block.coord[1]][block.coord[0]]

    def add_machine(self, machine):
        # it is assumed that machines are connected
        for y_dict in machine.blocks.values():
            for block in y_dict.values():
                # cannot just use the add method since the check might fail
                if block.coord[1] in self.blocks:
                    self.blocks[block.coord[1]][block.coord[0]] = block
                else:
                    self.blocks[block.coord[1]] = {block.coord[0]: block}

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

