import pygame
from typing import Tuple, List, Union
from abc import ABC

import block_classes.materials.environment_materials as environment_materials
import block_classes.materials.materials as base_materials
import block_classes.block_utility as block_util
import utility.constants as con
import utility.utilities as util
import entities
import interfaces.windows.interface_utility as interface_util
import board.pathfinding as pathfinding
import board.flora as flora
from utility import loading_saving
from block_classes.blocks import Block


class Chunk(loading_saving.Savable, loading_saving.Loadable):
    def __init__(self, pos, foreground, background, main_sprite_group, plants, changed=(False, False)):
        self.rect = pygame.Rect((pos[0], pos[1], con.CHUNK_SIZE.width, con.CHUNK_SIZE.height))
        self.id = util.unique_id()

        self.all_plants = plants
        # blocks are added here that the board has to place because they can go across chunk borders or rely on a
        # network or something else that is ultamately managed by the board. The attribute is deleted after it is
        # requested
        self.__board_update_blocks = []
        self.__matrix = self.__create_blocks_from_string(foreground)
        self.__back_matrix = self.__create_blocks_from_string(background)
        # changed, if it is the first time --> tracking for loading purposes of new chunks
        self.changed = list(changed)

        offset = [int(pos[0] / con.CHUNK_SIZE.width), int(pos[1] / con.CHUNK_SIZE.height)]
        foreground_image = BoardImage(self.rect.topleft, block_matrix=self.__matrix, layer=con.BOARD_LAYER,
                                      offset=offset)
        background_image = BoardImage(self.rect.topleft, block_matrix=self.__back_matrix, layer=con.BACKGROUND_LAYER,
                                      offset=offset)
        light_image = LightImage(self.rect.topleft, layer=con.LIGHT_LAYER,
                                 color=con.INVISIBLE_COLOR if con.DEBUG.NO_LIGHTING else (0, 0, 0, 255))
        selection_image = TransparantBoardImage(self.rect.topleft, layer=con.HIGHLIGHT_LAYER, color=con.INVISIBLE_COLOR)

        self.layers = [light_image, selection_image, foreground_image, background_image]
        self.pathfinding_chunk = pathfinding.PathfindingChunk(self.__matrix)
        main_sprite_group.add(foreground_image)
        main_sprite_group.add(background_image)
        main_sprite_group.add(light_image)
        main_sprite_group.add(selection_image)

    def __init_load__(self, pos=None, plants=None, front_matrix=None, back_matrix=None, main_sprite_group=None,
                      changed=None, id_=None):
        self.rect = pygame.Rect((pos[0], pos[1], con.CHUNK_SIZE.width, con.CHUNK_SIZE.height))

        self.id = id_
        self.all_plants = plants
        # blocks are added here that the board has to place because they can go across chunk borders or rely on a
        # network or something else that is ultamately managed by the board. The attribute is deleted after it is
        # requested
        self.__board_update_blocks = []
        self.__matrix = self.__create_blocks_from_string(front_matrix)
        self.__back_matrix = self.__create_blocks_from_string(back_matrix)
        # changed, if it is the first time --> tracking for loading purposes of new chunks
        self.changed = changed

        offset = [int(pos[0] / con.CHUNK_SIZE.width), int(pos[1] / con.CHUNK_SIZE.height)]
        foreground_image = BoardImage(self.rect.topleft, block_matrix=self.__matrix, layer=con.BOARD_LAYER,
                                      offset=offset)
        background_image = BoardImage(self.rect.topleft, block_matrix=self.__back_matrix, layer=con.BACKGROUND_LAYER,
                                      offset=offset)
        light_image = LightImage(self.rect.topleft, layer=con.LIGHT_LAYER,
                                 color=con.INVISIBLE_COLOR if con.DEBUG.NO_LIGHTING else (0, 0, 0, 255))
        selection_image = TransparantBoardImage(self.rect.topleft, layer=con.HIGHLIGHT_LAYER, color=con.INVISIBLE_COLOR)

        self.layers = [light_image, selection_image, foreground_image, background_image]
        self.pathfinding_chunk = pathfinding.PathfindingChunk(self.__matrix)
        main_sprite_group.add(foreground_image)
        main_sprite_group.add(background_image)
        main_sprite_group.add(light_image)
        main_sprite_group.add(selection_image)

    def to_dict(self):
        return {
            "pos": self.rect.topleft,
            "matrix": [[block.to_dict() for block in row] for row in self.__matrix],
            "back_matrix": [[block.to_dict() for block in row] for row in self.__back_matrix],
            "changed": self.changed,
            "id": self.id
        }

    @classmethod
    def from_dict(cls, dct, sprite_group=None, plants=None):
        # create matrices of MCD's that can then in turn be made into images
        matrix = [[Block.from_dict(d) for d in row] for row in dct["matrix"]]
        back_matrix = [[Block.from_dict(d) for d in row] for row in dct["back_matrix"]]
        return cls.load(pos=dct["pos"], plants=plants, front_matrix=matrix, back_matrix=back_matrix,
                        changed=dct["changed"], main_sprite_group=sprite_group, id_=dct["id"])

    @property
    def coord(self):
        return int(self.rect.left / self.rect.width), int(self.rect.top / self.rect.height)

    def is_showing(self) -> bool:
        return self.layers[2].is_showing()

    def is_loaded(self) -> bool:
        # TODO make this respond to the location of workers and the player
        return self.changed[1]

    def add_rectangle(self, rect, color, layer=2, border=0, trigger_change=True):
        self.changed[0] = trigger_change
        local_rect = self.__local_adjusted_rect(rect)
        image = self.layers[layer]
        image.add_rect(local_rect, color, border)

    def add_blocks(self, *blocks):
        for block in blocks:
            local_block_rect = self.__local_adjusted_rect(block.rect)
            self.add_rectangle(local_block_rect, con.INVISIBLE_COLOR, layer=1, trigger_change=False)
            self.add_rectangle(local_block_rect, con.INVISIBLE_COLOR, layer=2, trigger_change=False)

            # dont update for growing plants
            if isinstance(block.material, environment_materials.MultiFloraMaterial):
                # check if a new plant, if so make sure the start is unique also
                if block not in self.all_plants:
                    plant = flora.Plant(block, self.id)
                    self.all_plants.add(plant)
                    block.material.image_key = -1
            # add the block
            self.layers[2].add_image(local_block_rect, block.surface)

            column, row = self.__local_adusted_block_coordinate(block.rect.topleft)
            self.__matrix[row][column].set_block(block)
            self.pathfinding_chunk.added_rects.append(block.rect)

    def remove_blocks(self, *blocks):
        removed_items = []
        for block in blocks:
            removed_items.extend(block.destroy())
            local_block_rect = self.__local_adjusted_rect(block.rect)
            self.add_rectangle(local_block_rect, con.INVISIBLE_COLOR, layer=2, trigger_change=False)
            # remove the highlight
            self.add_rectangle(local_block_rect, con.INVISIBLE_COLOR, layer=1, trigger_change=False)
            column, row = self.__local_adusted_block_coordinate(block.rect.topleft)
            self.__matrix[row][column].set_block(base_materials.Air().to_block(block.rect.topleft))
            self.pathfinding_chunk.removed_rects.append(block.rect)
        return removed_items

    def update_blocks(self, *blocks):
        for block in blocks:
            self.pathfinding_chunk.added_rects.append(block.rect)

    def get_block(self, point) -> util.BlockPointer:
        column, row = self.__local_adusted_block_coordinate(point)
        try:
            return self.__matrix[row][column]
        except IndexError:
            raise util.GameException("Point: {} is not within chunk at {}".format(point, self.rect))

    def overlapping_blocks(
        self,
        rect: pygame.Rect
    ) -> List[util.BlockPointer]:
        column_start, row_start = self.__local_adusted_block_coordinate(rect.topleft)
        column_end, row_end = self.__local_adusted_block_coordinate(rect.bottomright)
        overlapping_blocks = []
        for row in self.__matrix[row_start: row_end + 1]:
            add_row = row[column_start: column_end + 1]
            if len(add_row) > 0:
                overlapping_blocks.append(add_row)
        return overlapping_blocks

    def __local_adusted_block_coordinate(self, point):
        # get the coordinate of a block in the local self.matrix grid
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
                # create position
                pos = (self.rect.left + column_i * con.BLOCK_SIZE.width,
                       self.rect.top + row_i * con.BLOCK_SIZE.height)
                material_class_definition = s_matrix[row_i][column_i]
                material_instance = material_class_definition.to_instance(depth=row_i)
                block = material_instance.to_block(pos, **material_class_definition.block_kwargs)
                if material_class_definition.needs_board_update or block.light_level > 0:
                    self.__board_update_blocks.append(block)
                if isinstance(material_instance, environment_materials.MultiFloraMaterial):
                    plant = flora.Plant(block, self.id)
                    self.all_plants.add(plant)
                s_matrix[row_i][column_i] = util.BlockPointer(block)

        return s_matrix

    def get_board_update_blocks(self):
        try:
            update_blocks = self.__board_update_blocks
        except AttributeError:
            if con.DEBUG.WARNINGS:
                print("Warning: get_board_update_blocks method was called a second time. "
                      "This method should be called once per chunk right after instantiation")
            return []
        del self.__board_update_blocks
        return update_blocks


class StartChunk(Chunk):
    START_RECTANGLE = pygame.Rect((round((con.CHUNK_SIZE.width / 2 - (con.CHUNK_SIZE.width / 2) / 2) / 10) * 10,
                                   round((con.CHUNK_SIZE.height / 2 - (con.CHUNK_SIZE.height / 10) / 2) / 10) * 10,
                                   round((con.CHUNK_SIZE.width / 2) / 10) * 10,
                                   round((con.CHUNK_SIZE.height / 5) / 10) * 10))

    def __init__(self, pos, foreground, background, main_sprite_group, all_plants, **kwargs):
        foreground = self.__adjust_foreground_string_matrix(foreground)
        super().__init__(pos, foreground, background, main_sprite_group, all_plants, **kwargs)

    def __adjust_foreground_string_matrix(self, matrix):
        # generate the air space at the start position
        for row_i in range(interface_util.p_to_r(self.START_RECTANGLE.top), interface_util.p_to_r(self.START_RECTANGLE.bottom)):
            for column_i in range(interface_util.p_to_c(self.START_RECTANGLE.left), interface_util.p_to_c(self.START_RECTANGLE.right)):
                matrix[row_i][column_i] = block_util.MCD("Air")
        return matrix


class BaseBoardImage(entities.ZoomableSprite, ABC):
    def __init__(
        self,
        pos: Union[List[int], Tuple[int, int]],
        **kwargs
    ):
        super().__init__(pos, con.CHUNK_SIZE, **kwargs)

    def add_rect(
        self,
        rect: Union[pygame.Rect, List[int], Tuple[int, int, int, int]],
        color: Union[List[int], Tuple[int, int, int], Tuple[int, int, int, int]],
        border: bool
    ):
        """Add a rectangle to the this image. This can be transparant to remove rectangles"""
        pygame.draw.rect(self.orig_surface, color, rect, border)
        zoomed_rect = pygame.Rect((round(rect.x * self._zoom), round(rect.y * self._zoom),
                                   round(rect.width * self._zoom), round(rect.height * self._zoom)))
        pygame.draw.rect(self.surface, color, zoomed_rect, border)

    def add_image(
        self,
        rect: Union[pygame.Rect, List[int], Tuple[int, int, int, int]],
        image: pygame.Surface
    ):
        """Blit an image on this image at a given rectangle while taking zoomed varaibles into account"""
        self.orig_surface.blit(image, rect)
        zoomed_rect = pygame.Rect((round(rect.x * self._zoom),round(rect.y * self._zoom),
                                   round(rect.width * self._zoom),round(rect.height * self._zoom)))
        zoomed_image = pygame.transform.scale(image, (round(rect.width * self._zoom),round(rect.height * self._zoom)))
        self.surface.blit(zoomed_image, zoomed_rect)


class BoardImage(BaseBoardImage):
    """
    Convert a matrix of block_classes into a surface that persists as an entity. This
    is done to severly decrease the amount of blit calls and allow for layering
    of images aswell as easily scaling.
    """
    def __init__(
        self,
        pos: Union[List[int], Tuple[int, int]],
        offset: Union[List[int], Tuple[int, int]],
        block_matrix: List[List["Block"]],
        **kwargs
    ):
        self.__offset = offset
        self.__block_matrix = block_matrix
        super().__init__(pos, **kwargs)

    def _create_surface(
        self,
        size: Union[util.Size, List[int], Tuple[int, int]],
        color: Union[List[int], Tuple[int, int, int], Tuple[int, int, int, int]],
    ):
        """
        Overwrites the image creation process in the basic Entity class
        """
        image = pygame.Surface(size).convert_alpha()
        # make sure that surfaces that have alpha channels are blittet as transparant because the background
        # is transparant
        image.fill(con.INVISIBLE_COLOR)
        for row in self.__block_matrix:
            for block in row:
                block_rect = (block.rect.left - self.__offset[0] * con.CHUNK_SIZE.width,
                              block.rect.top - self.__offset[1] * con.CHUNK_SIZE.height, *block.rect.size)
                image.blit(block.surface, block_rect)
        return image


class TransparantBoardImage(BaseBoardImage):
    """
    Slight variation on the basic Board image that creates a transparant
    surface on which selections can be drawn
    """

    def _create_surface(self, size, color):
        """
        Overwrites the image creation process in the basic Entity class
        """
        image = pygame.Surface(size)
        image = image.convert_alpha()
        image.fill(color)
        return image


class LightImage(TransparantBoardImage):
    def __init__(
        self,
        pos: Union[List[int], Tuple[int, int]],
        **kwargs
    ):
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
