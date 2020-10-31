import pygame
from random import choices, uniform

from utility.constants import BLOCK_SIZE
from utility.utilities import normalize
from board import materials
from board.blocks import Block

class Plant:

    DIRECTION_ADDITON = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    def __init__(self, start_block):
        self.material = start_block.material
        self.__matrix = [[start_block]]
        self.grow_block = start_block
        self.__grow_block_coord = [0, 0]

    def grow(self, surrounding_blocks):
        allowed_factor = [1 for _ in range(4)]
        for i, block in enumerate(surrounding_blocks):
            if block.name() != "Air":
                allowed_factor[i] = 0
        continuation_chance = [self.material.CONTINUATION_DIRECTION[i] * allowed_factor[i] for i in range(4)]
        #no place to grow
        if sum(continuation_chance) == 0:
            return None
        direction_chance = normalize(continuation_chance)
        dir = choices(range(4), direction_chance, k=1)[0]
        material_obj = getattr(materials, self.grow_block.name())
        extension_block = Block(self.grow_block.coord, material_obj(image_number=dir))

        #move the tip of the plant forward
        self.grow_block.rect.topleft = (self.grow_block.rect.left + BLOCK_SIZE.width * self.DIRECTION_ADDITON[dir][0],
                                        self.grow_block.rect.top + BLOCK_SIZE.height * self.DIRECTION_ADDITON[dir][1])
        self.__add_matrix(self.DIRECTION_ADDITON[dir], extension_block)
        return extension_block, self.grow_block

    def __add_matrix(self, direction, block):
        if direction[0] != 0:
            if self.__grow_block_coord[0] == 0 or self.__grow_block_coord[0] == len(self.__matrix[0]) - 1:
                for row in self.__matrix:
                    row.insert(self.__grow_block_coord[0], None)
        else:
            if self.__grow_block_coord[1] == 0 or self.__grow_block_coord[1] == len(self.__matrix) - 1:
                self.__matrix.insert(self.__grow_block_coord[1], [None for _ in range(len(self.__matrix[0]))])
        self.__matrix[self.__grow_block_coord[1]][self.__grow_block_coord[0]] = block
        self.__grow_block_coord = (max(0, self.__grow_block_coord[0] + direction[0]), max(0, self.__grow_block_coord[1] + direction[1]))
        self.__matrix[self.__grow_block_coord[1]][self.__grow_block_coord[0]] = self.grow_block

    def can_grow(self):
        return self.material.GROW_CHANCE > 0 and self.__size() < self.material.MAX_SIZE

    def __size(self):
        size = 0
        for row in self.__matrix:
            for b in row:
                if b != None:
                    size += 1
        return size