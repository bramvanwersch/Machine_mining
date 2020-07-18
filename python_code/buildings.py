from python_code.materials import TerminalMaterial
from python_code.image_handling import image_sheets
from python_code.constants import BLOCK_SIZE
from python_code.blocks import ContainerBlock

class Building:
    def __init__(self, pos, depth):
        self.pos = pos


class Terminal(Building):

    IMAGE_SPECIFICATIONS = ["buildings", (0, 0, 20, 20), {"color_key" : (255,255,255)}]
    def __init__(self, pos, depth):
        super().__init__(pos, depth)
        self.pos = pos
        images = image_sheets[self.IMAGE_SPECIFICATIONS[0]].images_at_rectangle(self.IMAGE_SPECIFICATIONS[1], **self.IMAGE_SPECIFICATIONS[2])
        self.blocks = self.__get_blocks(images, depth)

    def __get_blocks(self, images, depth):
        blocks = []
        for row_i, row in enumerate(images):
            block_row = []
            for column_i, image in enumerate(row):
                material = TerminalMaterial(depth, image = image)
                pos = (self.pos[0] + column_i * BLOCK_SIZE.width, self.pos[1] + row_i * BLOCK_SIZE.height)
                block_row.append(ContainerBlock(pos, BLOCK_SIZE, material))
            blocks.append(block_row)
        return blocks

