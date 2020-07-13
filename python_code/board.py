from random import randint, choices, choice

from python_code.entities import Entity
from python_code.utilities import *
from python_code import materials
from python_code.constants import *
from python_code.pathfinding import PathFinder
from python_code.blocks import AirBlock, Block

class Board:
    """
    Class that holds a matrix of blocks that is a playing field and an image
    representing set matrix
    """
    START_RECTANGLE = pygame.Rect((BOARD_SIZE.width / 2 - 125, 0, 250, 50))
    BLOCK_PER_CLUSRTER = 500
    #the max size of a ore cluster around the center
    MAX_CLUSTER_SIZE = 3
    def __init__(self, main_sprite_group):
        self.matrix = self.__generate_foreground_matrix()
        self.back_matrix = self.__generate_background_matrix()
        self.foreground_image = BoardImage(main_sprite_group,
                                           block_matrix = self.matrix, layer = BOTTOM_LAYER)
        self.background_image = BoardImage(main_sprite_group,
                                           block_matrix = self.back_matrix, layer = BOTTOM_LAYER - 1)
        self.selection_image = TransparantBoardImage(main_sprite_group, layer = BOTTOM_LAYER + 1)
        self.pf = PathFinder(self.matrix)

    def overlapping_blocks(self, rect):
        """
        Get a list of all overlapping blocks with a certain rectangle. The list
        is ordered from low to high x then y.

        :param rect: pygame Rect object that tells where the overlap is desired
        :return: a sub matrix of overlapping blocks
        """
        #make sure that blocks that are just selected are not included
        row_start = self.__p_to_r(rect.top)
        row_end = self.__p_to_r(rect.bottom )
        column_start = self.__p_to_c(rect.left)
        column_end = self.__p_to_c(rect.right)
        overlapping_blocks = []
        for row in self.matrix[row_start : row_end + 1]:
            add_row = row[column_start : column_end + 1]
            if len(add_row) > 0:
                overlapping_blocks.append(add_row)
        return overlapping_blocks

    def surrounding_blocks(self, block):
        """
        Calculate the surrounding blocks of a certain block in the order
        NESW and None if there is no block (edge of the playing field).

        :param block: the center Block Object for the surrounding blocks
        :param matrix: the matrix that contains the surrounding blocks
        :return: 4 Block or None objects
        """
        row = self.__p_to_r(block.rect.y)
        column = self.__p_to_c(block.rect.x)
        blocks = [None, None, None, None]
        for index, new_position in enumerate([(0, -1), (1, 0), (0, 1), (-1, 0)]):
            matrix_position = (column + new_position[0], row + new_position[1])

            # Make sure within range
            if matrix_position[0] > (len(self.matrix[0]) - 1) or \
                    matrix_position[0] < 0 or \
                    matrix_position[1] > (len(self.matrix) - 1) or \
                    matrix_position[1] < 0:
                continue
            blocks[index] = self.matrix[matrix_position[1]][matrix_position[0]]
        return blocks

    def remove_blocks(self, blocks):
        """
        Remove a matrix of bloxks from the second board layer by replacing them
        with air

        :param blocks: a matrix of blocks
        """
        rect = rect_from_block_matrix(blocks)
        self.add_rectangle(INVISIBLE_COLOR, rect, layer=2)
        # remove the highlight
        self.add_rectangle(INVISIBLE_COLOR, rect, layer=1)
        for row in blocks:
            for block in row:
                row = self.__p_to_r(block.rect.y)
                column = self.__p_to_c(block.rect.x)
                self.matrix[row][column] = AirBlock(block.rect.topleft, block.rect.size)

    def highlight_non_air_blocks(self, color, blocks):
        """
        Highlight in a given area all the non air blocks

        :param color: The highlight color
        :param blocks: a matrix of blocks
        """
        rect = rect_from_block_matrix(blocks)
        self.add_rectangle(color, rect, layer = 1)
        air_spaces = self.get_air_rectangles(blocks)
        for air_rect in air_spaces:
            self.add_rectangle(INVISIBLE_COLOR, air_rect, layer = 1)

    def get_air_rectangles(self, blocks):
        """
        Get all air spaces in the given matrix of blocks as a collection of
        rectangles

        :param blocks: a matrix of blocks
        :return: a list of rectangles
        """
        air_rectangles = []
        covered_coordinates = []
        for n_row, row in enumerate(blocks):
            for n_col, block in enumerate(row):
                if block != "Air" or (n_col, n_row) in covered_coordinates:
                    continue
                sub_matrix = [sub_row[n_col:] for sub_row in blocks[n_row:]]
                lm_coord = self.__find_air_rectangle(sub_matrix)
                # add covered coordinates
                for x in range(lm_coord[0]+ 1):
                    for y in range(lm_coord[1] + 1):
                        covered_coordinates.append((n_col + x, n_row + y))
                # add the air rectangle
                air_matrix = [sub_row[n_col:n_col + lm_coord[0] + 1] for sub_row in blocks[n_row:n_row + lm_coord[1] + 1]]
                rect = rect_from_block_matrix(air_matrix)
                air_rectangles.append(rect)
        return air_rectangles

    def __find_air_rectangle(self, blocks):
        """
        Find starting from an air block all the air blocks in a rectangle

        :param blocks: a selection of blocks in a matrix
        :return: the matrix coordinate of the local blocks matrix in form
        (column, row) where the air square ends
        """
        #first find how far the column is filled cannot fill on 0 since 0 is guaranteed to be a air block
        x_size = 0
        for block in blocks[0][1:]:
            if block != "Air":
                break
            x_size += 1
        matrix_coordinate = [x_size, 0]

        #skip the first row since this was checked already
        for n_row, row in enumerate(blocks[1:]):
            for n_col, block in enumerate(row[:x_size + 1]):
                if block != "Air":
                    break
            if block != "Air":
                break
            matrix_coordinate[1] += 1
        return matrix_coordinate

    def add_rectangle(self, color, rect, layer = 2):
        """
        Add a rectangle on to one of the layers.

        :param color: the color of the rectangle. Use INVISIBLE_COLOR to make
        rectangles dissapear
        :param layer: an integer that between 1 and 3 that tells at what layer
        the rectangle should be added

        This can be used to remove parts of the image or add something to it
        """
        if layer == 1:
            image = self.selection_image
        elif layer == 2:
            image = self.foreground_image
        elif layer == 3:
            image = self.background_image
        image.add_rect(rect, color)

    def __getitem__(self, item):
        return self.matrix[item]

    def __p_to_r(self, value):
        """
        Point to row conversion. Convert a coordinate into a row number

        :param value: a coordinate
        :return: the corresponding row number
        """
        return int(value / BLOCK_SIZE.height)

    def __p_to_c(self, value):
        """
        Point to column conversion. Convert a coordinate into a column number

        :param value: a coordinate
        :return: the corresponding column number
        """
        return int(value / BLOCK_SIZE.width)

#### MAP GENERATION FUNCTIONS ###

    def __generate_foreground_matrix(self):
        """
        Fill a matrix with names of the materials of the respective blocks

        :return: a matrix containing strings corresponding to names of material
        classes.
        """

        matrix = []
        #first make everything stone
        for _ in range(self.__p_to_r(BOARD_SIZE.height)):
            row = ["Stone"] * self.__p_to_c(BOARD_SIZE.width)
            matrix.append(row)

        #generate some ores inbetween the start and end locations
        for row_i, row in enumerate(matrix):
            for column_i, value in enumerate(row):
                if randint(1, self.BLOCK_PER_CLUSRTER) == 1:
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
        #generate the air space at the start position
        for row_i in range(self.__p_to_r(self.START_RECTANGLE.bottom)):
            for column_i in range(self.__p_to_c(self.START_RECTANGLE.left),
                                  self.__p_to_c(self.START_RECTANGLE.right)):
                matrix[row_i][column_i] = "Air"
        #generate pre made buildings
        matrix[self.__p_to_c(40)][self.__p_to_r(BOARD_SIZE[1] / 2 + 50)] = "Terminal"
        matrix = self.__create_blocks_from_string(matrix)
        return matrix

    def __generate_background_matrix(self):
        """
        Generate the backdrop matrix.

        :return: a matrix of the given size
        """
        matrix = []
        for _ in range(self.__p_to_r(BOARD_SIZE.height)):
            row = ["Dirt"] * self.__p_to_c(BOARD_SIZE.width)
            matrix.append(row)
        matrix = self.__create_blocks_from_string(matrix)
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
                location[index] = max(0, pos * randint(0,
                                self.MAX_CLUSTER_SIZE) + center[index])
            if location not in ore_locations:
                ore_locations.append(location)
        return ore_locations

    def __create_blocks_from_string(self, s_matrix):
        """
        Change strings into blocks

        :param s_matrix: a string matrix that contains strings corresponding to
        material classes
        :return: the s_matrix filled with block class instances

        Blit squares in the color of the material onto the base image.
        """
        for row_i, row in enumerate(s_matrix):
            for column_i, value in enumerate(row):
                #create position
                pos = (column_i * BLOCK_SIZE.width,
                       row_i * BLOCK_SIZE.height,)
                if s_matrix[row_i][column_i] == "Air":
                    block = AirBlock(pos, BLOCK_SIZE)
                else:
                    material = getattr(materials, s_matrix[row_i][column_i])(row_i)
                    block = Block(pos, BLOCK_SIZE, material)
                s_matrix[row_i][column_i] = block
        return s_matrix


class BoardImage(Entity):
    """
    Convert a matrix of blocks into a surface that persists as an entity. This
    is done to severly decrease the amount of blit calls and allow for layering
    of images aswell as easily scaling.
    """
    def __init__(self, main_sprite_group, **kwargs):
        Entity.__init__(self, (0, 0), BOARD_SIZE, main_sprite_group, **kwargs)

    def _create_image(self, size, color, **kwargs):
        """
        Overwrites the image creation process in the basic Entity class
        """
        block_matrix = kwargs["block_matrix"]
        image = pygame.Surface(size)
        image.set_colorkey((0,0,0), RLEACCEL)
        image = image.convert_alpha()
        for row in block_matrix:
            for block in row:
                if block != "Air":
                    image.blit(block.surface, block.rect)
        return image

    def add_rect(self, rect, color):
        """
        Remove a rectangle from the foreground by blitting a transparant
        rectangle on top

        :param rect: a pygame rect object
        """
        pygame.draw.rect(self.orig_image, color, rect)
        zoomed_rect = pygame.Rect((round(rect.x * self._zoom), round(rect.y * self._zoom), round(rect.width * self._zoom), round(rect.height * self._zoom)))
        pygame.draw.rect(self.image, color, zoomed_rect)

class TransparantBoardImage(BoardImage):
    """
    Slight variation on the basic Board image that creates a transparant
    surface on which selections can be drawn
    """
    def __init__(self, main_sprite_group, **kwargs):
        BoardImage.__init__(self, main_sprite_group, **kwargs)

    def _create_image(self, size, color, **kwargs):
        """
        Overwrites the image creation process in the basic Entity class
        """
        image = pygame.Surface(size).convert_alpha()
        image.set_colorkey((0,0,0), RLEACCEL)
        image.fill(INVISIBLE_COLOR)
        return image

