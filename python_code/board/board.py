from random import choices, choice, randint, uniform
from math import sin, cos, pi

from python_code.entities import SelectionRectangle
from python_code.utility.utilities import *
from python_code.board import materials
from python_code.utility.constants import *
from python_code.board.pathfinding import PathFinder
from python_code.board.buildings import *
from python_code.utility.event_handling import BoardEventHandler
from python_code.interfaces.building_interface import get_selected_item
from python_code.network.pipes import Network
from python_code.interfaces.interface_utility import *
from python_code.board.chunks import *

class Board(BoardEventHandler):

    #ORE cluster values
    #the amount of normal blocks per cluster
    CLUSTER_LIKELYHOOD = 120
    #the max size of a ore cluster around the center
    MAX_CLUSTER_SIZE = 3

    #CAVE values
    MAX_CAVES = int((CHUNK_GRID_SIZE.width * CHUNK_GRID_SIZE.height) / 6)
    #the fraction of the distance between points based on the shortest side of the board
    POINT_FRACTION_DISTANCE = 0.35
    #distance the center of the cave should at least be away from the border
    CAVE_X_BORDER_DISTANCE = int(0.1 * BOARD_SIZE.width)
    CAVE_Y_BORDER_DISTANCE = int(0.1 * BOARD_SIZE.height)
    NUMBER_OF_CAVE_POINTS = int(CHUNK_GRID_SIZE.width * CHUNK_GRID_SIZE.height * 1.3)
    #the chance for a cave to stop extending around its core. Do not go lower then 0.0001 --> takes a long time
    CAVE_STOP_SPREAD_CHANCE = 0.05

    #BORDER values
    SPREAD_LIKELYHOOD = Gaussian(0, 2)
    MAX_SPREAD_DISTANCE = 4
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
        self.main_sprite_group = main_sprite_group

        #setup the board
        # self.matrix = self.__generate_foreground_matrix()
        self.pf = PathFinder()
        self.chunk_matrix = self.__generate_chunk_matrix(main_sprite_group)
        # self.back_matrix = self.__generate_background_matrix()
        # self.foreground_image = BoardImage(main_sprite_group, block_matrix = self.matrix, layer = BOARD_LAYER)
        # self.background_image = BoardImage(main_sprite_group, block_matrix = self.back_matrix, layer = BACKGROUND_LAYER)
        # self.selection_image = TransparantBoardImage(main_sprite_group, layer = HIGHLIGHT_LAYER)

        self.task_control = None

        #the current SelectionRectangle object that shows
        self.selection_rectangle = None
        #last placed highlighted rectangle
        self.__highlight_rectangle = None

        #pipe network
        self.pipe_network = Network(self.task_control)

        self.__buildings = {}
        self.__add_starter_buildings()

        #variables needed when playing

    def __generate_chunk_matrix(self, main_sprite_group):
        foreground_matrix = self.__generate_foreground_string_matrix()
        background_matrix = self.__generate_background_string_matrix()
        chunk_matrix = []
        for col_c in range(CHUNK_GRID_SIZE.height):
            chunk_row = []
            for row_c in range(CHUNK_GRID_SIZE.width):
                point_pos = (row_c * CHUNK_SIZE.width, col_c * CHUNK_SIZE.height)
                for_string_matrix = [row[p_to_c(row_c * CHUNK_SIZE.height):p_to_r((row_c + 1) * CHUNK_SIZE.height)] for\
                    row in foreground_matrix[p_to_r(col_c * CHUNK_SIZE.width):p_to_r((col_c + 1) * CHUNK_SIZE.width)]]
                back_string_matrix = [row[p_to_c(row_c * CHUNK_SIZE.height):p_to_r((row_c + 1) * CHUNK_SIZE.height)] for\
                    row in background_matrix[p_to_r(col_c * CHUNK_SIZE.width):p_to_r((col_c + 1) * CHUNK_SIZE.width)]]
                if (row_c, col_c) == START_CHUNK_POS:
                    chunk = StartChunk(point_pos, for_string_matrix, back_string_matrix, main_sprite_group)
                else:
                    chunk = Chunk(point_pos, for_string_matrix, back_string_matrix, main_sprite_group)
                chunk_row.append(chunk)
                self.pf.pathfinding_tree.add_chunk(chunk.pathfinding_chunk)
            chunk_matrix.append(chunk_row)
        return chunk_matrix

    def get_start_chunk(self):
        for row in self.chunk_matrix:
            for chunk in row:
                if isinstance(chunk, StartChunk):
                    return chunk
        #should not happen
        return None

    def __get_chunks_from_rect(self, rect):
        affected_chunks = []
        tl_column, tl_row = p_to_cp(rect.topleft)
        br_column, br_row = p_to_cp(rect.bottomright)
        top = rect.top
        for row in range(br_row - tl_row + 1):
            if row == 0:
                height = min(CHUNK_SIZE.height - (top % CHUNK_SIZE.height), rect.height)
            else:
                height = ((rect.bottom - top) % CHUNK_SIZE.height)
            left = rect.left
            for column in range(br_column - tl_column + 1):
                if column == 0:
                    width = min(CHUNK_SIZE.width - (left % CHUNK_SIZE.width), rect.width)
                else:
                    width = ((rect.right - left) % CHUNK_SIZE.width)
                topleft = (left, top)
                new_rect = pygame.Rect((*topleft, width, height))
                chunk = self.__chunk_from_point(topleft)
                affected_chunks.append([chunk, new_rect])
                left += width
            top += height
        return affected_chunks

    def __get_blocks_from_rect(self, rect):
        blocks = []
        for chunk, rect in self.__get_chunks_from_rect(rect):
            for y_coord in range(rect.top, rect.bottom, BLOCK_SIZE.height):
                for x_coord in range(rect.left, rect.right, BLOCK_SIZE.width):
                    point = (x_coord, y_coord)
                    blocks.append(chunk.get_block(point))
        return blocks

    def set_task_control(self, task_control):
        self.task_control = task_control
        self.pipe_network.task_control = task_control

    def surrounding_blocks(self, block):
        """
        Calculate the surrounding blocks of a certain block in the order
        NESW and None if there is no block (edge of the playing field).

        :param block: the center Block Object for the surrounding blocks
        :param matrix: the matrix that contains the surrounding blocks
        :return: 4 Block or None objects
        """
        blocks = [None, None, None, None]
        for index, new_position in enumerate([(0, -1), (1, 0), (0, 1), (-1, 0)]):
            surrounding_pos = (block.rect.x + new_position[0] * BLOCK_SIZE.width, block.rect.y + new_position[1] * BLOCK_SIZE.height)
            # Make sure within range
            if surrounding_pos[0] > BOARD_SIZE.width or \
                surrounding_pos[0] < 0 or \
                surrounding_pos[1] > BOARD_SIZE.height or \
                surrounding_pos[1] < 0:
                continue
            chunk = self.__chunk_from_point(surrounding_pos)
            surrouding_block = chunk.get_block(surrounding_pos)
            blocks[index] = surrouding_block
        return blocks

    def remove_blocks(self, *blocks):
        for block in blocks:
            if block.id in self.__buildings:
                self.remove_building(block)
            else:
                chunk = self.__chunk_from_point(block.rect.topleft)
                chunk.remove_blocks(block)
            if isinstance(block, NetworkBlock):
                surrounding_blocks = self.surrounding_blocks(block)
                self.pipe_network.remove_pipe(block)
                for block in surrounding_blocks:
                    if isinstance(block, NetworkBlock) and not isinstance(block, ContainerBlock):
                        self.pipe_network.configure_block(block, self.surrounding_blocks(block), remove=True)
                        self.add_blocks(block)

    def remove_building(self, block):
        building_instance = self.__buildings.pop(block.id, None)
        if building_instance == None:
            return
        if isinstance(block, NetworkBlock):
            self.pipe_network.remove_node(building_instance)
        blocks = building_instance.blocks
        for row in blocks:
            for block in row:
                self.task_control.cancel_tasks(block, remove=True)
                chunk = self.__chunk_from_point(block.rect.topleft)
                chunk.remove_blocks(block)

    def add_blocks(self, *blocks, update=False):
        """
        Add a block to the board by changing the matrix and blitting the image
        to the foreground_layer

        :param blocks: one or more BasicBlock objects or inheriting classes
        """
        update_blocks = []
        for block in blocks:
            if isinstance(block, Building):
                self.add_building(block)
            else:
                if isinstance(block, NetworkBlock):
                    update_blocks.extend(self.pipe_network.configure_block(block, self.surrounding_blocks(block), update=update))
                    if update:
                        self.pipe_network.add_pipe(block)
                chunk = self.__chunk_from_point(block.coord)
                chunk.add_blocks(block)
        if len(update_blocks) > 0:
            self.add_blocks(*update_blocks)

    def add_building(self, building_instance, draw = True):
        """
        Add a building into the matrix and potentially draw it when requested

        :param building_instance: an instance of Building
        :param draw: Boolean telling if the foreground image should be updated
        mainly important when innitiating
        #TODO lookinto what the draw parameter ads
        """
        building_rect = building_instance.rect
        self.__buildings[building_instance.id] = building_instance
        update_blocks = []
        if isinstance(building_instance, NetworkNode):
            self.pipe_network.add_node(building_instance)
        for row in building_instance.blocks:
            for block in row:
                chunk = self.__chunk_from_point(block.coord)
                chunk.add_blocks(block)
                if isinstance(block, ContainerBlock):
                    self.inventorie_blocks.append(block)
                    update_blocks.extend(self.pipe_network.configure_block(block, self.surrounding_blocks(block), update=True))
        if len(update_blocks) > 0:
            update_blocks = [block for block in update_blocks if not isinstance(block, ContainerBlock)]
            self.add_blocks(*update_blocks)

    def closest_inventory(self, start, *item_names, deposit=True):
        """
        """
        #any distance should be shorter possible on the board
        shortest_distance = 10000000000000
        closest_block = None
        for block in self.inventorie_blocks:
            if (deposit == False and all([block.inventory.check_item_get(name) for name in item_names])):
                pass
            elif (deposit == True and all([block.inventory.check_item_deposit(name) for name in item_names])):
                pass
            else:
                continue
            path = self.pf.get_path(start, block.rect)
            if path != None and path.path_lenght < shortest_distance:
                shortest_distance = path.path_lenght
                closest_block = block
        return closest_block

    def add_rectangle(self, rect, color, layer=2, border=0):
        """
        Add a rectangle on to one of the layers.

        :param color: the color of the rectangle. Use INVISIBLE_COLOR to make
        rectangles dissapear
        :param layer: an integer that between 1 and 3 that tells at what layer
        the rectangle should be added

        This can be used to remove parts of the image or add something to it
        """
        chunk_rectangles = self.__get_chunks_from_rect(rect)
        for chunk, rect in chunk_rectangles:
            chunk.add_rectangle(rect, color, layer, border)

    def __getitem__(self, item):
        return self.matrix[item]

    def transparant_collide(self, point):
        chunk = self.__chunk_from_point(point)
        block = chunk.get_block(point)
        if block.transparant_group != 0:
            return True
        return False

    def __chunk_from_point(self, point):
        column, row = p_to_cp(point)
        return self.chunk_matrix[row][column]

    def add_selection_rectangle(self, pos, keep = False):
        """
        Add a rectangle that shows what the user is currently selecting

        :param pos: the event.pos of the rectangle
        :param keep: if the previous highlight should be kept
        """
        #bit retarded
        zoom = self.chunk_matrix[0][0].selection_image._zoom
        mouse_pos = screen_to_board_coordinate(pos, self.main_sprite_group.target, zoom)
        # should the highlighted area stay when a new one is selected
        if not keep and self.__highlight_rectangle:
            self.add_rectangle(rect, INVISIBLE_COLOR, layer=1)
        self.selection_rectangle = SelectionRectangle(mouse_pos, (0, 0), pos,
                                                      self.main_sprite_group,zoom=zoom)

    def add_building_rectangle(self, pos, size=(10, 10)):
        # bit retarded
        zoom = self.chunk_matrix[0][0].selection_image._zoom
        mouse_pos = screen_to_board_coordinate(pos, self.main_sprite_group.target, zoom)
        self.selection_rectangle = ZoomableEntity(mouse_pos, size - BLOCK_SIZE,
                                                  self.main_sprite_group, zoom=zoom, color=INVISIBLE_COLOR)

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
            self.add_rectangle(self.__highlight_rectangle, INVISIBLE_COLOR, layer=1)
        self.__highlight_rectangle = None
        self.remove_selection()

    def add_highlight_rectangle(self, rect, color):
        """
        Add a rectangle to this image that functions as highlight from the
        current selection
        :param color: the color of the highlight
        """
        self.__highlight_rectangle = rect
        self.add_rectangle(rect, color, layer=1)

    def _handle_mouse_events(self):
        """
        Handle mouse events issued by the user.
        """
        #mousebutton1
        if self.pressed(1):
            if self._mode.name in ["Mining", "Cancel", "Selecting"]:
                keep = False
                if self._mode.name == "Mining":
                    keep = True
                self.reset_selection_and_highlight(keep)
                self.add_selection_rectangle(self.get_key(1).event.pos, self._mode.persistent_highlight)

            elif self._mode.name == "Building":
                item = get_selected_item()
                # if no item is selected dont do anything
                if item == None:
                    return
                material = get_selected_item().material
                building_block_i = block_i_from_material(material)
                self.add_building_rectangle(self.get_key(1).event.pos, size=building_block_i.SIZE)
        elif self.unpressed(1):
            if self._mode.name == "Selecting":
                # bit retarded
                zoom = self.chunk_matrix[0][0].selection_image._zoom
                board_coord = screen_to_board_coordinate(self.get_key(1).event.pos, self.main_sprite_group.target, zoom)
                chunk = self.__chunk_from_point(board_coord)
                chunk.get_block(board_coord).action()
            self.__process_selection()
            self.remove_selection()

    def __process_selection(self):
        """
        Process selection by adding tasks, and direct the board to highlight
        the tasks
        """
        if self.selection_rectangle == None:
            return
        chunks_rectangles = self.__get_chunks_from_rect(self.selection_rectangle.orig_rect)
        first_chunk = chunks_rectangles[0][0]
        selection_matrix = first_chunk.overlapping_blocks(chunks_rectangles[0][1])
        for chunk, rect in chunks_rectangles[1:]:
            blocks = chunk.overlapping_blocks(rect)
            #extending horizontal
            if chunk.coord[0] > first_chunk.coord[0]:
                extra_rows = len(selection_matrix) - len(blocks)
                for row_i, row in enumerate(blocks):
                    selection_matrix[extra_rows + row_i].extend(row)
            #extending vertical
            else:
                for row_i, row in enumerate(blocks):
                    selection_matrix.append(row)
        for index in range(len(selection_matrix[1:])):
            assert len(selection_matrix[index]) == len(selection_matrix[index - 1])
        # the user is selecting blocks
        if len(selection_matrix) > 0:
            self._assign_tasks(selection_matrix)

    def _get_task_rectangles(self, blocks, task_type=None, dissallowed_block_types=[]):
        """
        Get all spaces of a certain block type, task or both

        :param blocks: a matrix of blocks
        :return: a list of rectangles
        """
        rectangles = []
        approved_blocks = []

        #save covered coordinates in a same lenght matrix for faster checking
        covered_coordinates = [[] for row in blocks]

        #find all rectangles in the block matrix
        for n_row, row in enumerate(blocks):
            for n_col, block in enumerate(row):
                if (task_type in block.allowed_tasks) and (block.name() not in dissallowed_block_types) or n_col in covered_coordinates[n_row]:
                    if n_col not in covered_coordinates[n_row]:
                        approved_blocks.append(block)
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
                lm_coord = self.__find_task_rectangle(sub_matrix, task_type, dissallowed_block_types)

                # add newly covered coordinates
                for x in range(lm_coord[0]+ 1):
                    for y in range(lm_coord[1] + 1):
                        covered_coordinates[n_row + y].append(n_col + x)

                # add the air rectangle to the list of rectangles
                air_matrix = [sub_row[n_col:n_col + lm_coord[0] + 1] for sub_row in blocks[n_row:n_row + lm_coord[1] + 1]]
                rect = rect_from_block_matrix(air_matrix)
                rectangles.append(rect)
        return rectangles, approved_blocks

    def __find_task_rectangle(self, blocks, task_type, dissallowed_block_types):
        """
        Find in a matrix of blocks all blocks of a certain task type

        :param blocks: a matrix of blocks
        :param task_type: the string name of a certain type of task
        :return:
        """
        #first find how far the column is filled cannot fill on 0 since 0 is guaranteed to be a air block
        x_size = 0
        for block in blocks[0][1:]:
            if (task_type in block.allowed_tasks) and (block.name() not in dissallowed_block_types):
                break
            x_size += 1
        matrix_coordinate = [x_size, 0]

        #skip the first row since this was checked already
        block = None
        for n_row, row in enumerate(blocks[1:]):
            for n_col, block in enumerate(row[:x_size + 1]):
                if (task_type in block.allowed_tasks) and (block.name() not in dissallowed_block_types):
                    break
            if block == None or (task_type in block.allowed_tasks) and (block.name() not in dissallowed_block_types):
                break
            matrix_coordinate[1] += 1
        return matrix_coordinate

    def _assign_tasks(self, blocks):
        rect = rect_from_block_matrix(blocks)

        #remove all tasks present
        for row in blocks:
            for block in row:
                self.task_control.cancel_tasks(block, remove=True)

        #select the full area
        self.add_highlight_rectangle(rect, self._mode.color)

        #assign tasks to all blocks elligable
        if self._mode.name == "Building":
            no_highlight_block = get_selected_item().name()
            no_task_rectangles, approved_blocks = self._get_task_rectangles(blocks, self._mode.name, [no_highlight_block])
            #if not the full image was selected dont add tasks
            if len(no_task_rectangles) > 0:
                self.add_rectangle(rect, INVISIBLE_COLOR, layer=1)
                return
            #the first block of the selection is the start block of the material
            approved_blocks = [blocks[0][0]]
        elif self._mode.name == "Cancel":
            # remove highlight
            self.add_rectangle(rect, INVISIBLE_COLOR, layer=1)
            return
        else:
            no_task_rectangles, approved_blocks = self._get_task_rectangles(blocks, self._mode.name)

        for rect in no_task_rectangles:
            self.add_rectangle(rect, INVISIBLE_COLOR, layer=1)
        self._add_tasks(approved_blocks)

    # task management
    def _add_tasks(self, blocks):
        """
        Add tasks of the _mode.name type, tasks are added to the task control
        when they need to be assigned to workers or directly resolved otherwise

        :param blocks: a list of blocks
        """
        if self._mode.name == "Mining":
            self.task_control.add(self._mode.name, *blocks)
        elif self._mode.name == "Building":
            #this should always be 1 block
            block = blocks[0]
            material = get_selected_item().material
            building_block_i = block_i_from_material(material)
            group = block.transparant_group
            if group != 0:
                block.transparant_group = unique_group()
            if issubclass(building_block_i, InterafaceBuilding):
                finish_block = building_block_i(block.rect.topleft, self.main_sprite_group, material=material)
            else:
                finish_block = building_block_i(block.rect.topleft, material=material)
            if isinstance(finish_block, Building):
                overlap_rect = pygame.Rect((*finish_block.rect.topleft, finish_block.rect.width - 1, finish_block.rect.height - 1))
                overlap_blocks = self.__get_blocks_from_rect(overlap_rect)
            else:
                overlap_blocks = [block]
            self.task_control.add(self._mode.name, block, finish_block = finish_block, original_group=group, removed_blocks=overlap_blocks)


#### MAP GENERATION FUNCTIONS ###

    def __generate_foreground_string_matrix(self):
        matrix = self.__generate_stone_background()
        self.__add_ores(matrix)
        self.__add_caves(matrix)
        self.__add_border(matrix)
        return matrix

    def __generate_stone_background(self):
        matrix = []
        for row_i in range(p_to_r(BOARD_SIZE.height)):
            filler_likelyhoods = self.__get_material_lh_at_depth(materials.filler_materials, row_i)
            row = []
            for _ in range(p_to_c(BOARD_SIZE.width)):
                filler = choices([f.name() for f in materials.filler_materials], filler_likelyhoods, k=1)[0]
                row.append(filler)
            matrix.append(row)
        return matrix

    def __add_caves(self, matrix):
        nr_caves = randint(self.MAX_CAVES - int(max(self.MAX_CAVES / 2, 1)), self.MAX_CAVES)
        for _ in range(nr_caves):
            cave_points = self.__get_cave_points()
            #get the line between the points
            for index in range(1, len(cave_points)):
                point1 = cave_points[index - 1]
                point2 = cave_points[index]
                a, b = line_from_points(point1, point2)
                if abs(a) < 1:
                    number_of_breaks = int(abs(point1[0] - point2[0]) * abs(1 / a))
                else:
                    number_of_breaks = int(abs(point1[0] - point2[0]) * abs(a))
                break_size = (point2[0] - point1[0]) / number_of_breaks
                x_values = [point1[0] + index * break_size for index in range(0, number_of_breaks)]
                y_values = [a * x + b for x in x_values]
                #make all blocks air on the direct line
                for index in range(len(x_values)):
                    x = int(x_values[index])
                    y = int(y_values[index])
                    matrix[min(y, int(BOARD_SIZE.height / BLOCK_SIZE.height) -1)][min(x, int(BOARD_SIZE.width / BLOCK_SIZE.width) - 1)] = "Air"
                    surrounding_coords = [coord for coord in self.__get_surrounding_block_coords(x, y) if matrix[coord[1]][coord[0]] != "Air"]
                    #extend the cave around the direct line.
                    while len(surrounding_coords) > 0:
                        if uniform(0, 1) < self.CAVE_STOP_SPREAD_CHANCE:
                            break
                        remove_block = choice(surrounding_coords)
                        surrounding_coords.remove(remove_block)
                        matrix[remove_block[1]][remove_block[0]] = "Air"
                        new_sur_coords = surrounding_coords.extend([coord for coord in self.__get_surrounding_block_coords(*remove_block) if matrix[coord[1]][coord[0]] != "Air"])
        return matrix

    def __get_cave_points(self):
        max_radius = int(min(*BOARD_SIZE) * self.POINT_FRACTION_DISTANCE)

        # random point on the board within 10% of the boundaries
        first_point = [randint(self.CAVE_X_BORDER_DISTANCE, BOARD_SIZE.width - self.CAVE_X_BORDER_DISTANCE),
                       randint(self.CAVE_Y_BORDER_DISTANCE, BOARD_SIZE.height - self.CAVE_Y_BORDER_DISTANCE)]
        cave_points = [first_point]
        prev_direction = uniform(0, 2 * pi)
        amnt_points = randint(self.NUMBER_OF_CAVE_POINTS - int(max(self.NUMBER_OF_CAVE_POINTS / 2, 1)), self.NUMBER_OF_CAVE_POINTS)
        while len(cave_points) < amnt_points:
            radius = randint(max(1, int(max_radius / 2)), max_radius)
            prev_direction = uniform(prev_direction - 0.5 * pi, prev_direction + 0.5 * pi)
            new_x = min(max(int(cave_points[-1][0] + cos(prev_direction) * radius), self.CAVE_X_BORDER_DISTANCE),
                        BOARD_SIZE.width - self.CAVE_X_BORDER_DISTANCE)
            new_y = min(max(int(cave_points[-1][1] + sin(prev_direction) * radius), self.CAVE_Y_BORDER_DISTANCE),
                        BOARD_SIZE.height - self.CAVE_Y_BORDER_DISTANCE)
            #make sure no double points and no straight lines
            if [new_x, new_y] in cave_points or \
                    int(new_x / BLOCK_SIZE.width) == int(cave_points[-1][0] / BLOCK_SIZE.width) or\
                    int(new_y / BLOCK_SIZE.height) == int(cave_points[-1][1] / BLOCK_SIZE.height):
                continue
            cave_points.append([new_x, new_y])
        return [[int(x / BLOCK_SIZE.width), int(y / BLOCK_SIZE.height)] for x, y in cave_points]

    def __get_surrounding_block_coords(self, x, y):
        surrounding_coords = []
        for index, new_position in enumerate([(0, -1), (1, 0), (0, 1), (-1, 0)]):
            surrounding_coord = [x - new_position[0], y - new_position[1]]
            # Make sure within range
            if surrounding_coord[0] >= BOARD_SIZE.width / BLOCK_SIZE.width or \
                    surrounding_coord[0] < 0 or \
                    surrounding_coord[1] >= BOARD_SIZE.height / BLOCK_SIZE.height or \
                    surrounding_coord[1] < 0:
                continue
            surrounding_coords.append(surrounding_coord)
        return surrounding_coords

    def __add_ores(self, matrix):
        """
        Fill a matrix with names of the materials of the respective blocks

        :return: a matrix containing strings corresponding to names of __material
        classes.
        """

        # generate some ores inbetween the start and end locations
        for row_i, row in enumerate(matrix):
            ore_likelyhoods = self.__get_material_lh_at_depth(materials.ore_materials, row_i)
            for column_i, value in enumerate(row):
                if randint(1, self.CLUSTER_LIKELYHOOD) == 1:
                    # decide the ore
                    ore = choices([f.name() for f in materials.ore_materials], ore_likelyhoods, k=1)[0]
                    # create a list of locations around the current location
                    # where an ore is going to be located
                    ore_locations = self.__create_ore_cluster(ore, (column_i, row_i))
                    for loc in ore_locations:
                        try:
                            matrix[loc[1]][loc[0]] = ore
                        except IndexError:
                            # if outside board skip
                            continue
        return matrix

    def __get_material_lh_at_depth(self, material_list, depth):
        """
        Figure out the likelyood of all ores and return a wheighted randomly
        chosen ore

        :param depth: the depth for the ore to be at
        :return: a string that is an ore
        """
        likelyhoods = []
        for material in material_list:
            norm_depth = depth / MAX_DEPTH * 100
            lh = Gaussian(material.MEAN_DEPTH, material.SD).probability(norm_depth)
            likelyhoods.append(round(lh, 10))
        norm_likelyhoods = normalize(likelyhoods)

        return norm_likelyhoods

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
            location = [0, 0]
            for index in range(2):
                pos = choice([-1, 1])
                # assert index is bigger then 0
                location[index] = max(0, pos * randint(0, self.MAX_CLUSTER_SIZE) + center[index])
            if location not in ore_locations:
                ore_locations.append(location)
        return ore_locations

    def __add_border(self, matrix):
        #north border
        rows = matrix[0:self.MAX_SPREAD_DISTANCE]
        for row_i in range(len(rows)):
            border_block_chance = self.SPREAD_LIKELYHOOD.cumulative_probability(row_i)
            for col_i in range(len(matrix[row_i])):
                if uniform(0, 1) < border_block_chance:
                    matrix[row_i][col_i] = "BorderMaterial"
        #south border
        rows = matrix[- (self.MAX_SPREAD_DISTANCE + 1):-1]
        for row_i in range(len(rows)):
            border_block_chance = self.SPREAD_LIKELYHOOD.cumulative_probability(row_i)
            for col_i in range(len(matrix[row_i])):
                if uniform(0, 1) < border_block_chance:
                    matrix[-(row_i + 1)][- (col_i + 1)] = "BorderMaterial"
        #east border
        for row_i in range(len(matrix)):
            for col_i in range(len(matrix[row_i][0:self.MAX_SPREAD_DISTANCE])):
                border_block_chance = self.SPREAD_LIKELYHOOD.cumulative_probability(col_i)
                if uniform(0, 1) < border_block_chance:
                    matrix[row_i][col_i] = "BorderMaterial"
        #west border
        for row_i in range(len(matrix)):
            for col_i in range(len(matrix[row_i][- (self.MAX_SPREAD_DISTANCE + 1):-1])):
                border_block_chance = self.SPREAD_LIKELYHOOD.cumulative_probability(col_i)
                if uniform(0, 1) < border_block_chance:
                    matrix[- (row_i + 1)][ - (col_i + 1)] = "BorderMaterial"

        return matrix

    def __generate_background_string_matrix(self):
        """
        Generate the backdrop matrix.

        :return: a matrix of the given size
        """
        matrix = []
        for _ in range(p_to_r(BOARD_SIZE.height)):
            row = ["Dirt"] * p_to_c(BOARD_SIZE.width)
            matrix.append(row)
        return matrix

    def __add_starter_buildings(self):
        """
        Add all starter building that should be placed before the game starts
        """
        start_chunk = self.get_start_chunk()
        appropriate_location = pygame.Vector2(int(start_chunk.START_RECTANGLE.centerx / BLOCK_SIZE.width) * BLOCK_SIZE.width + start_chunk.rect.left,
                                              + start_chunk.START_RECTANGLE.bottom - BLOCK_SIZE.height + + start_chunk.rect.top)
        t = Terminal(appropriate_location + (60, -10), self.main_sprite_group)
        c = Factory(appropriate_location + (40, -10), self.main_sprite_group)
        f = Furnace(appropriate_location + (20, -10), self.main_sprite_group)
        self.add_building(t)
        self.add_building(c)
        self.add_building(f)
