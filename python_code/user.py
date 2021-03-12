import pygame

import tasks
import utility.constants as con
import entities
import utility.event_handling
import interfaces.small_interfaces as small_interface
import interfaces.interface_utility as interface_util
import utility.utilities as util
from block_classes import buildings, environment_materials


class User(utility.event_handling.EventHandler):
    """The director of a game, assigning tasks to workers and directing interaction between workers the board and the
    tkas management"""
    def __init__(self, board, progress_var, sprite_group):
        super().__init__(recordable_keys=[1, 2, 3, 4, con.MINING, con.CANCEL, con.BUILDING, con.SELECTING])
        self.board = board
        self.__sprite_group = sprite_group
        self.task_control = None
        self.selection_rectangle = None
        self.__highlight_rectangle = None
        self.__init_task_control(progress_var)

        self.workers = []
        self.__init_workers(progress_var)

        self._mode = con.MODES[con.SELECTING]

    def __init_task_control(self, progress_var):
        # tasks
        progress_var[0] = "Making tasks..."
        self.task_control = tasks.TaskControl(self.board)

    def __init_workers(self, progress_var):
        progress_var[0] = "Populating with miners..."
        start_chunk = self.board.get_start_chunk()
        appropriate_location = \
            (int(start_chunk.START_RECTANGLE.centerx / con.BLOCK_SIZE.width) * con.BLOCK_SIZE.width +
             start_chunk.rect.left, + start_chunk.START_RECTANGLE.bottom - con.BLOCK_SIZE.height + start_chunk.rect.top)
        for _ in range(con.STARTING_ENTITIES):
            new_worker = entities.Worker(appropriate_location, self.__sprite_group, board=self.board,
                                         task_control=self.task_control)
            self.workers.append(new_worker)

    def handle_events(self, events, consume_events=True):
        leftover_events = super().handle_events(events, consume_events=consume_events)
        self._handle_mouse_events()
        self.__handle_mode_events()
        return leftover_events

    def __handle_mode_events(self):
        pressed_modes = self.get_all_pressed()
        if len(pressed_modes):
            # make sure to clear the board of any remnants before switching
            if pressed_modes[0].name in con.MODES:
                self.reset_highlight_rectangle(self._mode.persistent_highlight)
                self._mode = con.MODES[pressed_modes[0].name]
                # TODO add this into the gui somewhere best way might be with a text entity
                print(self._mode.name)

    def _handle_mouse_events(self):
        """
        Handle mouse events issued by the user.
        """
        # mousebutton1
        if self.pressed(1):
            if self._mode.name in ["Mining", "Cancel", "Selecting"]:
                keep = False
                if self._mode.name == "Mining":
                    keep = True
                self.reset_highlight_rectangle(keep)
                self.add_selection_rectangle(self.get_key(1).event.pos, self._mode.persistent_highlight)

            elif self._mode.name == "Building":
                item = small_interface.get_selected_item()
                # if no item is selected dont do anything
                if item is None:
                    return
                material = small_interface.get_selected_item().material
                building_block_i = material.block_type
                self.add_building_rectangle(self.get_key(1).event.pos, size=building_block_i.SIZE)
        elif self.unpressed(1):
            if self._mode.name == "Selecting":
                # bit retarded
                zoom = self.board.get_start_chunk().layers[0]._zoom
                board_coord = interface_util.screen_to_board_coordinate(self.get_key(1).event.pos,
                                                                        self.__sprite_group.target, zoom)
                chunk = self.board.chunk_from_point(board_coord)
                if chunk is None:
                    return
                chunk.get_block(board_coord).action()
            self.__process_selection()
            self.remove_selection_rectangle()

# TASK SELECTION HANDLING
    def __process_selection(self):
        """Take all the blocks in a given rectangle and assign tasks based on the given mode"""
        if self.selection_rectangle is None:
            return
        chunks_rectangles = self.board.get_chunks_from_rect(self.selection_rectangle.orig_rect)
        if len(chunks_rectangles) == 0:
            return
        first_chunk = chunks_rectangles[0][0]
        selection_matrix = first_chunk.overlapping_blocks(chunks_rectangles[0][1])
        for chunk, rect in chunks_rectangles[1:]:
            blocks = chunk.overlapping_blocks(rect)
            # extending horizontal
            if chunk.coord[0] > first_chunk.coord[0]:
                extra_rows = len(selection_matrix) - len(blocks)
                for row_i, row in enumerate(blocks):
                    selection_matrix[extra_rows + row_i].extend(row)
            # extending vertical
            else:
                for row_i, row in enumerate(blocks):
                    selection_matrix.append(row)

        if len(selection_matrix) > 0:
            self.__assign_tasks(selection_matrix)

    def add_selection_rectangle(self, pos, keep=False):
        # bit retarded
        zoom = self.board.get_start_chunk().layers[0]._zoom
        mouse_pos = interface_util.screen_to_board_coordinate(pos, self.__sprite_group.target, zoom)
        # should the highlighted area stay when a new one is selected
        if not keep and self.__highlight_rectangle:
            self.board.add_rectangle(self.__highlight_rectangle.rect, con.INVISIBLE_COLOR, layer=1)
        self.selection_rectangle = entities.SelectionRectangle(mouse_pos, (0, 0), pos,
                                                               self.__sprite_group, zoom=zoom)

    def add_highlight_rectangle(self, rect, color):
        self.__highlight_rectangle = rect
        self.board.add_rectangle(rect, color, layer=1)

    def remove_selection_rectangle(self):
        """
        Safely remove the selection rectangle
        """
        if self.selection_rectangle:
            self.selection_rectangle.kill()
            self.selection_rectangle = None

    def add_building_rectangle(self, pos, size=(10, 10)):
        # bit retarded
        zoom = self.board.get_start_chunk().layers[0]._zoom
        mouse_pos = interface_util.screen_to_board_coordinate(pos, self.__sprite_group.target, zoom)
        self.selection_rectangle = entities.ZoomableEntity(mouse_pos, size - con.BLOCK_SIZE,
                                                           self.__sprite_group, zoom=zoom, color=con.INVISIBLE_COLOR)

    def reset_highlight_rectangle(self, keep):
        # remove the selection rectangle holding the highlight and remove the highlight if requested
        if not keep and self.__highlight_rectangle:
            self.board.add_rectangle(self.__highlight_rectangle, con.INVISIBLE_COLOR, layer=1)
        self.__highlight_rectangle = None
        self.remove_selection_rectangle()

    def _get_task_rectangles(self, blocks, task_type=None, dissallowed_block_types=[]):
        """
        Get all spaces of a certain block type, task or both

        :param blocks: a matrix of block_classes
        :return: a list of rectangles
        """
        rectangles = []
        approved_blocks = []

        # save covered coordinates in a same lenght matrix for faster checking
        covered_coordinates = [[] for row in blocks]

        # find all rectangles in the block matrix
        for n_row, row in enumerate(blocks):
            for n_col, block in enumerate(row):
                if block.is_task_allowded(task_type) and (block.name() not in dissallowed_block_types and
                                                          block.light_level > 0) or n_col in covered_coordinates[n_row]:
                    if n_col not in covered_coordinates[n_row]:
                        approved_blocks.append(block)
                    continue

                # calculate the maximum lenght of a rectangle based on already
                # established ones
                end_n_col = n_col
                for n in range(n_col, len(row)):
                    end_n_col = n
                    if end_n_col in covered_coordinates[n_row]:
                        break

                # find all air rectangles in a sub matrix
                sub_matrix = [sub_row[n_col:end_n_col] for sub_row in blocks[n_row:]]
                lm_coord = self.__find_task_rectangle(sub_matrix, task_type, dissallowed_block_types)

                # add newly covered coordinates
                for x in range(lm_coord[0]+ 1):
                    for y in range(lm_coord[1] + 1):
                        covered_coordinates[n_row + y].append(n_col + x)

                # add the air rectangle to the list of rectangles
                air_matrix = [sub_row[n_col:n_col + lm_coord[0] + 1] for sub_row in
                              blocks[n_row:n_row + lm_coord[1] + 1]]
                rect = util.rect_from_block_matrix(air_matrix)
                rectangles.append(rect)
        return rectangles, approved_blocks

    def __find_task_rectangle(self, blocks, task_type, dissallowed_block_types):

        # first find how far the column is filled cannot fill on 0 since 0 is guaranteed to be a air block
        x_size = 0
        for block in blocks[0][1:]:
            if block.is_task_allowded(task_type) and (block.name() not in dissallowed_block_types and
                                                      block.light_level > 0):
                break
            x_size += 1
        matrix_coordinate = [x_size, 0]

        # skip the first row since this was checked already
        block = None
        for n_row, row in enumerate(blocks[1:]):
            for n_col, block in enumerate(row[:x_size + 1]):
                if block.is_task_allowded(task_type) and (block.name() not in dissallowed_block_types):
                    break
            if block is None or block.is_task_allowded(task_type) and (block.name() not in dissallowed_block_types):
                break
            matrix_coordinate[1] += 1
        return matrix_coordinate

    def __assign_tasks(self, blocks):
        rect = util.rect_from_block_matrix(blocks)

        # remove all tasks present
        for row in blocks:
            for block in row:
                self.task_control.cancel_tasks(block, remove=True)

        # select the full area
        self.add_highlight_rectangle(rect, self._mode.color)

        # assign tasks to all block_classes elligable
        if self._mode.name == "Building":
            no_highlight_block = small_interface.get_selected_item().name()
            no_task_rectangles, approved_blocks = self._get_task_rectangles(blocks, self._mode.name,
                                                                            [no_highlight_block])
            # if not the full image was selected dont add tasks
            if len(no_task_rectangles) > 0:
                self.board.add_rectangle(rect, con.INVISIBLE_COLOR, layer=1)
                return
            # make sure the plant is allowed to grow at the given place
            if isinstance(small_interface.get_selected_item().material, environment_materials.MultiFloraMaterial) and \
                    not self.board.can_add_flora(block, small_interface.get_selected_item().material):
                self.board.add_rectangle(rect, con.INVISIBLE_COLOR, layer=1)
                return
            # the first block of the selection is the start block of the material
            approved_blocks = [blocks[0][0]]
        elif self._mode.name == "Cancel":
            # remove highlight
            self.board.add_rectangle(rect, con.INVISIBLE_COLOR, layer=1)
            return
        else:
            no_task_rectangles, approved_blocks = self._get_task_rectangles(blocks, self._mode.name)

        for rect in no_task_rectangles:
            self.board.add_rectangle(rect, con.INVISIBLE_COLOR, layer=1)
        self.__add_tasks(approved_blocks)

    def __add_tasks(self, blocks):
        """
        Add tasks of the _mode.name type, tasks are added to the task control
        when they need to be assigned to workers or directly resolved otherwise

        :param blocks: a list of block_classes
        """
        if self._mode.name == "Mining":
            self.task_control.add(self._mode.name, *blocks)
        elif self._mode.name == "Building":
            # this should always be 1 block
            block = blocks[0]
            material = small_interface.get_selected_item().material
            building_block_i = material.block_type
            group = block.transparant_group
            if group != 0:
                block.transparant_group = util.unique_id()
                chunk = self.board.chunk_from_point(block.coord)
                chunk.update_blocks(block)
            if issubclass(building_block_i, buildings.InterfaceBuilding):
                finish_block = building_block_i(block.rect.topleft, self.__sprite_group, material=material)
            else:
                finish_block = building_block_i(block.rect.topleft, material=material)
            if isinstance(finish_block, buildings.Building):
                overlap_rect = pygame.Rect((finish_block.rect.top, finish_block.rect.left, finish_block.rect.width - 1,
                                            finish_block.rect.height - 1))
                overlap_blocks = self.board.get_blocks_from_rect(overlap_rect)
            else:
                overlap_blocks = [block]
            self.task_control.add(self._mode.name, block, finish_block = finish_block, original_group=group,
                                  removed_blocks=overlap_blocks)


