import pygame
from typing import Union, List, Tuple, TYPE_CHECKING, Type, Dict, Any

import tasks
import entities
import interfaces.other_interfaces as small_interface
import interfaces.interface_utility as interface_util
from utility import utilities as util, constants as con, event_handling, loading_saving
from block_classes import buildings
from block_classes.materials import building_materials, environment_materials

if TYPE_CHECKING:
    from board.board import Board
    from board.sprite_groups import CameraAwareLayeredUpdates
    from block_classes.blocks import Block


class User(event_handling.EventHandler, loading_saving.Savable):
    """The user of a game, assigning tasks to workers and directing interaction between workers the board and the
    taks management"""

    board: "Board"
    __sprite_group: "CameraAwareLayeredUpdates"
    task_control: Union[tasks.TaskControl, None]
    # rectangle that shows the current selection of the user with his mouse
    selection_rectangle: Union[entities.SelectionRectangle, None]
    # record of the last selected rectangle by selection rectangle for which a highlight was drawn
    __highlight_rectangle: Union[pygame.Rect, None]
    workers: List[entities.Worker]
    _mode: con.ModeConstants
    zoom: float

    def __init__(
        self,
        board: "Board",
        progress_var: List[str],
        sprite_group: "CameraAwareLayeredUpdates"
    ):
        super().__init__(recordable_keys=[1, 2, 3, 4, *con.BOARD_KEYS.all_keys()])
        self.board = board
        self.__sprite_group = sprite_group
        self.task_control = None
        self.selection_rectangle = None
        self.__highlight_rectangle = None
        self.__init_task_control(progress_var)

        self.workers = []
        self.__init_workers(progress_var)

        self._mode = con.MODES[con.BOARD_KEYS.SELECTING]
        self.zoom = 1.0
        self.__rotate = 0  # track the amount of times that the rotate key was pressed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_control": self.task_control.to_dict(),
            "workers": [worker.to_dict() for worker in self.workers],
        }

    def __init_task_control(
        self,
        progress_var: List[str]
    ):
        """Innitialize the task control"""
        # tasks
        progress_var[0] = "Making tasks..."
        self.task_control = tasks.TaskControl(self.board)

    def __init_workers(
        self,
        progress_var: List[str]
    ):
        """Innitialize all the workers"""
        progress_var[0] = "Populating with miners..."
        start_chunk = self.board.get_start_chunk()
        appropriate_location = \
            (int(start_chunk.START_RECTANGLE.centerx / con.BLOCK_SIZE.width) * con.BLOCK_SIZE.width +
             start_chunk.rect.left, + start_chunk.START_RECTANGLE.bottom - con.BLOCK_SIZE.height + start_chunk.rect.top)
        for _ in range(con.STARTING_ENTITIES):
            new_worker = entities.Worker(appropriate_location, self.__sprite_group, board_=self.board,
                                         task_control=self.task_control)
            self.workers.append(new_worker)

    def handle_events(
        self,
        events: List[pygame.event.Event],
        consume_events: bool = True
    ) -> List[pygame.event.Event]:
        """Handle mouse and mode events separately"""
        leftover_events = super().handle_events(events, consume_events=consume_events)
        self.__handle_mouse_events()
        self.__handle_key_events()
        return leftover_events

    def __handle_key_events(self):
        pressed_keys = self.get_all_pressed()
        for key in pressed_keys:
            if key.name in con.MODES:
                if not self._mode.persistent_highlight:
                    self.__remove_highlight_rectangle()
                self._mode = con.MODES[key.name]
                board_coord = interface_util.screen_to_board_coordinate(con.SCREEN_SIZE.center,
                                                                        self.__sprite_group.target, self.zoom)
                entities.TextSprite(board_coord, self._mode.name, self.__sprite_group)
            elif key.name == con.BOARD_KEYS.ROTATING and self._mode.name == "Building":
                self.__rotate += 1

    def __handle_mouse_events(self):
        """Handle mouse events issued by the user."""
        # mousebutton1
        if self.pressed(1):
            if self._mode.name in ["Mining", "Cancel", "Selecting"]:
                if not self._mode.persistent_highlight:
                    self.__remove_highlight_rectangle()
                self.add_selection_rectangle(self.get_key(1).event.pos, self._mode.persistent_highlight)
        elif self.unpressed(1):
            if self._mode.name == "Selecting":
                board_coord = interface_util.screen_to_board_coordinate(self.get_key(1).event.pos,
                                                                        self.__sprite_group.target, self.zoom)
                for worker in self.workers:
                    if worker.orig_rect.collidepoint(*board_coord):
                        worker.open_interface()
                        self.__remove_selection_rectangle()
                        return
                chunk = self.board.chunk_from_point(board_coord)
                if chunk is None:
                    return
                chunk.get_block(board_coord).action()
                self.__remove_selection_rectangle()
            elif self._mode.name == "Building":
                item = small_interface.get_selected_item()
                # if no item is selected dont do anything
                if item is None:
                    return

                building_block_class = self.get_building_block_class()

                mouse_pos = interface_util.screen_to_board_coordinate(self.get_key(1).event.pos,
                                                                      self.__sprite_group.target, self.zoom)
                mouse_pos[0] = int(mouse_pos[0] / con.BLOCK_SIZE.width) * con.BLOCK_SIZE.width
                mouse_pos[1] = int(mouse_pos[1] / con.BLOCK_SIZE.height) * con.BLOCK_SIZE.height
                rectangle = pygame.Rect((mouse_pos[0], mouse_pos[1], building_block_class.size().width - 1,
                                         building_block_class.size().height - 1))
                self.__process_selection(rectangle)
            else:
                rectangle = self.selection_rectangle.orig_rect
                self.__process_selection(rectangle)
                self.__remove_selection_rectangle()

    def get_building_block_class(self) -> Union[Type["Block"], Type[buildings.InterfaceBuilding]]:
        material = small_interface.get_selected_item().material
        if isinstance(material, building_materials.Building):
            # this is fine because building is the abstract class that all buildings have
            building_block_class = buildings.material_mapping[material.name()]  # noqa
        else:
            building_block_class = material.block_type
        return building_block_class

    def add_selection_rectangle(
        self,
        pos: Union[Tuple[int, int], List[int]],
        keep: bool = False
    ):
        """Add a entities.SelectionRectangle to the board and remove highlight from a previous selection if requested"""
        self.__remove_selection_rectangle()
        mouse_pos = interface_util.screen_to_board_coordinate(pos, self.__sprite_group.target, self.zoom)
        # should the highlighted area stay when a new one is selected
        if not keep and self.__highlight_rectangle:
            self.board.add_rectangle(self.__highlight_rectangle, con.INVISIBLE_COLOR, layer=1)
        self.selection_rectangle = entities.SelectionRectangle(mouse_pos, (0, 0), pos, self.__sprite_group,
                                                               zoom=self.zoom)

    def __remove_selection_rectangle(self):
        """Safely remove the selection rectangle"""
        if self.selection_rectangle:
            self.selection_rectangle.kill()
            self.selection_rectangle = None

    def __add_highlight_rectangle(
        self,
        rect: pygame.Rect,
        color: Union[Tuple[int, int, int], Tuple[int, int, int, int], List[int]]
    ):
        """Assign the __highlight_rectangle to rect and draw on the board on layer 1 (highlight layer)"""
        self.__highlight_rectangle = rect
        self.board.add_rectangle(rect, color, layer=1)

    def __remove_highlight_rectangle(self):
        # remove the selection rectangle holding the highlight and remove the highlight if requested
        if self.__highlight_rectangle is not None:
            self.board.add_rectangle(self.__highlight_rectangle, con.INVISIBLE_COLOR, layer=1)
            self.__highlight_rectangle = None

    # TASK SELECTION HANDLING
    def __process_selection(
        self,
        rect: pygame.Rect
    ):
        """Take all the blocks in a given rectangle and assign tasks based on the given mode"""
        chunks_rectangles = self.board.get_chunks_from_rect(rect)
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

    def __assign_tasks(
        self,
        blocks: List[List["Block"]]
    ):
        rect = util.rect_from_block_matrix(blocks)
        self.__remove_all_tasks(blocks)

        # select the full area
        self.__add_highlight_rectangle(rect, self._mode.color)
        if self._mode.name == "Cancel":
            return

        # assign tasks to all block_classes elligable
        if self._mode.name == "Building":
            # make sure to not build on blocks that are already the given material
            no_highlight_block = small_interface.get_selected_item().name()
            no_task_rectangles, approved_blocks = self.__get_task_blocks(blocks, [no_highlight_block])
            # if not the full image was selected dont add tasks
            if len(no_task_rectangles) > 0:
                self.board.add_rectangle(rect, con.INVISIBLE_COLOR, layer=1)
                return
            # make sure the plant is allowed to grow at the given place
            if isinstance(small_interface.get_selected_item().material, environment_materials.MultiFloraMaterial) and \
                    not self.board.can_add_flora(blocks[0][0], small_interface.get_selected_item().material):
                self.board.add_rectangle(rect, con.INVISIBLE_COLOR, layer=1)
                return
            # the first block of the selection is the start block of the material
            approved_blocks = [blocks[0][0]]
        else:
            no_task_rectangles, approved_blocks = self.__get_task_blocks(blocks)

        for rect in no_task_rectangles:
            self.board.add_rectangle(rect, con.INVISIBLE_COLOR, layer=1)
        self.__add_tasks(approved_blocks)

    def __remove_all_tasks(
        self,
        blocks: List[List["Block"]]
    ):
        # remove all tasks present
        for row in blocks:
            for block in row:
                self.task_control.cancel_tasks(block, remove=True)

    def __get_task_blocks(
        self,
        blocks: List[List["Block"]],
        dissallowed_block_types: List[str] = None
    ) -> Tuple[List[pygame.Rect], List["Block"]]:
        """Get all bocks that can have the assigned task and all rectangles that cannot. This seems a bit strange
        but the drawing is improved quite allot with this system."""
        dissallowed_block_types = dissallowed_block_types if dissallowed_block_types else []
        no_task_rectangles = []  # all the rectangles the task cannot be performed at --> returned for more efficiency
        approved_blocks = []

        # save covered coordinates in a same lenght matrix for faster checking
        covered_coordinates = [[False for _ in row] for row in blocks]

        for n_row, row in enumerate(blocks):
            for n_col, block in enumerate(row):
                # select everything were the block task is allowed and the lighting allows it
                if block.is_task_allowded(self._mode.name) and \
                        block.name() not in dissallowed_block_types and\
                        block.light_level > 0:
                    approved_blocks.append(block)
                    continue
                elif covered_coordinates[n_row][n_col] is True:
                    continue

                # calculate the maximum lenght of a rectangle based on already established ones
                end_n_col = n_col
                for n in range(n_col, len(row)):
                    end_n_col = n
                    if covered_coordinates[n_row][end_n_col] is True:
                        break

                # find all air rectangles
                sub_matrix = [sub_row[n_col:end_n_col] for sub_row in blocks[n_row:]]
                no_task_matrix_size = self.__find_no_task_rectangle(sub_matrix, dissallowed_block_types)

                # add newly covered coordinates
                for x in range(no_task_matrix_size.width + 1):
                    for y in range(no_task_matrix_size.height + 1):
                        covered_coordinates[n_row + y][n_col + x] = True

                # add the rectangle to the list of rectangles
                air_matrix = [sub_row[n_col:n_col + no_task_matrix_size[0] + 1] for sub_row in
                              blocks[n_row:n_row + no_task_matrix_size[1] + 1]]
                rect = util.rect_from_block_matrix(air_matrix)
                no_task_rectangles.append(rect)
        return no_task_rectangles, approved_blocks

    def __find_no_task_rectangle(
        self,
        blocks: List[List["Block"]],
        dissallowed_block_types: List[str]
    ) -> util.Size:
        """Find in a given matrix of blocks the submatrix that contains blocks that the task of the selected mode is
        not allowed for. The 0,0 cooridinate is guaranteed to be a block that does not allow the task."""
        # find how far the x-coordinate extends containing blocks that cannot have  the selected task assigned
        x_size = 0
        for block in blocks[0][1:]:
            if block.is_task_allowded(self._mode.name) and\
                    (block.name() not in dissallowed_block_types and block.light_level > 0):
                break
            x_size += 1
        matrix_size = util.Size(x_size, 0)

        # skip the first row since this was checked already in the previous loop
        block = None
        for n_row, row in enumerate(blocks[1:]):
            for n_col, block in enumerate(row[:x_size + 1]):
                if block.is_task_allowded(self._mode.name) and (block.name() not in dissallowed_block_types):
                    break
            if block is None or block.is_task_allowded(self._mode.name) and\
                    (block.name() not in dissallowed_block_types):
                break
            matrix_size.height += 1
        return matrix_size

    def __add_tasks(
        self,
        blocks: List["Block"]
    ):
        """Add tasks of mode._name to all the provided blocks. All the blocks should be allowed to get the given task"""
        if self._mode.name == "Mining":
            self.task_control.add(self._mode.name, *blocks)
        elif self._mode.name == "Building":
            # this should always be 1 block
            block = blocks[0]
            material = small_interface.get_selected_item().material.copy()
            if isinstance(material, building_materials.RotatbleBuildingMaterial):
                material.rotate(self.__rotate)
            building_block_class = self.get_building_block_class()
            group = block.transparant_group
            if group != 0:
                block.transparant_group = util.unique_id()
                chunk = self.board.chunk_from_point(block.coord)
                chunk.update_blocks(block)
            if issubclass(building_block_class, buildings.InterfaceBuilding):
                finish_block = building_block_class(block.rect.topleft, self.__sprite_group)
            else:
                finish_block = building_block_class(block.rect.topleft, material=material)
            if isinstance(finish_block, buildings.Building):
                overlap_rect = pygame.Rect((finish_block.rect.top, finish_block.rect.left, finish_block.rect.width - 1,
                                            finish_block.rect.height - 1))
                overlap_blocks = self.board.get_blocks_from_rect(overlap_rect)
            else:
                overlap_blocks = [block]
            self.task_control.add(self._mode.name, block, finish_block=finish_block, original_group=group,
                                  removed_blocks=overlap_blocks)
