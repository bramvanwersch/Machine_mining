from random import randint, choices, choice

from python_code.entities import Entity
from python_code.utilities import *
from python_code import materials
from python_code.constants import *
from python_code.pathfinding import PathFinder

class Board:
    """
    Class that holds a matrix of blocks that is a playing field and an image
    representing set matrix
    """
    START_RECTANGLE = pygame.Rect((BOARD_SIZE.width / 2 - 125, 0, 250, 50))
    BLOCK_PER_CLUSRTER = 500
    #the max size of a ore cluster around the center
    MAX_CLUSTER_SIZE = 3
    def __init__(self, pixel_board_size, main_sprite_group):
        self.matrix = self.__generate_foreground_matrix(pixel_board_size)
        self.back_matrix = self.__generate_background_matrix(pixel_board_size)
        self.foreground_image = BoardImage(pixel_board_size, main_sprite_group,
                                           block_matrix = self.matrix, layer = BOTTOM_LAYER)
        self.background_image = BoardImage(pixel_board_size, main_sprite_group,
                                           block_matrix = self.back_matrix, layer = BOTTOM_LAYER - 1)
        self.selection_image = TransparantBoardImage(pixel_board_size, main_sprite_group, layer = BOTTOM_LAYER + 1)
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

    def pathfind(self, start, end):
        """
        Returns a list of tuples as a path from the given start to the given end
        https://gist.github.com/Nicholas-Swift/003e1932ef2804bebef2710527008f44#file-astar-py
        """
        start = (self.__p_to_r(start[1]), self.__p_to_c(start[0]))
        end = (self.__p_to_r(end[1]), self.__p_to_c(end[0]))
        # Create start and end node
        start_node = Node(None, start)
        start_node.g = start_node.f = 0
        end_node = Node(None, end)
        end_node.g = end_node.h = end_node.f = 0
        start_node.h = manhattan_distance(start_node.position, end_node.position)

        # Initialize both open and closed list
        open_list = []
        closed_list = []

        # Add the start node
        open_list.append(start_node)

        # Loop until you find the end
        outer_iterations = 0
        while len(open_list) > 0:

            # Get the current node with lowest f
            current_node = open_list[0]
            current_index = 0
            for index, item in enumerate(open_list):
                if item.f < current_node.f:
                    current_node = item
                    current_index = index

            # Pop current off open list, add to closed list
            open_list.pop(current_index)
            closed_list.append(current_node)

            # Found the goal on block infront of destination
            if current_node.h <= 1 and current_node.h > 0:
                return self.__retrace_path(current_node)

            # Generate children
            children = []
            for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]:  # Adjacent squares

                # Get node position
                node_position = (current_node.position[0] + new_position[0],
                                 current_node.position[1] + new_position[1])

                # Make sure within range
                if node_position[0] > (len(self.matrix) - 1) or node_position[
                    0] < 0 or node_position[1] > (
                        len(self.matrix[len(self.matrix) - 1]) - 1) or node_position[1] < 0:
                    continue

                # Make sure walkable terrain
                if self.matrix[node_position[0]][node_position[1]] != "Air":
                    continue

                # Create new node
                new_node = Node(current_node, node_position)

                # Append
                children.append(new_node)

            # Loop through children
            for child in children:

                # Child is on the closed list
                if len([closed_child for closed_child in closed_list if
                        closed_child == child]) > 0:
                    continue

                # Create the f, g, and h values
                child.g = current_node.g + 1
                child.h = manhattan_distance(child.position, end_node.position)
                child.f = child.g + child.h

                # Child is already in the open list
                if len([open_node for open_node in open_list if
                        child.position == open_node.position]) > 0:
                    continue

                # Add the child to the open list
                open_list.append(child)
        return None

    def __retrace_path(self, node):
        """
        Retrace from a given node class back to the starting parent node

        :param node: A Node object
        :return: a list of tuples that is the paht from end to start.

        transforms matrix indexes into board coordinates aswell as flipping the
        positions.
        """
        prev_node = (node.position[1] * BLOCK_SIZE.width,
                       node.position[0] * BLOCK_SIZE.height)
        path = [prev_node]
        while node is not None:
            board_coord = (node.position[1] * BLOCK_SIZE.width,
                           node.position[0] * BLOCK_SIZE.height)
            if path[-1][0] != board_coord[0] and path[-1][1] != board_coord[1]:
                path.append(prev_node)
            prev_node = board_coord
            node = node.parent
        return path

    def remove_blocks(self, blocks, layer = 2):
        """
        """
        for row in blocks:
            for block in row:
                row = self.__p_to_r(block.rect.y)
                column = self.__p_to_c(block.rect.x)
                self.matrix[row][column] = AirBlock(block.rect.topleft, block.rect.size)
                self.add_rectangle(INVISIBLE_COLOR, block.rect, layer=layer)
                #remove the highlight
                self.add_rectangle(INVISIBLE_COLOR, block.rect, layer = 1)

    def highlight_non_air_blocks(self, color, blocks):
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

    def __generate_foreground_matrix(self, size):
        """
        Fill a matrix with names of the materials of the respective blocks

        :return: a matrix containing strings corresponding to names of material
        classes.
        """

        matrix = []
        #first make everything stone
        for _ in range(self.__p_to_r(size.height)):
            row = ["Stone"] * self.__p_to_c(size.width)
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

    def __generate_background_matrix(self, size):
        """
        Generate the backdrop matrix.

        :param size: the size of the matrix
        :return: a matrix of the given size
        """
        matrix = []
        for _ in range(self.__p_to_r(size.height)):
            row = ["Dirt"] * self.__p_to_c(size.width)
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

class BaseBlock:
    """
    Base class for the blocks in image matrices
    """
    def __init__(self, pos, size):
        if type(self) == BaseBlock:
            raise Exception("Cannot instantiate base class BaseBlock")
        self.size = size
        self.rect = pygame.Rect((*pos, *self.size))
        self.tasks = {}

    def add_task(self, task):
        """
        Can hold a task from each type

        :param task: a Task object
        """
        self.tasks[task.task_type] = task

    def remove_finished_tasks(self):
        """
        Check if tasks are finished or not.

        :return: a list of task types that are removed.
        """
        finished = []
        for key in list(self.tasks.keys()):
            task = self.tasks[key]
            if task.finished:
                del self.tasks[task.task_type]
                finished.append(task.task_type)
        return finished

    @property
    def coord(self):
        """
        Simplify getting the coordinate of a block

        :return: the topleft cooridnate of the block rectangle.
        """
        return self.rect.topleft

    def __eq__(self, other):
        return other == self.material

    def __hash__(self):
        return hash(str(self.rect.topleft))

class Block(BaseBlock):
    """
    A normal block containing anythin but air
    """
    def __init__(self, pos, size, material):
        super().__init__(pos, size)
        self.material = material
        self.surface = self.__create_surface()
        self.rect = self.surface.get_rect(topleft=pos)

    def add_task(self, task):
        """
        Add an additional task progress for the task on a material block
        """
        super().add_task(task)
        task.task_progress = [0, self.material.task_time()]

    def __create_surface(self):
        """
        Create the surface of the block, this depends on the depth of the block
        and potential border

        :return: a pygame Surface object
        """
        surface = pygame.Surface(self.size)
        surface.fill(self.material.color)
        if SHOW_BLOCK_BORDER:
            pygame.draw.rect(surface, self.material.border_color,
                             (0, 0, self.size.width + 1,
                              self.size.height + 1), 1)
        return surface.convert()

class AirBlock(BaseBlock):
    """
    Special case of a block class that is an empty block with no surface
    """
    def __init__(self, pos, size):
        super().__init__(pos, size)
        self.material = "Air"

class BoardImage(Entity):
    """
    Convert a matrix of blocks into a surface that persists as an entity. This
    is done to severly decrease the amount of blit calls and allow for layering
    of images aswell as easily scaling.
    """
    def __init__(self, pixel_board_size, main_sprite_group, **kwargs):
        Entity.__init__(self, (0, 0), pixel_board_size, main_sprite_group, **kwargs)

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
    def __init__(self, pixel_board_size, main_sprite_group, **kwargs):
        BoardImage.__init__(self, pixel_board_size, main_sprite_group, **kwargs)

    def _create_image(self, size, color, **kwargs):
        """
        Overwrites the image creation process in the basic Entity class
        """
        image = pygame.Surface(size).convert_alpha()
        image.set_colorkey((0,0,0), RLEACCEL)
        image.fill(INVISIBLE_COLOR)
        return image

