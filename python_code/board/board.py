from random import uniform
import pygame

import utility.utilities as util
import board_generation.generation as generator
import utility.constants as con
import utility.event_handling as event_handling
import block_classes.blocks as block_classes
import block_classes.buildings as buildings
import block_classes.building_materials as build_materials
import block_classes.environment_materials as environment_materials
import board.pathfinding as pathfinding
import network.pipes as network
import interfaces.small_interfaces as small_interface
import interfaces.interface_utility as interface_util
import board.chunks as chunks
import inventories
import entities


class Board(event_handling.BoardEventHandler, util.Serializer):

    START_RECTANGLE = pygame.Rect((con.BOARD_SIZE.width / 2 - 125, 0, 250, 50))
    BLOCK_PER_CLUSRTER = 500

    def __init__(self, main_sprite_group, chunk_matrix=None, pipe_network=None, grow_update_time=0):
        event_handling.BoardEventHandler.__init__(self, [1, 2, 3, 4, con.MINING, con.CANCEL, con.BUILDING, con.SELECTING])
        self.inventorie_blocks = []
        self.main_sprite_group = main_sprite_group

        # setup the board
        self.pf = pathfinding.PathFinder()

        self.chunk_matrix = chunk_matrix if chunk_matrix else self.__generate_chunk_matrix(main_sprite_group)

        self.task_control = None

        # the current SelectionRectangle object that shows
        self.selection_rectangle = None
        # last placed highlighted rectangle
        self.__highlight_rectangle = None

        # pipe network
        self.pipe_network = network.Network(self.task_control)

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
        self.__grow_update_time += con.GAME_TIME.get_time()
        if self.__grow_update_time > con.GROW_CYCLE_UPDATE_TIME:
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
        arguments["chunk_matrix"] = [chunks.Chunk.from_dict(sprite_group=sprite_group, **kwargs) for row in arguments["chunk_matrix"] for kwargs in row]
        pipe_coords = arguments["pipe_coordinates"]
        builds = arguments.pop("buildings")
        inst = super().from_dict(**arguments)
        building_objects = [getattr(buildings, dct["type"]).from_dict(**dct) for dct in builds]
        [inst.add_building(build) for build in building_objects]
        # add the network blocks back
        inst.add_blocks(*[block_classes.NetworkEdgeBlock(pos, getattr(build_materials, type_)) for pos, type_ in pipe_coords])

    def __grow_flora(self):
        for row in self.chunk_matrix:
            for chunk in row:
                if chunk is None:
                    continue
                for plant in chunk.plants.values():
                    if plant.can_grow() and uniform(0,1) < plant.material.GROW_CHANCE:
                        new_blocks = plant.grow(self.surrounding_blocks(plant.grow_block))
                        if new_blocks != None:
                            self.add_blocks(*new_blocks)

    def __generate_chunk_matrix(self, main_sprite_group):
        chunk_matrix = [[None for _ in range(int(con.BOARD_SIZE.width / con.CHUNK_SIZE.width))]
                        for _ in range(int(con.BOARD_SIZE.height / con.CHUNK_SIZE.height))]
        board_generator = generator.BoardGenerator()
        for row_i in con.START_LOAD_AREA[1]:
            for col_i in con.START_LOAD_AREA[0]:
                point_pos = (col_i * con.CHUNK_SIZE.width, row_i * con.CHUNK_SIZE.height)
                for_string_matrix, back_string_matrix = board_generator.generate_chunk(point_pos)
                if (col_i, row_i) == con.START_CHUNK_POS:
                    chunk = chunks.StartChunk(point_pos, for_string_matrix, back_string_matrix, main_sprite_group)
                else:
                    chunk = chunks.Chunk(point_pos, for_string_matrix, back_string_matrix, main_sprite_group)
                chunk_matrix[row_i][col_i] = chunk
                self.pf.pathfinding_tree.add_chunk(chunk.pathfinding_chunk)
        return chunk_matrix

    def get_start_chunk(self):
        return self.chunk_matrix[con.START_CHUNK_POS[1]][con.START_CHUNK_POS[0]]

    def __get_chunks_from_rect(self, rect):
        affected_chunks = []
        tl_column, tl_row = interface_util.p_to_cp(rect.topleft)
        br_column, br_row = interface_util.p_to_cp(rect.bottomright)
        top = rect.top
        for row in range(br_row - tl_row + 1):
            if row == 0:
                height = min(con.CHUNK_SIZE.height - (top % con.CHUNK_SIZE.height), rect.height)
            else:
                height = ((rect.bottom - top) % con.CHUNK_SIZE.height)
            left = rect.left
            for column in range(br_column - tl_column + 1):
                if column == 0:
                    width = min(con.CHUNK_SIZE.width - (left % con.CHUNK_SIZE.width), rect.width)
                else:
                    width = ((rect.right - left) % con.CHUNK_SIZE.width)
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
            for y_coord in range(rect.top, rect.bottom, con.BLOCK_SIZE.height):
                for x_coord in range(rect.left, rect.right, con.BLOCK_SIZE.width):
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
            surrounding_pos = (block.rect.x + new_position[0] * con.BLOCK_SIZE.width, block.rect.y + new_position[1] * con.BLOCK_SIZE.height)
            # Make sure within range
            if surrounding_pos[0] > con.BOARD_SIZE.width or \
                surrounding_pos[0] < 0 or \
                surrounding_pos[1] > con.BOARD_SIZE.height or \
                surrounding_pos[1] < 0:
                continue
            chunk = self.__chunk_from_point(surrounding_pos)
            if chunk:
                surrounding_block = chunk.get_block(surrounding_pos)
                blocks[index] = surrounding_block
        return blocks

    def surrounding_chunks(self, chunk):
        chunks = [None for _ in range(4)]
        for index, new_position in enumerate([(0, -1), (1, 0), (0, 1), (-1, 0)]):
            surrounding_pos = (chunk.rect.x + new_position[0] * con.CHUNK_SIZE.width, chunk.rect.y + new_position[1] * con.CHUNK_SIZE.height)
            # Make sure within range
            if surrounding_pos[0] > con.BOARD_SIZE.width or \
                surrounding_pos[0] < 0 or \
                surrounding_pos[1] > con.BOARD_SIZE.height or \
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
            elif isinstance(block.material, environment_materials.MultiFloraMaterial):
                removed_items.extend(self.remove_plant(block))
            else:
                chunk = self.__chunk_from_point(block.rect.topleft)
                removed_items.extend(chunk.remove_blocks(block))

            if isinstance(block, block_classes.NetworkEdgeBlock):
                self.pipe_network.remove_pipe(block)
            surrounding_blocks = self.surrounding_blocks(block)
            for index, s_block in enumerate(surrounding_blocks):
                if s_block == None:
                    continue
                elif isinstance(s_block, block_classes.NetworkEdgeBlock) and not isinstance(s_block, block_classes.ContainerBlock):
                    self.pipe_network.configure_block(s_block, self.surrounding_blocks(s_block), remove=True)
                    self.add_blocks(s_block)
                # check if the block a surrounding plant is attached to is still solid
                elif isinstance(s_block.material, environment_materials.EnvironmentMaterial) and \
                        index == s_block.material.START_DIRECTION:
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
        if isinstance(block, block_classes.NetworkEdgeBlock):
            self.pipe_network.remove_node(building_instance)
        blocks = building_instance.blocks
        for row in blocks:
            for block in row:
                self.task_control.cancel_tasks(block, remove=True)
                chunk = self.__chunk_from_point(block.rect.topleft)
                chunk.remove_blocks(block)
        return inventories.Item(block.material, 1)

    def add_blocks(self, *blocks, update=False):
        """
        Add a block to the board by changing the matrix and blitting the image
        to the foreground_layer

        :param blocks: one or more BasicBlock objects or inheriting classes
        """
        update_blocks = []
        for block in blocks:
            if isinstance(block, buildings.Building):
                self.add_building(block)
            else:
                if isinstance(block, block_classes.NetworkEdgeBlock):
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
        if isinstance(building_instance, network.NetworkNode):
            self.pipe_network.add_node(building_instance)
        for row in building_instance.blocks:
            for block in row:
                chunk = self.__chunk_from_point(block.coord)
                chunk.add_blocks(block)
                if isinstance(block, block_classes.ContainerBlock):
                    self.inventorie_blocks.append(block)
                    update_blocks.extend(self.pipe_network.configure_block(block, self.surrounding_blocks(block), update=True))
        if len(update_blocks) > 0:
            update_blocks = [block for block in update_blocks if not isinstance(block, block_classes.ContainerBlock)]
            self.add_blocks(*update_blocks)

    def adjust_lighting(self, point, radius, point_light):
        #extend in a circle around a center point and assign new light values based on the light point
        point_light = min(point_light, con.MAX_LIGHT)

        adjusted_blocks = []
        start_block = self.__block_from_point(point)
        if start_block.light_level < point_light:
            start_block.light_level = point_light
            self.changed_light_blocks.add(start_block)
        col_blocks = int(radius / con.BLOCK_SIZE.width)
        row_blocks = int(radius / con.BLOCK_SIZE.height)

        row_end_extend = [False, False]
        for row_i in range(row_blocks):
            for row_s_i, sign in enumerate((-1, 1)):
                if row_end_extend[row_s_i]:
                    continue
                if all(row_end_extend):
                    break
                new_block_y = point[1] + sign * row_i * con.BLOCK_SIZE.height
                next_block = self.__block_from_point((point[0], new_block_y))
                if next_block.light_level < int(point_light - row_i * con.DECREASE_SPEED):
                    next_block.light_level = int(point_light - row_i * con.DECREASE_SPEED)
                    self.changed_light_blocks.add(next_block)
                col_end_extend = [False, False]
                for col_i in range(1, col_blocks + 1 - (row_i)):
                    for col_s_i, sign in enumerate((-1, 1)):
                        #positive x direction
                        if col_end_extend[col_s_i]:
                            continue
                        if all(col_end_extend):
                            break
                        new_block_x = point[0] + sign * col_i * con.BLOCK_SIZE.width
                        next_block = self.__block_from_point((new_block_x, new_block_y))
                        if next_block.light_level < int(point_light - col_i * con.DECREASE_SPEED - row_i * con.DECREASE_SPEED):
                            next_block.light_level = int(point_light - col_i * con.DECREASE_SPEED - row_i * con.DECREASE_SPEED)
                            self.changed_light_blocks.add(next_block)

    def change_light_levels(self):
        for block in self.changed_light_blocks:
            chunk = self.__chunk_from_point(block.rect.topleft)
            alpha = 255 - block.light_level * int(255 / con.MAX_LIGHT)
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

            distance = util.manhattan_distance(start.center, block.rect.center)
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
        column, row = interface_util.p_to_cp(point)
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
        zoom = self.get_start_chunk().layers[0]._zoom
        mouse_pos = interface_util.screen_to_board_coordinate(pos, self.main_sprite_group.target, zoom)
        # should the highlighted area stay when a new one is selected
        if not keep and self.__highlight_rectangle:
            self.add_rectangle(self.__highlight_rectangle.rect, con.INVISIBLE_COLOR, layer=1)
        self.selection_rectangle = entities.SelectionRectangle(mouse_pos, (0, 0), pos,
                                                      self.main_sprite_group,zoom=zoom)

    def add_building_rectangle(self, pos, size=(10, 10)):
        # bit retarded
        zoom = self.get_start_chunk().layers[0]._zoom
        mouse_pos = interface_util.screen_to_board_coordinate(pos, self.main_sprite_group.target, zoom)
        self.selection_rectangle = entities.ZoomableEntity(mouse_pos, size - con.BLOCK_SIZE,
                                                  self.main_sprite_group, zoom=zoom, color=con.INVISIBLE_COLOR)

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
            self.add_rectangle(self.__highlight_rectangle, con.INVISIBLE_COLOR, layer=1)
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
                item = small_interface.get_selected_item()
                # if no item is selected dont do anything
                if item == None:
                    return
                material = small_interface.get_selected_item().material
                building_block_i = material.block_type
                self.add_building_rectangle(self.get_key(1).event.pos, size=building_block_i.SIZE)
        elif self.unpressed(1):
            if self._mode.name == "Selecting":
                # bit retarded
                zoom = self.get_start_chunk().layers[0]._zoom
                board_coord = interface_util.screen_to_board_coordinate(self.get_key(1).event.pos, self.main_sprite_group.target, zoom)
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
                rect = util.rect_from_block_matrix(air_matrix)
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
        rect = util.rect_from_block_matrix(blocks)

        #remove all tasks present
        for row in blocks:
            for block in row:
                self.task_control.cancel_tasks(block, remove=True)

        #select the full area
        self.add_highlight_rectangle(rect, self._mode.color)

        #assign tasks to all block_classes elligable
        if self._mode.name == "Building":
            no_highlight_block = small_interface.get_selected_item().name()
            no_task_rectangles, approved_blocks = self._get_task_rectangles(blocks, self._mode.name, [no_highlight_block])
            #if not the full image was selected dont add tasks
            if len(no_task_rectangles) > 0:
                self.add_rectangle(rect, con.INVISIBLE_COLOR, layer=1)
                return
            #make sure the plant is allowed to grow at the given place
            if isinstance(small_interface.get_selected_item().material, environment_materials.MultiFloraMaterial) and not self.__can_add_flora(block, small_interface.get_selected_item().material):
                self.add_rectangle(rect, con.INVISIBLE_COLOR, layer=1)
                return
            #the first block of the selection is the start block of the material
            approved_blocks = [blocks[0][0]]
        elif self._mode.name == "Cancel":
            # remove highlight
            self.add_rectangle(rect, con.INVISIBLE_COLOR, layer=1)
            return
        else:
            no_task_rectangles, approved_blocks = self._get_task_rectangles(blocks, self._mode.name)

        for rect in no_task_rectangles:
            self.add_rectangle(rect, con.INVISIBLE_COLOR, layer=1)
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
            material = small_interface.get_selected_item().material
            building_block_i = material.block_type
            group = block.transparant_group
            if group != 0:
                block.transparant_group = util.unique_id()
                chunk = self.__chunk_from_point(block.coord)
                chunk.update_blocks(block)
            if issubclass(building_block_i, buildings.InterfaceBuilding):
                finish_block = building_block_i(block.rect.topleft, self.main_sprite_group, material=material)
            else:
                finish_block = building_block_i(block.rect.topleft, material=material)
            if isinstance(finish_block, buildings.Building):
                overlap_rect = pygame.Rect((*finish_block.rect.topleft, finish_block.rect.width - 1, finish_block.rect.height - 1))
                overlap_blocks = self.__get_blocks_from_rect(overlap_rect)
            else:
                overlap_blocks = [block]
            self.task_control.add(self._mode.name, block, finish_block = finish_block, original_group=group, removed_blocks=overlap_blocks)



    def __add_starter_buildings(self):
        """
        Add all starter building that should be placed before the game starts
        """
        start_chunk = self.get_start_chunk()
        appropriate_location = pygame.Vector2(int(start_chunk.START_RECTANGLE.centerx / con.BLOCK_SIZE.width) * con.BLOCK_SIZE.width + start_chunk.rect.left,
                                              + start_chunk.START_RECTANGLE.bottom - con.BLOCK_SIZE.height + + start_chunk.rect.top)
        t = buildings.Terminal(appropriate_location + (60, -10), self.main_sprite_group)
        c = buildings.Factory(appropriate_location + (40, -10), self.main_sprite_group)
        f = buildings.Furnace(appropriate_location + (20, -10), self.main_sprite_group)
        self.add_building(t)
        self.add_building(c)
        self.add_building(f)
