import pygame
from random import choices, choice, randint

from python_code.utility.constants import *
from python_code.utility.utilities import normalize, Gaussian
from python_code.board.blocks import *
from python_code.board import materials
from python_code.entities import ZoomableEntity, SelectionRectangle
from python_code.interfaces.interface_utility import p_to_c, p_to_r
from python_code.board.pathfinding import PathfindingChunk


class Chunk:
    BLOCK_PER_CLUSTER = 500
    #the max size of a ore cluster around the center
    MAX_CLUSTER_SIZE = 3

    def __init__(self, pos, main_sprite_group):
        #chunk with sizes in pixels lowest value should 0,0
        self.rect = pygame.Rect((*pos, *CHUNK_SIZE))
        string_matrix = self._generate_foreground_string_matrix()
        self.__matrix = self.__create_blocks_from_string(string_matrix)

        back_string_matrix = self._generate_background_string_matrix()
        self.__back_matrix = self.__create_blocks_from_string(back_string_matrix)

        offset = [int(pos[0] / CHUNK_SIZE.width), int(pos[1] / CHUNK_SIZE.height)]
        self.foreground_image = BoardImage(self.rect.topleft, main_sprite_group, block_matrix = self.__matrix, layer = BOARD_LAYER, offset=offset)
        self.background_image = BoardImage(self.rect.topleft, main_sprite_group, block_matrix = self.__back_matrix, layer = BACKGROUND_LAYER, offset=offset)
        self.selection_image = TransparantBoardImage(self.rect.topleft, main_sprite_group, layer = HIGHLIGHT_LAYER)
        self.pathfinding_chunk = PathfindingChunk(self.__matrix)

    @property
    def coord(self):
        return int(self.rect.left / self.rect.width), int(self.rect.top / self.rect.height)

    def add_rectangle(self, rect, color, layer=2, border=0):
        local_rect = self.__local_adjusted_rect(rect)
        if layer == 1:
            image = self.selection_image
        elif layer == 2:
            image = self.foreground_image
        elif layer == 3:
            image = self.background_image
        image.add_rect(local_rect, color, border)

    def add_blocks(self, *blocks):
        for block in blocks:
            local_block_rect = self.__local_adjusted_rect(block.rect)
            self.add_rectangle(local_block_rect, INVISIBLE_COLOR, layer=1)
            self.add_rectangle(local_block_rect, INVISIBLE_COLOR, layer=2)

            # add the block
            self.foreground_image.add_image(local_block_rect, block.surface)

            column, row = self.__local_adusted_block_coordinate(local_block_rect.topleft)
            self.__matrix[row][column] = block
            self.pathfinding_chunk.added_rects.append(block.rect)

    def remove_blocks(self, *blocks):
        for block in blocks:
            local_block_rect = self.__local_adjusted_rect(block.rect)
            self.add_rectangle(local_block_rect, INVISIBLE_COLOR, layer=2)
            # remove the highlight
            self.add_rectangle(local_block_rect, INVISIBLE_COLOR, layer=1)
            column, row = self.__local_adusted_block_coordinate(block.rect.topleft)
            self.__matrix[row][column] = AirBlock(block.rect.topleft, materials.Air())
            self.pathfinding_chunk.removed_rects.append(block.rect)

    def get_block(self, point):
        column, row = self.__local_adusted_block_coordinate(point)
        return self.__matrix[row][column]

    def overlapping_blocks(self, rect):
        column_start, row_start = self.__local_adusted_block_coordinate(rect.topleft)
        column_end, row_end = self.__local_adusted_block_coordinate(rect.bottomright)

        overlapping_blocks = []
        for row in self.__matrix[row_start : row_end + 1]:
            add_row = row[column_start : column_end + 1]
            if len(add_row) > 0:
                overlapping_blocks.append(add_row)
        return overlapping_blocks

    def _generate_background_string_matrix(self):
        """
        Generate the backdrop matrix.

        :return: a matrix of the given size
        """
        matrix = []
        for _ in range(p_to_r(BOARD_SIZE.height)):
            row = ["Dirt"] * p_to_c(BOARD_SIZE.width)
            matrix.append(row)
        return matrix

    def __local_adusted_block_coordinate(self, point):
        #get the coordinate of a block in the local self.matrix grid
        row = p_to_r(point[1]) - p_to_r(self.rect.y)
        column = p_to_c(point[0]) - p_to_r(self.rect.x)
        return [column, row]

    def __local_adjusted_rect(self, rect):
        topleft = (rect.left % CHUNK_SIZE.width, rect.top % CHUNK_SIZE.height)
        return pygame.Rect((*topleft, *rect.size))


##GENERATE CHUNK FUNCTIONS

    def _generate_foreground_string_matrix(self):
        """
        Fill a matrix with names of the materials of the respective blocks

        :return: a matrix containing strings corresponding to names of __material
        classes.
        """

        matrix = []
        #first make everything stone
        for _ in range(p_to_c(self.rect.height)):
            row = ["Stone"] * p_to_r(self.rect.width)
            matrix.append(row)

        #generate some ores inbetween the start and end locations
        for row_i, row in enumerate(matrix):
            for column_i, value in enumerate(row):
                if randint(1, self.BLOCK_PER_CLUSTER) == 1:
                    #decide the ore
                    ore = self.__get_ore_at_depth(row_i)
                    #create a list of locations around the current location
                    #where an ore is going to be located
                    ore_locations = self.__create_ore_cluster(ore, (column_i, row_i))
                    for loc in ore_locations:
                        try:
                            matrix[loc[1]][loc[0]] = ore
                        except IndexError:
                            #if outside board skip
                            continue
        return matrix

    def __get_ore_at_depth(self, depth):
        """
        Figure out the likelyood of all ores and return a wheighted randomly
        chosen ore

        :param depth: the depth for the ore to be at
        :return: a string that is an ore
        """
        likelyhoods = []
        for name in ORE_LIST:
            norm_depth = depth / MAX_DEPTH * 100
            mean = getattr(materials, name).MEAN_DEPTH
            sd = getattr(materials, name).SD
            lh = Gaussian(mean, sd).probability_density(norm_depth)
            likelyhoods.append(round(lh, 10))
        norm_likelyhoods = normalize(likelyhoods)

        return choices(ORE_LIST, norm_likelyhoods, k = 1)[0]

    def __create_ore_cluster(self, ore, center):
        """
        Generate a list of index offsets for a certain ore

        :param ore: string name of an ore
        :param center: a coordinate around which the ore cluster needs to be
        generated
        :return: a list of offset indexes around 0,0
        """
        size = randint(*getattr(materials, ore).CLUSTER_SIZE)
        ore_locations = []
        while len(ore_locations) <= size:
            location = [0,0]
            for index in range(2):
                pos = choice([-1, 1])
                #assert index is bigger then 0
                location[index] = max(0, pos * randint(0, self.MAX_CLUSTER_SIZE) + center[index])
            if location not in ore_locations:
                ore_locations.append(location)
        return ore_locations

    def __create_blocks_from_string(self, s_matrix):
        """
        Change strings into blocks

        :param s_matrix: a string matrix that contains strings corresponding to
        material classes
        :return: the s_matrix filled with block class instances
        """
        for row_i, row in enumerate(s_matrix):
            for column_i, value in enumerate(row):
                #create position
                pos = (self.rect.left + column_i * BLOCK_SIZE.width,
                       self.rect.top + row_i * BLOCK_SIZE.height,)
                material = getattr(materials, s_matrix[row_i][column_i])
                if issubclass(material, materials.ColorMaterial):
                    material_instance = material(depth=row_i)
                else:
                    material_instance = material()
                if material.name() == "Air":
                    block = AirBlock(pos, material_instance)
                else:
                    block = Block(pos, material_instance)
                s_matrix[row_i][column_i] = block
        return s_matrix


class StartChunk(Chunk):
    START_RECTANGLE = pygame.Rect((CHUNK_SIZE.width / 2 - 125, 0, 250, 50))

    def _generate_foreground_string_matrix(self):
        matrix = super()._generate_foreground_string_matrix()
        #generate the air space at the start position
        for row_i in range(p_to_r(self.START_RECTANGLE.bottom)):
            for column_i in range(p_to_c(self.START_RECTANGLE.left), p_to_r(self.START_RECTANGLE.right)):
                matrix[row_i][column_i] = "Air"
        return matrix


class BoardImage(ZoomableEntity):
    """
    Convert a matrix of blocks into a surface that persists as an entity. This
    is done to severly decrease the amount of blit calls and allow for layering
    of images aswell as easily scaling.
    """
    def __init__(self, pos, main_sprite_group, **kwargs):
        ZoomableEntity.__init__(self, pos, CHUNK_SIZE, main_sprite_group, **kwargs)
        self.visible = True

    def update(self, *args):
        pass

    def _create_image(self, size, color, **kwargs):
        """
        Overwrites the image creation process in the basic Entity class
        """
        block_matrix = kwargs["block_matrix"]
        offset = kwargs["offset"]
        image = pygame.Surface(size)
        image.set_colorkey((0,0,0), RLEACCEL)
        image = image.convert_alpha()
        for row in block_matrix:
            for block in row:
                if block != "Air":
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
    def __init__(self, pos, main_sprite_group, **kwargs):
        BoardImage.__init__(self, pos, main_sprite_group, **kwargs)

    def _create_image(self, size, color, **kwargs):
        """
        Overwrites the image creation process in the basic Entity class
        """
        image = pygame.Surface(size)
        image.set_colorkey((0,0,0), RLEACCEL)
        image = image.convert_alpha()
        image.fill(INVISIBLE_COLOR)
        return image

    def add_building_rectangle(self, pos, size=(10, 10)):
        mouse_pos = screen_to_board_coordinate(pos, self.groups()[0].target, self._zoom)
        self.selection_rectangle = ZoomableEntity(mouse_pos, size - BLOCK_SIZE,
                                        self.groups()[0],zoom=self._zoom, color=INVISIBLE_COLOR)



