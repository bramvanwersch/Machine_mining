from utility.constants import BLOCK_SIZE
from block_classes import flora_materials
from block_classes.blocks import Block

class Plant:

    DIRECTION_ADDITON = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    ID = 0
    def __init__(self, start_block):
        self.id = "Plant{}".format(self.ID)
        Plant.ID += 1
        self.material = start_block.material
        self.__blocks = [start_block]
        self.grow_block.id = self.id

    def grow(self, surrounding_blocks):
        dir = self.material.CONTINUATION_DIRECTION
        if surrounding_blocks[dir] != "Air":
            return None
        material_obj = getattr(flora_materials, self.grow_block.name())
        extension_block = Block(self.grow_block.coord, material_obj(image_number=dir), id=self.id)

        #move the tip of the plant forward
        self.grow_block.rect.topleft = (self.grow_block.rect.left + BLOCK_SIZE.width * self.DIRECTION_ADDITON[dir][0],
                                        self.grow_block.rect.top + BLOCK_SIZE.height * self.DIRECTION_ADDITON[dir][1])
        self.__blocks.insert(len(self.__blocks) -1, extension_block)
        return extension_block, self.grow_block

    def can_grow(self):
        return self.material.GROW_CHANCE > 0 and self._size() < self.material.MAX_SIZE

    def remove_block(self, block):
        index = 0
        for i, p_block in enumerate(self.__blocks):
            if p_block.coord == block.coord:
                index = i
                break
        remove_blocks = self.__blocks[index:]
        self.__blocks = self.__blocks[:index]

        return remove_blocks

    @property
    def grow_block(self):
        return self.__blocks[-1]

    @property
    def base_block(self):
        #the block that connects the plant to the ground
        return self.__blocks[0]

    def _size(self):
        return len(self.__blocks)