import pygame

import block_classes.environment_materials as environment_materials
import block_classes.materials as base_materials
import block_classes.block_utility as block_util
import utility.constants as con
import utility.utilities as util
import entities
from utility import inventories
import interfaces.interface_utility as interface_util
import board.pathfinding as pathfinding
import board.flora as flora


class Chunk(util.Serializer):

    def __init__(self, pos, foreground, background, main_sprite_group, first_time=False):
        # chunk with sizes in pixels lowest value should 0,0
        self.rect = pygame.Rect((*pos, *con.CHUNK_SIZE))

        self.plants = {}
        self.__matrix = self.__create_blocks_from_string(foreground)
        self.__back_matrix = self.__create_blocks_from_string(background)
        # changed, if it is the first time
        self.changed = [False, first_time]

        offset = [int(pos[0] / con.CHUNK_SIZE.width), int(pos[1] / con.CHUNK_SIZE.height)]
        foreground_image = BoardImage(self.rect.topleft, block_matrix = self.__matrix, layer = con.BOARD_LAYER, offset=offset)
        background_image = BoardImage(self.rect.topleft, block_matrix = self.__back_matrix, layer = con.BACKGROUND_LAYER, offset=offset)
        light_image = LightImage(self.rect.topleft, layer = con.LIGHT_LAYER, color=con.INVISIBLE_COLOR if con.DEBUG.NO_LIGHTING else (0, 0, 0, 255))
        selection_image = TransparantBoardImage(self.rect.topleft, layer = con.HIGHLIGHT_LAYER, color=con.INVISIBLE_COLOR)

        self.layers = [light_image, selection_image, foreground_image, background_image]
        self.pathfinding_chunk = pathfinding.PathfindingChunk(self.__matrix)
        main_sprite_group.add(foreground_image)
        main_sprite_group.add(background_image)
        main_sprite_group.add(light_image)
        main_sprite_group.add(selection_image)

    @property
    def coord(self):
        return int(self.rect.left / self.rect.width), int(self.rect.top / self.rect.height)

    def is_showing(self):
        return self.layers[2].is_showing()

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
        self.changed[0] = True
        local_rect = self.__local_adjusted_rect(rect)
        image = self.layers[layer]
        image.add_rect(local_rect, color, border)

    def add_blocks(self, *blocks):
        self.changed[0] = True
        for block in blocks:
            local_block_rect = self.__local_adjusted_rect(block.rect)
            self.add_rectangle(local_block_rect, con.INVISIBLE_COLOR, layer=1)
            self.add_rectangle(local_block_rect, con.INVISIBLE_COLOR, layer=2)

            #check if a new plant, if so make sure the start is unique
            if isinstance(block.material, environment_materials.MultiFloraMaterial) and block.id not in self.plants:
                plant = flora.Plant(block)
                self.plants[plant.id] = plant
                block.material.image_key = -1
            # add the block
            self.layers[2].add_image(local_block_rect, block.surface)

            column, row = self.__local_adusted_block_coordinate(block.rect.topleft)
            self.__matrix[row][column] = block
            self.pathfinding_chunk.added_rects.append(block.rect)

    def remove_blocks(self, *blocks):
        self.changed[0] = True
        removed_items = []
        for block in blocks:
            removed_items.append(inventories.Item(block.material))
            if hasattr(block, "inventory"):
                items = block.inventory.get_all_items(ignore_filter=True)
                removed_items.extend(items)
            local_block_rect = self.__local_adjusted_rect(block.rect)
            self.add_rectangle(local_block_rect, con.INVISIBLE_COLOR, layer=2)
            # remove the highlight
            self.add_rectangle(local_block_rect, con.INVISIBLE_COLOR, layer=1)
            column, row = self.__local_adusted_block_coordinate(block.rect.topleft)
            self.__matrix[row][column] = base_materials.Air().to_block(block.rect.topleft)
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
            raise util.GameException("Point: {} is not within chunk at {}".format(point, self.rect))

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
        row = interface_util.p_to_r(point[1]) - interface_util.p_to_r(self.rect.y)
        column = interface_util.p_to_c(point[0]) - interface_util.p_to_r(self.rect.x)
        return [column, row]

    def __local_adjusted_rect(self, rect):
        topleft = (rect.left % con.CHUNK_SIZE.width, rect.top % con.CHUNK_SIZE.height)
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
                pos = (self.rect.left + column_i * con.BLOCK_SIZE.width,
                       self.rect.top + row_i * con.BLOCK_SIZE.height,)
                material_instance = block_util.material_instance_from_string(s_matrix[row_i][column_i], depth=row_i)
                block = material_instance.to_block(pos)
                if isinstance(material_instance, environment_materials.MultiFloraMaterial):
                    plant = flora.Plant(block)
                    self.plants[plant.id] = plant
                s_matrix[row_i][column_i] = block
        return s_matrix


class StartChunk(Chunk):
    START_RECTANGLE = pygame.Rect((round((con.CHUNK_SIZE.width / 2 - (con.CHUNK_SIZE.width / 2) / 2) / 10) * 10,
                                   round((con.CHUNK_SIZE.height / 2 - (con.CHUNK_SIZE.height / 10) / 2) / 10) * 10,
                                   round((con.CHUNK_SIZE.width / 2) / 10) * 10,
                                   round((con.CHUNK_SIZE.height / 5) / 10) * 10))

    def __init__(self, pos, foreground, background, main_sprite_group, **kwargs):
        foreground = self.__adjust_foreground_string_matrix(foreground)
        super().__init__(pos, foreground, background, main_sprite_group, **kwargs)

    def __adjust_foreground_string_matrix(self, matrix):
        #generate the air space at the start position
        for row_i in range(interface_util.p_to_r(self.START_RECTANGLE.top), interface_util.p_to_r(self.START_RECTANGLE.bottom)):
            for column_i in range(interface_util.p_to_c(self.START_RECTANGLE.left), interface_util.p_to_c(self.START_RECTANGLE.right)):
                matrix[row_i][column_i] = "Air"
        return matrix


class BoardImage(entities.ZoomableEntity):
    """
    Convert a matrix of block_classes into a surface that persists as an entity. This
    is done to severly decrease the amount of blit calls and allow for layering
    of images aswell as easily scaling.
    """
    def __init__(self, pos, **kwargs):
        entities.ZoomableEntity.__init__(self, pos, con.CHUNK_SIZE, **kwargs)

    def _create_surface(self, size, color, **kwargs):
        """
        Overwrites the image creation process in the basic Entity class
        """
        block_matrix = kwargs["block_matrix"]
        offset = kwargs["offset"]
        image = pygame.Surface(size).convert()
        image.set_colorkey(con.INVISIBLE_COLOR, con.RLEACCEL)
        # make sure that surfaces that have alpha channels are blittet as transparant because the background
        # is transparant
        image.fill(con.INVISIBLE_COLOR)
        for row in block_matrix:
            for block in row:
                block_rect = (block.rect.left - offset[0] * con.CHUNK_SIZE.width, block.rect.top - offset[1] * con.CHUNK_SIZE.height, *block.rect.size)
                image.blit(block.surface, block_rect)
        return image

    def add_rect(self, rect, color, border):
        """
        Add a rectangle to the image, this can be a transparant rectangle to
        remove a part of the image or another rectangle

        :param rect: a pygame rect object
        """
        pygame.draw.rect(self.orig_surface, color, rect, border)
        zoomed_rect = pygame.Rect((round(rect.x * self._zoom), round(rect.y * self._zoom), round(rect.width * self._zoom), round(rect.height * self._zoom)))
        pygame.draw.rect(self.surface, color, zoomed_rect, border)

    def add_image(self, rect, image):
        """
        Add an image to the boardImage

        :param rect: location of the image as a pygame Rect object
        :param image: a pygame Surface object
        """
        self.orig_surface.blit(image, rect)
        zoomed_rect = pygame.Rect((round(rect.x * self._zoom),round(rect.y * self._zoom),round(rect.width * self._zoom),round(rect.height * self._zoom)))
        zoomed_image = pygame.transform.scale(image, (round(rect.width * self._zoom),round(rect.height * self._zoom)))
        self.surface.blit(zoomed_image, zoomed_rect)


class TransparantBoardImage(BoardImage):
    """
    Slight variation on the basic Board image that creates a transparant
    surface on which selections can be drawn
    """

    def _create_surface(self, size, color, **kwargs):
        """
        Overwrites the image creation process in the basic Entity class
        """
        image = pygame.Surface(size)
        image = image.convert_alpha()
        image.fill(color)
        return image


class LightImage(TransparantBoardImage):
    def __init__(self, pos,  **kwargs):
        super().__init__(pos, **kwargs)
        # first values can be determined when the first rectangle is added
        self.__left = con.BOARD_SIZE.width
        self.__top = con.BOARD_SIZE.height
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
