from random import randint, choices, choice

from python_code.entities import ZoomableEntity, SelectionRectangle
from python_code.utility.utilities import *
from python_code.board import materials
from python_code.utility.constants import *
from python_code.board.pathfinding import PathFinder
from python_code.board import buildings
from  python_code.board.buildings import *
from python_code.utility.event_handling import BoardEventHandler
from python_code.building.building import get_selected_item

class Board(BoardEventHandler):
    """
    Class that holds a matrix of blocks that is a playing field and an image
    representing set matrix
    """
    START_RECTANGLE = pygame.Rect((BOARD_SIZE.width / 2 - 125, 0, 250, 50))
    BLOCK_PER_CLUSRTER = 500
    #the max size of a ore cluster around the center
    MAX_CLUSTER_SIZE = 3
    def __init__(self, main_sprite_group):
        BoardEventHandler.__init__(self, [1, 2, 3, 4, MINING, CANCEL, BUILDING, SELECTING])
        self.inventorie_blocks = []

        #setup the board
        self.matrix = self.__generate_foreground_matrix()
        self.back_matrix = self.__generate_background_matrix()
        self.__add_starter_buildings()
        self.foreground_image = BoardImage(main_sprite_group,
                                           block_matrix = self.matrix, layer = BOARD_LAYER)
        self.background_image = BoardImage(main_sprite_group,
                                           block_matrix = self.back_matrix, layer = BACKGROUND_LAYER)
        self.selection_image = TransparantBoardImage(main_sprite_group, layer = HIGHLIGHT_LAYER)

        #variables needed when playing
        self.pf = PathFinder(self.matrix)
        self.task_control = None

    def add_building(self, building_instance, draw = True):
        """
        Add a building into the matrix and potentially draw it when requested

        :param building_instance: an instance of Building
        :param draw: Boolean telling if the foreground image should be updated
        mainly important when innitiating
        """
        for row_i, row in enumerate(building_instance.blocks):
            for column_i, block in enumerate(row):
                m_pos = (self.__p_to_c(block.coord[0]), self.__p_to_r(block.coord[1]))
                self.matrix[m_pos[1]][m_pos[0]] = block
                if draw:
                    self.foreground_image.add_image(block.rect, block.surface)
                if isinstance(block, ContainerBlock):
                    self.inventorie_blocks.append(block)

    def overlapping_blocks(self, rect):
        """
        Get a list of all overlapping blocks with a certain rectangle. The list
        is ordered from low to high x then y.

        :param rect: pygame Rect object that tells where the overlap is desired
        :return: a sub matrix of overlapping blocks
        """
        #make sure that blocks that are just selected are not included
        row_start = self.__p_to_r(rect.top + BLOCK_SIZE.height * 0.3)
        row_end = self.__p_to_r(rect.bottom - BLOCK_SIZE.height * 0.3)
        column_start = self.__p_to_c(rect.left + BLOCK_SIZE.width * 0.3)
        column_end = self.__p_to_c(rect.right - BLOCK_SIZE.width * 0.3)
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
        Remove a matrix of blocks from the second board layer by replacing them
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
                self.matrix[row][column] = AirBlock(block.rect.topleft, materials.Air())

    def add_block(self, block):
        """
        Add a block to the board by changing the matrix and blitting the image
        to the foreground_layer

        :param block: a BasicBlock object or inheriting class
        """
        self.foreground_image.add_image(block.rect, block.surface)
        # remove the highlight
        self.add_rectangle(INVISIBLE_COLOR, block.rect, layer=1)
        row = self.__p_to_r(block.rect.y)
        column = self.__p_to_c(block.rect.x)
        self.matrix[row][column] = block

    def closest_inventory(self, start):
        """
        Shortcut function for finding the closest inventory using __get_closest_block
        from a certain position of the worker.

        :param start: The coordinate of the worker looking for an inventory
        :return: a Block that is the closest inventory
        """
        return self.__get_closest_block(start, *self.inventorie_blocks)

    def __get_closest_block(self, start, *blocks):
        """
        Get the closest block in a list of blocks.

        :param start: a coordinate from where the closest blocks should be
        estimated
        :param blocks: a list of blocks that funtion as destinateion
        coordinates
        :return: a block from the list of blocks that is the closest or None
        when no block is reachable.

        The function uses pathfinding to estimate this so it should be used
        with care, meaning on lists of blocks that are not to big
        """
        #any distance should be shorter possible on the board
        shortest_distance = 10000000000000
        closest_block = None
        for block in blocks:
            path = self.pf.get_path(start, block.rect)
            if path != None and path.path_lenght < shortest_distance:
                shortest_distance = path.path_lenght
                closest_block = block
        return closest_block

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

    def collide_air(self, point):
        block = self.matrix[self.__p_to_r(point[1])][self.__p_to_c(point[0])]
        if block == "Air":
            return True
        return False

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

    def _get_task_rectangles(self, blocks, task_type):
        """
        Get all air spaces in the given matrix of blocks as a collection of
        rectangles

        :param blocks: a matrix of blocks
        :return: a list of rectangles
        """
        rectangles = []

        #save covered coordinates in a same lenght matrix for faster checking
        covered_coordinates = [[] for row in blocks]

        #find all rectangles in the block matrix
        for n_row, row in enumerate(blocks):
            for n_col, block in enumerate(row):
                if task_type in block.allowed_tasks or n_col in covered_coordinates[n_row]:
                    continue

                #calculate the maximum lenght of a rectangle based on already
                #established ones
                end_n_col = n_col
                for n in range(n_col, len(row)):
                    end_n_col = n
                    if end_n_col in covered_coordinates[n_row]:
                        break

                #find all air rectangles in a sub matrix
                sub_matrix = [sub_row[n_col:end_n_col] for sub_row in blocks[n_row:]]
                lm_coord = self.__find_task_rectangle(sub_matrix, task_type)

                # add newly covered coordinates
                for x in range(lm_coord[0]+ 1):
                    for y in range(lm_coord[1] + 1):
                        covered_coordinates[n_row + y].append(n_col + x)

                # add the air rectangle to the list of rectangles
                air_matrix = [sub_row[n_col:n_col + lm_coord[0] + 1] for sub_row in blocks[n_row:n_row + lm_coord[1] + 1]]
                rect = rect_from_block_matrix(air_matrix)
                rectangles.append(rect)
        return rectangles

    def __find_task_rectangle(self, blocks, task_type):
        """
        Find in a matrix of blocks all blocks of a certain task type

        :param blocks: a matrix of blocks
        :param task_type: the string name of a certain type of task
        :return:
        """
        #first find how far the column is filled cannot fill on 0 since 0 is guaranteed to be a air block
        x_size = 0
        for block in blocks[0][1:]:
            if task_type in block.allowed_tasks:
                break
            x_size += 1
        matrix_coordinate = [x_size, 0]

        #skip the first row since this was checked already
        block = None
        for n_row, row in enumerate(blocks[1:]):
            for n_col, block in enumerate(row[:x_size + 1]):
                if task_type in block.allowed_tasks:
                    break
            if block == None or task_type in block.allowed_tasks:
                break
            matrix_coordinate[1] += 1
        return matrix_coordinate


    # task management
    def _add_tasks(self, blocks):
        """
        Add tasks of the _mode.name type, tasks are added to the task control
        when they need to be assigned to workers or directly resolved otherwise

        :param blocks: a matrix of blocks
        """
        if self._mode.name == "Mining":
            self.task_control.add(self._mode.name, blocks)
        elif self._mode.name == "Cancel":
            rect = rect_from_block_matrix(blocks)
            # remove highlight
            self.add_rectangle(INVISIBLE_COLOR, rect, layer=1)
            for row in blocks:
                self.task_control.remove(*row, cancel=True)
        elif self._mode.name == "Building":
            build_blocks = self.__change_to_building_blocks(blocks)
            self.task_control.add(self._mode.name, build_blocks)

    def __change_to_building_blocks(self, blocks):
        """
        change a matrix of blocks to instances of BuildingBlock

        :param blocks: a matrix of blocks
        :return: the original matrix where all the air blocks are filles with
        BuildingBlocks
        """
        material = get_selected_item().material
        if isinstance(material, BuildingMaterial):
            name = material.name().replace("Material", "")
            building_block_i = getattr(buildings, name)
        else:
            building_block_i = Block
        for row_i, row in enumerate(blocks):
            for col_i, block in enumerate(row):
                if material.name() != block.material.name():
                    finish_block = building_block_i(block.rect.topleft, material)
                    row_i_m = self.__p_to_r(block.rect.y)
                    column_i_m = self.__p_to_c(block.rect.x)
                    self.matrix[row_i_m][column_i_m] = BuildingBlock(block.rect.topleft, BuildMaterial(), finish_block, block)
                    blocks[row_i][col_i] = self.matrix[row_i_m][column_i_m]
                else:
                    blocks[row_i][col_i] = None
        return blocks


#### MAP GENERATION FUNCTIONS ###

    def __generate_foreground_matrix(self):
        """
        Fill a matrix with names of the materials of the respective blocks

        :return: a matrix containing strings corresponding to names of __material
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

        matrix = self.__create_blocks_from_string(matrix)
        return matrix

    def __add_starter_buildings(self):
        """
        Add all starter building that should be placed before the game starts
        """
        t = Terminal((BOARD_SIZE[1] / 2 + 50, 30))
        self.add_building(t, draw = False)

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

        """
        for row_i, row in enumerate(s_matrix):
            for column_i, value in enumerate(row):
                #create position
                pos = (column_i * BLOCK_SIZE.width,
                       row_i * BLOCK_SIZE.height,)
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


class BoardImage(ZoomableEntity):
    """
    Convert a matrix of blocks into a surface that persists as an entity. This
    is done to severly decrease the amount of blit calls and allow for layering
    of images aswell as easily scaling.
    """
    def __init__(self, main_sprite_group, **kwargs):
        ZoomableEntity.__init__(self, (0, 0), BOARD_SIZE, main_sprite_group, **kwargs)
        self.visible = True

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
        Add a rectangle to the image, this can be a transparant rectangle to
        remove a part of the image or another rectangle

        :param rect: a pygame rect object
        """
        pygame.draw.rect(self.orig_image, color, rect)
        zoomed_rect = pygame.Rect((round(rect.x * self._zoom), round(rect.y * self._zoom), round(rect.width * self._zoom), round(rect.height * self._zoom)))
        pygame.draw.rect(self.image, color, zoomed_rect)

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

    #for determining mouse position on the board given the screen coordinate
    def _screen_to_board_coordinate(self, coord):
        """
        Calculate the screen to current board size coordinate. That is the
        zoomed in board. Then revert the coordinate back to the normal screen

        :param coord: a coordinate with x and y value within the screen region
        :return: a coordinate with x and y vale within the ORIGINAL_BOARD_SIZE.

        The value is scaled back to the original size after instead of
        being calculated as the original size on the spot because the screen
        coordinate can not be converted between zoom levels so easily.
        """
        c = self.groups()[0].target.rect.center
        #last half a screen of the board
        if BOARD_SIZE.width - c[0] - SCREEN_SIZE.width / 2 < 0:
            x = BOARD_SIZE.width - (SCREEN_SIZE.width - coord[0])
        #the rest of the board
        elif c[0] - SCREEN_SIZE.width / 2 > 0:
            x = coord[0] + (c[0] - SCREEN_SIZE.width / 2)
        #first half a screen of the board
        else:
            x = coord[0]
        if BOARD_SIZE.height - c[1] - SCREEN_SIZE.height / 2 < 0:
            y = BOARD_SIZE.height - (SCREEN_SIZE.height - coord[1])
        elif c[1] - SCREEN_SIZE.height / 2 > 0:
            y = coord[1] + (c[1] - SCREEN_SIZE.height / 2)
        else:
            y = coord[1]
        return [int(x / self._zoom), int(y / self._zoom)]

class TransparantBoardImage(BoardImage):
    """
    Slight variation on the basic Board image that creates a transparant
    surface on which selections can be drawn
    """
    def __init__(self, main_sprite_group, **kwargs):
        BoardImage.__init__(self, main_sprite_group, **kwargs)
        #the current SelectionRectangle object that shows
        self.selection_rectangle = None
        #last placed highlighted rectangle
        self.__highlight_rectangle = None

    def _create_image(self, size, color, **kwargs):
        """
        Overwrites the image creation process in the basic Entity class
        """
        image = pygame.Surface(size).convert_alpha()
        image.set_colorkey((0,0,0), RLEACCEL)
        image.fill(INVISIBLE_COLOR)
        return image

    def add_selection_rectangle(self, pos, keep = False):
        """
        Add a rectangle that shows what the user is currently selecting

        :param pos: the event.pos of the rectangle
        :param keep: if the previous highlight should be kept
        """
        mouse_pos = self._screen_to_board_coordinate(pos)
        # should the highlighted area stay when a new one is selected
        if not keep and self.__highlight_rectangle:
            self.add_rect(self.__highlight_rectangle, INVISIBLE_COLOR)
        self.selection_rectangle = SelectionRectangle(mouse_pos,
                                                       (0, 0), pos,
                                                       self.groups()[0],
                                                       zoom=self._zoom)

    def add_highlight_rectangle(self, rect, color):
        """
        Add a rectangle to this image that functions as highlight from the
        current selection

        :param rect: the rectangle to highlight, this is a slightly adjusted
        rectangle compared to the selection rectangle
        :param color: the color of the highlight
        """
        self.__highlight_rectangle = rect
        self.add_rect(rect, color)


    def remove_selection(self):
        """
        Safely remove the selection rectangle
        """
        if self.selection_rectangle:
            self.selection_rectangle.kill()
            self.selection_rectangle = None

    def reset_selection_and_highlight(self, keep):
        """
        Reset the selection of the selection layer and the highlight rectangle

        :param keep: if the highlight rectangle should be saved or not
        """
        if not keep and self.__highlight_rectangle:
            self.add_rect(self.__highlight_rectangle, INVISIBLE_COLOR)
        self.__highlight_rectangle = None
        self.remove_selection()


