from random import uniform
from math import sin, cos

import block_classes.building_materials
from utility.utilities import *
from board.pathfinding import PathFinder
import block_classes.buildings as buildings
from block_classes.buildings import *
from utility.event_handling import BoardEventHandler
from interfaces.small_interfaces import get_selected_item
from network.pipes import Network
from interfaces.interface_utility import *
from board.chunks import *
from entities import SelectionRectangle


class Board(BoardEventHandler, Serializer):

    # ORE cluster values
    # the amount of normal block_classes per cluster
    CLUSTER_LIKELYHOOD = 120
    # the max size of a ore cluster around the center
    MAX_CLUSTER_SIZE = 3

    # CAVE values
    MAX_CAVES = int((CHUNK_GRID_SIZE.width * CHUNK_GRID_SIZE.height) / 6)
    # the fraction of the distance between points based on the shortest side of the board
    POINT_FRACTION_DISTANCE = 0.35
    # distance the center of the cave should at least be away from the border
    CAVE_X_BORDER_DISTANCE = int(0.1 * BOARD_SIZE.width)
    CAVE_Y_BORDER_DISTANCE = int(0.1 * BOARD_SIZE.height)
    NUMBER_OF_CAVE_POINTS = int(CHUNK_GRID_SIZE.width * CHUNK_GRID_SIZE.height * 1.3)
    # the chance for a cave to stop extending around its core. Do not go lower then 0.0001 --> takes a long time
    CAVE_STOP_SPREAD_CHANCE = 0.05

    # BORDER values
    SPREAD_LIKELYHOOD = Gaussian(0, 2)
    MAX_SPREAD_DISTANCE = 4

    # PLANT values
    FLORA_CHANCE = 0.1
    START_RECTANGLE = pygame.Rect((BOARD_SIZE.width / 2 - 125, 0, 250, 50))
    BLOCK_PER_CLUSRTER = 500

    def __init__(self, main_sprite_group, chunk_matrix=None, pipe_network=None, grow_update_time=0):
        BoardEventHandler.__init__(self, [1, 2, 3, 4, MINING, CANCEL, BUILDING, SELECTING])
        self.inventorie_blocks = []
        self.main_sprite_group = main_sprite_group

        # setup the board
        self.pf = PathFinder()

        self.chunk_matrix = chunk_matrix if chunk_matrix else self.__generate_chunk_matrix(main_sprite_group)

        self.task_control = None

        # the current SelectionRectangle object that shows
        self.selection_rectangle = None
        # last placed highlighted rectangle
        self.__highlight_rectangle = None

        # pipe network
        self.pipe_network = Network(self.task_control)

        self.__buildings = {}
        self.__grow_update_time = grow_update_time

    def setup_board(self):
        self.__add_starter_buildings()
        for _ in range(10):
            self.__grow_flora()

        self.changed_light_blocks = set()

    def update_board(self):

        #update lighting
        self.change_light_levels()
        self.changed_light_blocks = set()

        #update network
        self.pipe_network.update()

        #update pathfinding
        self.pf.update()

        #grow cycle updates
        self.__grow_update_time += GAME_TIME.get_time()
        if self.__grow_update_time > GROW_CYCLE_UPDATE_TIME:
            self.__grow_flora()
            self.__grow_update_time = 0

    def to_dict(self):
        return {
            "chunk_matrix": [chunk.to_dict() for row in self.chunk_matrix for chunk in row],
            "pipe_coordinates": self.pipe_network.pipe_coordinates(),
            "buildings": [building.to_dict() for building in self.__buildings.values()],
            "grow_update_time": self.__grow_update_time
        }

    @classmethod
    def from_dict(cls, sprite_group=None, **arguments):
        arguments["chunk_matrix"] = [Chunk.from_dict(sprite_group=sprite_group, **kwargs) for row in arguments["chunk_matrix"] for kwargs in row]
        pipe_coords = arguments["pipe_coordinates"]
        builds = arguments.pop("buildings")
        inst = super().from_dict(**arguments)
        building_objects = [getattr(buildings, dct["type"]).from_dict(**dct) for dct in builds]
        [inst.add_building(build) for build in building_objects]
        # add the network blocks back
        inst.add_blocks(*[NetworkBlock(pos, getattr(block_classes.building_materials, type_)) for pos, type in pipe_coords])

    def __grow_flora(self):
        for row in self.chunk_matrix:
            for chunk in row:
                for plant in chunk.plants.values():
                    if plant.can_grow() and uniform(0,1) < plant.material.GROW_CHANCE:
                        new_blocks = plant.grow(self.surrounding_blocks(plant.grow_block))
                        if new_blocks != None:
                            self.add_blocks(*new_blocks)

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
        Calculate the surrounding block_classes of a certain block in the order
        NESW and None if there is no block (edge of the playing field).

        :param block: the center Block Object for the surrounding block_classes
        :param matrix: the matrix that contains the surrounding block_classes
        :return: 4 Block or None objects
        """
        blocks = [None for _ in range(4)]
        for index, new_position in enumerate([(0, -1), (1, 0), (0, 1), (-1, 0)]):
            surrounding_pos = (block.rect.x + new_position[0] * BLOCK_SIZE.width, block.rect.y + new_position[1] * BLOCK_SIZE.height)
            # Make sure within range
            if surrounding_pos[0] > BOARD_SIZE.width or \
                surrounding_pos[0] < 0 or \
                surrounding_pos[1] > BOARD_SIZE.height or \
                surrounding_pos[1] < 0:
                continue
            chunk = self.__chunk_from_point(surrounding_pos)
            surrounding_block = chunk.get_block(surrounding_pos)
            blocks[index] = surrounding_block
        return blocks

    def surrounding_chunks(self, chunk):
        chunks = [None for _ in range(4)]
        for index, new_position in enumerate([(0, -1), (1, 0), (0, 1), (-1, 0)]):
            surrounding_pos = (chunk.rect.x + new_position[0] * CHUNK_SIZE.width, chunk.rect.y + new_position[1] * CHUNK_SIZE.height)
            # Make sure within range
            if surrounding_pos[0] > BOARD_SIZE.width or \
                surrounding_pos[0] < 0 or \
                surrounding_pos[1] > BOARD_SIZE.height or \
                surrounding_pos[1] < 0:
                continue
            surrounding_chunk = self.__chunk_from_point(surrounding_pos)
            chunks[index] = surrounding_chunk
        return chunks

    def remove_blocks(self, *blocks):
        removed_items = []
        for block in blocks:
            if block.id in self.__buildings:
                removed_items.append(self.remove_building(block))
            elif isinstance(block.material, block_classes.flora_materials.MultiFloraMaterial):
                removed_items.extend(self.remove_plant(block))
            else:
                chunk = self.__chunk_from_point(block.rect.topleft)
                removed_items.extend(chunk.remove_blocks(block))

            if isinstance(block, NetworkBlock):
                self.pipe_network.remove_pipe(block)
            surrounding_blocks = self.surrounding_blocks(block)
            for index, s_block in enumerate(surrounding_blocks):
                if s_block == None:
                    continue
                elif isinstance(s_block, NetworkBlock) and not isinstance(s_block, ContainerBlock):
                    self.pipe_network.configure_block(s_block, self.surrounding_blocks(s_block), remove=True)
                    self.add_blocks(s_block)
                # check if the block a surrounding plant is attached to is still solid
                elif isinstance(s_block.material, block_classes.flora_materials.FloraMaterial) and \
                        index == s_block.material.CONTINUATION_DIRECTION:
                    removed_items.extend(self.remove_blocks(s_block))
        return removed_items

    def remove_plant(self, block):
        removed_items = []
        chunk = self.__chunk_from_point(block.rect.topleft)
        possible_chunks = self.surrounding_chunks(chunk) + [chunk]
        plant = None
        for chunk in possible_chunks:
            if chunk != None and block.id in chunk.plants:
                plant = chunk.plants[block.id]
        if plant == None:
            return []
        removed_blocks = plant.remove_block(block)

        for block in removed_blocks:
            chunk = self.__chunk_from_point(block.rect.topleft)
            removed_items.extend(chunk.remove_blocks(block))
        if plant._size() == 0:
            chunk.plants.pop(block.id)
        else:
            plant.grow_block.material.image_key = -1
            self.add_blocks(plant.grow_block)
        return removed_items

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
        return Item(block.material, 1)

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

    def adjust_lighting(self, point, radius, point_light):
        #extend in a circle around a center point and assign new light values based on the light point
        point_light = min(point_light, MAX_LIGHT)

        adjusted_blocks = []
        start_block = self.__block_from_point(point)
        if start_block.light_level < point_light:
            start_block.light_level = point_light
            self.changed_light_blocks.add(start_block)
        col_blocks = int(radius / BLOCK_SIZE.width)
        row_blocks = int(radius / BLOCK_SIZE.height)

        row_end_extend = [False, False]
        for row_i in range(row_blocks):
            for row_s_i, sign in enumerate((-1, 1)):
                if row_end_extend[row_s_i]:
                    continue
                if all(row_end_extend):
                    break
                new_block_y = point[1] + sign * row_i * BLOCK_SIZE.height
                next_block = self.__block_from_point((point[0], new_block_y))
                if next_block.light_level < int(point_light - row_i * DECREASE_SPEED):
                    next_block.light_level = int(point_light - row_i * DECREASE_SPEED)
                    self.changed_light_blocks.add(next_block)
                col_end_extend = [False, False]
                for col_i in range(1, col_blocks + 1 - (row_i)):
                    for col_s_i, sign in enumerate((-1, 1)):
                        #positive x direction
                        if col_end_extend[col_s_i]:
                            continue
                        if all(col_end_extend):
                            break
                        new_block_x = point[0] + sign * col_i * BLOCK_SIZE.width
                        next_block = self.__block_from_point((new_block_x, new_block_y))
                        if next_block.light_level < int(point_light - col_i * DECREASE_SPEED - row_i * DECREASE_SPEED):
                            next_block.light_level = int(point_light - col_i * DECREASE_SPEED - row_i * DECREASE_SPEED)
                            self.changed_light_blocks.add(next_block)

    def change_light_levels(self):
        for block in self.changed_light_blocks:
            chunk = self.__chunk_from_point(block.rect.topleft)
            alpha = 255 - block.light_level * int(255 / MAX_LIGHT)
            chunk.add_rectangle(block.rect, (0,0,0, alpha), layer=0)

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

            distance = manhattan_distance(start.center, block.rect.center)
            if distance < shortest_distance:
                shortest_distance = distance
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

    def transparant_collide(self, point):
        chunk = self.__chunk_from_point(point)
        block = chunk.get_block(point)
        if block.transparant_group != 0:
            return True
        return False

    def __chunk_from_point(self, point):
        column, row = p_to_cp(point)
        return self.chunk_matrix[row][column]

    def __block_from_point(self, point):
        chunk = self.__chunk_from_point(point)
        return chunk.get_block(point)

    def add_selection_rectangle(self, pos, keep = False):
        """
        Add a rectangle that shows what the user is currently selecting

        :param pos: the event.pos of the rectangle
        :param keep: if the previous highlight should be kept
        """
        #bit retarded
        zoom = self.chunk_matrix[0][0].layers[0]._zoom
        mouse_pos = screen_to_board_coordinate(pos, self.main_sprite_group.target, zoom)
        # should the highlighted area stay when a new one is selected
        if not keep and self.__highlight_rectangle:
            self.add_rectangle(self.__highlight_rectangle.rect, INVISIBLE_COLOR, layer=1)
        self.selection_rectangle = SelectionRectangle(mouse_pos, (0, 0), pos,
                                                      self.main_sprite_group,zoom=zoom)

    def add_building_rectangle(self, pos, size=(10, 10)):
        # bit retarded
        zoom = self.chunk_matrix[0][0].layers[0]._zoom
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
                zoom = self.chunk_matrix[0][0].layers[0]._zoom
                board_coord = screen_to_board_coordinate(self.get_key(1).event.pos, self.main_sprite_group.target, zoom)
                chunk = self.__chunk_from_point(board_coord)
                chunk.get_block(board_coord).action()
            self.__process_selection()
            self.remove_selection()

    def __process_selection(self):

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
        # the user is selecting block_classes
        if len(selection_matrix) > 0:
            self._assign_tasks(selection_matrix)

    def _get_task_rectangles(self, blocks, task_type=None, dissallowed_block_types=[]):
        """
        Get all spaces of a certain block type, task or both

        :param blocks: a matrix of block_classes
        :return: a list of rectangles
        """
        rectangles = []
        approved_blocks = []

        #save covered coordinates in a same lenght matrix for faster checking
        covered_coordinates = [[] for row in blocks]

        #find all rectangles in the block matrix
        for n_row, row in enumerate(blocks):
            for n_col, block in enumerate(row):
                if block.is_task_allowded(task_type) and (block.name() not in dissallowed_block_types and block.light_level > 0) or n_col in covered_coordinates[n_row]:
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
        Find in a matrix of block_classes all block_classes of a certain task type

        :param blocks: a matrix of block_classes
        :param task_type: the string name of a certain type of task
        :return:
        """
        #first find how far the column is filled cannot fill on 0 since 0 is guaranteed to be a air block
        x_size = 0
        for block in blocks[0][1:]:
            if block.is_task_allowded(task_type) and (block.name() not in dissallowed_block_types and block.light_level > 0):
                break
            x_size += 1
        matrix_coordinate = [x_size, 0]

        #skip the first row since this was checked already
        block = None
        for n_row, row in enumerate(blocks[1:]):
            for n_col, block in enumerate(row[:x_size + 1]):
                if block.is_task_allowded(task_type) and (block.name() not in dissallowed_block_types):
                    break
            if block == None or block.is_task_allowded(task_type) and (block.name() not in dissallowed_block_types):
                break
            matrix_coordinate[1] += 1
        return matrix_coordinate

    def __can_add_flora(self, block, flora):
        sur_blocks = self.surrounding_blocks(block)

        if sur_blocks[flora.CONTINUATION_DIRECTION  - 2] != None and\
                sur_blocks[flora.CONTINUATION_DIRECTION  - 2].transparant_group == 0:
            return True
        return False

    def _assign_tasks(self, blocks):
        rect = rect_from_block_matrix(blocks)

        #remove all tasks present
        for row in blocks:
            for block in row:
                self.task_control.cancel_tasks(block, remove=True)

        #select the full area
        self.add_highlight_rectangle(rect, self._mode.color)

        #assign tasks to all block_classes elligable
        if self._mode.name == "Building":
            no_highlight_block = get_selected_item().name()
            no_task_rectangles, approved_blocks = self._get_task_rectangles(blocks, self._mode.name, [no_highlight_block])
            #if not the full image was selected dont add tasks
            if len(no_task_rectangles) > 0:
                self.add_rectangle(rect, INVISIBLE_COLOR, layer=1)
                return
            #make sure the plant is allowed to grow at the given place
            if isinstance(get_selected_item().material, block_classes.flora_materials.MultiFloraMaterial) and not self.__can_add_flora(block, get_selected_item().material):
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

        :param blocks: a list of block_classes
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
                chunk = self.__chunk_from_point(block.coord)
                chunk.update_blocks(block)
            if issubclass(building_block_i, InterfaceBuilding):
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
        self.__add_flora(matrix)
        return matrix

    def __generate_stone_background(self):
        matrix = []
        for row_i in range(p_to_r(BOARD_SIZE.height)):
            filler_likelyhoods = self.__get_material_lh_at_depth(block_classes.block_utility.filler_materials, row_i)
            row = []
            for _ in range(p_to_c(BOARD_SIZE.width)):
                filler = choices([f.name() for f in block_classes.block_utility.filler_materials], filler_likelyhoods, k=1)[0]
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
                #make all block_classes air on the direct line
                for index in range(len(x_values)):
                    x = int(x_values[index])
                    y = int(y_values[index])
                    matrix[min(y, int(BOARD_SIZE.height / BLOCK_SIZE.height) -1)][min(x, int(BOARD_SIZE.width / BLOCK_SIZE.width) - 1)] = "Air"
                    surrounding_coords = [coord for coord in self.__get_surrounding_block_coords(x, y) if matrix[coord[1]][coord[0]] not in ["Air", None]]
                    #extend the cave around the direct line.
                    while len(surrounding_coords) > 0:
                        if uniform(0, 1) < self.CAVE_STOP_SPREAD_CHANCE:
                            break
                        remove_block = choice(surrounding_coords)
                        surrounding_coords.remove(remove_block)
                        matrix[remove_block[1]][remove_block[0]] = "Air"
                        new_sur_coords = surrounding_coords.extend([coord for coord in self.__get_surrounding_block_coords(*remove_block) if matrix[coord[1]][coord[0]] not in ["Air", None]])
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
        surrounding_coords = [None for _ in range(4)]
        for index, new_position in enumerate([(0, -1), (1, 0), (0, 1), (-1, 0)]):
            surrounding_coord = [x + new_position[0], y + new_position[1]]
            # Make sure within range
            if surrounding_coord[0] >= BOARD_SIZE.width / BLOCK_SIZE.width or \
                    surrounding_coord[0] < 0 or \
                    surrounding_coord[1] >= BOARD_SIZE.height / BLOCK_SIZE.height or \
                    surrounding_coord[1] < 0:
                continue
            surrounding_coords[index] = surrounding_coord
        return surrounding_coords

    def __add_ores(self, matrix):
        """
        Fill a matrix with names of the materials of the respective block_classes

        :return: a matrix containing strings corresponding to names of __material
        classes.
        """

        # generate some ores inbetween the start and end locations
        for row_i, row in enumerate(matrix):
            ore_likelyhoods = self.__get_material_lh_at_depth(block_classes.block_utility.ore_materials, row_i)
            for column_i, value in enumerate(row):
                if randint(1, self.CLUSTER_LIKELYHOOD) == 1:
                    # decide the ore
                    ore = choices([f.name() for f in block_classes.block_utility.ore_materials], ore_likelyhoods, k=1)[0]
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
        likelyhoods = []
        for material in material_list:
            lh = material.get_lh_at_depth(depth)
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
        size = getattr(block_classes.ground_materials, ore).get_cluster_size()
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

    def __add_flora(self, matrix):
        for row_i in range(len(matrix)):
            flora_likelyhoods = [self.__get_material_lh_at_depth([m for m in block_classes.block_utility.flora_materials if m.START_DIRECTION == 0], row_i),
                                 self.__get_material_lh_at_depth([m for m in block_classes.block_utility.flora_materials if m.START_DIRECTION == 1], row_i),
                                 self.__get_material_lh_at_depth([m for m in block_classes.block_utility.flora_materials if m.START_DIRECTION == 2], row_i),
                                 self.__get_material_lh_at_depth([m for m in block_classes.block_utility.flora_materials if m.START_DIRECTION == 3], row_i)]
            for col_i, string in enumerate(matrix[row_i]):
                if string != "Air":
                    continue
                s_coords = self.__get_surrounding_block_coords(col_i, row_i)
                elligable_indexes = [coord for coord in s_coords if matrix[coord[1]][coord[0]] in [m.name() for m in block_classes.block_utility.filler_materials]]
                if len(elligable_indexes) == 0 or uniform(0, 1) >= self.FLORA_CHANCE:
                    continue
                chosen_index = s_coords.index(choice(elligable_indexes))
                if len(flora_likelyhoods[chosen_index]) == 0:
                    continue
                flora = choices([m for m in block_classes.block_utility.flora_materials if m.START_DIRECTION == chosen_index], flora_likelyhoods[chosen_index], k=1)
                matrix[row_i][col_i] = flora[0].name()

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
