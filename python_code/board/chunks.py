import block_classes.flora_materials
from utility.constants import *
from utility.utilities import GameException, Serializer
from block_classes.blocks import *
from block_classes import materials, block_utility
from entities import ZoomableEntity
from interfaces.interface_utility import p_to_c, p_to_r
from board.pathfinding import PathfindingChunk
from board.flora import Plant
from inventories import Item


class Chunk(Serializer):

    def __init__(self, pos, foreground, background, main_sprite_group):
        #chunk with sizes in pixels lowest value should 0,0
        self.rect = pygame.Rect((*pos, *CHUNK_SIZE))

        self.plants = {}
        self.__matrix = self.__create_blocks_from_string(foreground)
        self.__back_matrix = self.__create_blocks_from_string(background)

        offset = [int(pos[0] / CHUNK_SIZE.width), int(pos[1] / CHUNK_SIZE.height)]
        foreground_image = BoardImage(self.rect.topleft, main_sprite_group, block_matrix = self.__matrix, layer = BOARD_LAYER, offset=offset)
        background_image = BoardImage(self.rect.topleft, main_sprite_group, block_matrix = self.__back_matrix, layer = BACKGROUND_LAYER, offset=offset)
        light_image = LightImage(self.rect.topleft, main_sprite_group, layer = LIGHT_LAYER, color=(0, 0, 0, 255))
        selection_image = TransparantBoardImage(self.rect.topleft, main_sprite_group, layer = HIGHLIGHT_LAYER, color=INVISIBLE_COLOR)

        self.layers = [light_image, selection_image, foreground_image, background_image]
        self.pathfinding_chunk = PathfindingChunk(self.__matrix)

    @property
    def coord(self):
        return int(self.rect.left / self.rect.width), int(self.rect.top / self.rect.height)

    def to_dict(self):
        return {
            "pos": self.rect.topleft,
            "foreground": [block.name() for row in self.__matrix for block in row],
            "backgrounc": [block.name() for row in self.__back_matrix for block in row]
        }

    @classmethod
    def from_dict(cls, sprite_group=None, **arguments):
        super().from_dict(main_sprite_group=sprite_group, **arguments)

    def add_rectangle(self, rect, color, layer=2, border=0):

        local_rect = self.__local_adjusted_rect(rect)
        image = self.layers[layer]
        image.add_rect(local_rect, color, border)

    def add_blocks(self, *blocks):

        for block in blocks:
            local_block_rect = self.__local_adjusted_rect(block.rect)
            self.add_rectangle(local_block_rect, INVISIBLE_COLOR, layer=1)
            self.add_rectangle(local_block_rect, INVISIBLE_COLOR, layer=2)

            #check if a new plant, if so make sure the start is unique
            if isinstance(block.material, block_classes.flora_materials.MultiFloraMaterial) and block.id not in self.plants:
                plant = Plant(block)
                self.plants[plant.id] = plant
                block.material.image_key = -1
            # add the block
            self.layers[2].add_image(local_block_rect, block.surface)

            column, row = self.__local_adusted_block_coordinate(block.rect.topleft)
            self.__matrix[row][column] = block
            self.pathfinding_chunk.added_rects.append(block.rect)

    def remove_blocks(self, *blocks):

        removed_items = []
        for block in blocks:
            removed_items.append(Item(block.material))
            if hasattr(block, "inventory"):
                items = block.inventory.get_all_items(ignore_filter=True)
                removed_items.extend(items)
            local_block_rect = self.__local_adjusted_rect(block.rect)
            self.add_rectangle(local_block_rect, INVISIBLE_COLOR, layer=2)
            # remove the highlight
            self.add_rectangle(local_block_rect, INVISIBLE_COLOR, layer=1)
            column, row = self.__local_adusted_block_coordinate(block.rect.topleft)
            self.__matrix[row][column] = AirBlock(block.rect.topleft, materials.Air())
            self.pathfinding_chunk.removed_rects.append(block.rect)
        return removed_items

    def update_blocks(self, *blocks):
        for block in blocks:
            self.pathfinding_chunk.added_rects.append(block.rect)

    def get_block(self, point):
        column, row = self.__local_adusted_block_coordinate(point)
        try:
            return self.__matrix[row][column]
        except IndexError:
            raise GameException("Point: {} is not within chunk at {}".format(point, self.rect))

    def overlapping_blocks(self, rect):
        column_start, row_start = self.__local_adusted_block_coordinate(rect.topleft)
        column_end, row_end = self.__local_adusted_block_coordinate(rect.bottomright)

        overlapping_blocks = []
        for row in self.__matrix[row_start : row_end + 1]:
            add_row = row[column_start : column_end + 1]
            if len(add_row) > 0:
                overlapping_blocks.append(add_row)
        return overlapping_blocks

    def __local_adusted_block_coordinate(self, point):
        #get the coordinate of a block in the local self.matrix grid
        row = p_to_r(point[1]) - p_to_r(self.rect.y)
        column = p_to_c(point[0]) - p_to_r(self.rect.x)
        return [column, row]

    def __local_adjusted_rect(self, rect):
        topleft = (rect.left % CHUNK_SIZE.width, rect.top % CHUNK_SIZE.height)
        return pygame.Rect((*topleft, *rect.size))

##GENERATE CHUNK FUNCTIONS
    def __create_blocks_from_string(self, s_matrix):
        """
        Change strings into block_classes

        :param s_matrix: a string matrix that contains strings corresponding to
        material classes
        :return: the s_matrix filled with block class instances
        """
        for row_i, row in enumerate(s_matrix):
            for column_i, value in enumerate(row):
                #create position
                pos = (self.rect.left + column_i * BLOCK_SIZE.width,
                       self.rect.top + row_i * BLOCK_SIZE.height,)
                material_instance = block_utility.material_instance_from_string(s_matrix[row_i][column_i], depth=row_i)
                block = material_instance.to_block(pos)
                if isinstance(material_instance, block_classes.flora_materials.MultiFloraMaterial):
                    plant = Plant(block)
                    self.plants[plant.id] = plant
                s_matrix[row_i][column_i] = block
        return s_matrix


class StartChunk(Chunk):
    START_RECTANGLE = pygame.Rect((CHUNK_SIZE.width / 2 - (CHUNK_SIZE.width / 2) / 2,
                                   CHUNK_SIZE.height / 2 - (CHUNK_SIZE.height / 10) / 2,
                                   CHUNK_SIZE.width / 2,  CHUNK_SIZE.height / 10))

    def __init__(self, pos, foreground, background, main_sprite_group):
        foreground = self.__adjust_foreground_string_matrix(foreground)
        super().__init__(pos, foreground, background, main_sprite_group)

    def __adjust_foreground_string_matrix(self, matrix):
        #generate the air space at the start position
        for row_i in range(p_to_r(self.START_RECTANGLE.top), p_to_r(self.START_RECTANGLE.bottom)):
            for column_i in range(p_to_c(self.START_RECTANGLE.left), p_to_c(self.START_RECTANGLE.right)):
                matrix[row_i][column_i] = "Air"
        return matrix


class BoardImage(ZoomableEntity):
    """
    Convert a matrix of block_classes into a surface that persists as an entity. This
    is done to severly decrease the amount of blit calls and allow for layering
    of images aswell as easily scaling.
    """
    def __init__(self, pos, main_sprite_group, **kwargs):
        ZoomableEntity.__init__(self, pos, CHUNK_SIZE, main_sprite_group, **kwargs)

    def _create_image(self, size, color, **kwargs):
        """
        Overwrites the image creation process in the basic Entity class
        """
        block_matrix = kwargs["block_matrix"]
        offset = kwargs["offset"]
        image = pygame.Surface(size)
        image.set_colorkey(INVISIBLE_COLOR, RLEACCEL)
        image = image.convert()
        for row in block_matrix:
            for block in row:
                block_rect = (block.rect.left - offset[0] * CHUNK_SIZE.width, block.rect.top - offset[1] * CHUNK_SIZE.height,*block.rect.size)
                image.blit(block.surface, block_rect)
        return image

    def add_rect(self, rect, color, border):
        """
        Add a rectangle to the image, this can be a transparant rectangle to
        remove a part of the image or another rectangle

        :param rect: a pygame rect object
        """
        pygame.draw.rect(self.orig_image, color, rect, border)
        zoomed_rect = pygame.Rect((round(rect.x * self._zoom), round(rect.y * self._zoom), round(rect.width * self._zoom), round(rect.height * self._zoom)))
        pygame.draw.rect(self.image, color, zoomed_rect, border)

    def add_image(self, rect, image):
        """
        Add an image to the boardImage

        :param rect: location of the image as a pygame Rect object
        :param image: a pygame Surface object
        """
        self.orig_image.blit(image, rect)
        zoomed_rect = pygame.Rect((round(rect.x * self._zoom),round(rect.y * self._zoom),round(rect.width * self._zoom),round(rect.height * self._zoom)))
        zoomed_image = pygame.transform.scale(image, (round(rect.width * self._zoom),round(rect.height * self._zoom)))
        self.image.blit(zoomed_image, zoomed_rect)


class TransparantBoardImage(BoardImage):
    """
    Slight variation on the basic Board image that creates a transparant
    surface on which selections can be drawn
    """

    def _create_image(self, size, color, **kwargs):
        """
        Overwrites the image creation process in the basic Entity class
        """
        image = pygame.Surface(size)
        image = image.convert_alpha()
        image.fill(color)
        return image


class LightImage(TransparantBoardImage):
    def __init__(self, pos, main_sprite_group, **kwargs):
        super().__init__(pos, main_sprite_group, **kwargs)
        # first values can be determined when the first rectangle is added
        self.__left = BOARD_SIZE.width
        self.__top = BOARD_SIZE.height
        self.__right = 0
        self.__bottom = 0
        self.__updated = False

    def get_update_rect(self):
        if self.__left < self.__right:
            return pygame.Rect((self.__left, self.__top, self.__right - self.__left, self.__bottom - self.__top))
        return None

    def add_rect(self, rect, color, border):
        super().add_rect(rect, color, border)
        rect.top += self.orig_rect.top
        rect.left += self.orig_rect.left

        if rect.left < self.__left:
            self.__left = rect.left
        if rect.top < self.__top:
            self.__top = rect.top
        if rect.right > self.__right:
            self.__right = rect.right
        if rect.bottom > self.__bottom:
            self.__bottom = rect.bottom
