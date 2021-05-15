from random import uniform
import pygame
from math import ceil
from typing import List, Union, Tuple, Dict, Any
from threading import Thread

import block_classes.blocks as block_classes
import block_classes.buildings as buildings
import block_classes.materials.building_materials as build_materials
import block_classes.materials.environment_materials as environment_materials
import interfaces.interface_utility as interface_util
from board import flora, chunks, pathfinding
import network.conveynetwork
from utility import game_timing, loading_saving, utilities as util, constants as con


class Board(loading_saving.Savable, loading_saving.Loadable):

    chunk_matrix: List[List[Union[chunks.Chunk, None]]]

    def __init__(self, board_generator, main_sprite_group, progress_var):
        self.inventorie_blocks = []
        self.main_sprite_group = main_sprite_group

        # setup the board
        progress_var[0] = "Innitialising pathfinding..."
        self.pathfinding = pathfinding.PathFinder()
        self.all_plants = flora.Flora()

        # pipe network
        progress_var[0] = "Innitialising pipe network..."
        self.conveyor_network = network.conveynetwork.ConveyorNetwork()

        self.buildings = {}
        self.variable_blocks = set()
        self.changed_light_blocks = set()

        self.board_generator = board_generator
        self.chunk_matrix = [[None for _ in range(int(con.BOARD_SIZE.width / con.CHUNK_SIZE.width))]
                             for _ in range(int(con.BOARD_SIZE.height / con.CHUNK_SIZE.height))]
        self.loaded_chunks = set()
        # chunks that are currently loading to make sure that no double chunks are generated
        self._loading_chunks = set()
        self.generate_chunks(*con.START_LOAD_AREA, thread_it=False, progress_var=progress_var)

        # last placed highlighted rectangle
        self.__highlight_rectangle = None

        self.__grow_update_time = 0
        self.terminal = None

    def __init_load__(self, board_generator=None, sprite_group=None, chunk_matrix=None, grow_update_time=None,
                      buildings_=None):
        self.inventorie_blocks = []
        self.main_sprite_group = sprite_group

        # setup the board
        self.pathfinding = pathfinding.PathFinder()
        self.all_plants = flora.Flora()

        # pipe network
        self.conveyor_network = network.conveynetwork.ConveyorNetwork()

        self.buildings = buildings_
        self.variable_blocks = set()
        self.changed_light_blocks = set()

        self.board_generator = board_generator
        self.chunk_matrix = chunk_matrix
        self.loaded_chunks = set()
        for row in chunk_matrix:
            for chunk in row:
                if chunk is None:
                    continue
                self.loaded_chunks.add(chunk)
                self.pathfinding.pathfinding_tree.add_chunk(chunk.pathfinding_chunk)
                update_blocks = chunk.get_board_update_blocks()
                self.add_blocks(*update_blocks, update=True)
                self.changed_light_blocks.update(update_blocks)
        # chunks that are currently loading to make sure that no double chunks are generated
        self._loading_chunks = set()

        # last placed highlighted rectangle
        self.__highlight_rectangle = None

        self.__grow_update_time = grow_update_time
        for building in self.buildings.values():
            if isinstance(building, buildings.Terminal):
                self.terminal = building
            self.add_blocks(building)

    def to_dict(self) -> Dict[str, Any]:
        # TODO handle chunks currently being loaded
        return {
            "board_generator": self.board_generator.to_dict(),
            "chunk_matrix": [[chunk.to_dict() if chunk is not None else None for chunk in row]
                             for row in self.chunk_matrix],
            "buildings": {name: building.to_dict() for name, building in self.buildings.items()},
            "grow_update_time": self.__grow_update_time,
            "plants": self.all_plants.to_dict()
        }

    @classmethod
    def from_dict(cls, dct, sprite_group=None):
        from board_generation import generation
        board_generator = generation.BoardGenerator.from_dict(dct["board_generator"])
        plants = flora.Flora.from_dict(dct["plants"])
        chunk_matrix = [[chunks.Chunk.from_dict(chunk_d, sprite_group=sprite_group, plants=plants)
                         if chunk_d is not None else None for chunk_d in row]
                        for row in dct["chunk_matrix"]]
        buildings_ = {name: buildings.Building.from_dict(building_dict, sprite_group=sprite_group)
                      for name, building_dict in dct["buildings"].items()}
        return cls.load(sprite_group=sprite_group, board_generator=board_generator, chunk_matrix=chunk_matrix,
                        buildings_=buildings_, grow_update_time=dct["grow_update_time"])

    def setup_board(self):
        self.__add_starter_buildings()
        for _ in range(10):
            self.update_board()

    def update_board(self):

        self.change_light_levels()
        self.changed_light_blocks = set()

        self.pathfinding.update()

        self.__update_conveyor_network()

        self.__update_plants()

        self.__update_variable_blocks()

        # chunk updates
        for chunk in self.loaded_chunks.copy():
            if not chunk.is_showing():
                continue
            # when the first update happens to a chunk meaning the player is there generate new ones.
            if not chunk.changed[1] and chunk.changed[0]:
                chunk.changed[1] = True
                chunk_coord = interface_util.p_to_cp(chunk.rect.topleft)
                self.generate_chunks(list(range(chunk_coord[0] - 1, chunk_coord[0] + 2)),
                                     list(range(chunk_coord[1] - 1, chunk_coord[1] + 2)))

    @game_timing.time_function("plant update")
    def __update_plants(self):
        self.__grow_update_time += con.GAME_TIME.get_time()
        if self.__grow_update_time < con.GROW_CYCLE_UPDATE_TIME:
            return
        for plant in self.all_plants:
            if plant.can_grow() and uniform(0, 1) < plant.material.GROW_CHANCE:
                new_blocks = plant.grow(self.surrounding_blocks(plant.grow_block))
                if new_blocks is not None:
                    self.add_blocks(*new_blocks)
        self.__grow_update_time = 0

    @game_timing.time_function("conveyor calcluation update")
    def __update_conveyor_network(self):
        for belt in self.conveyor_network:
            belt.update()

    @game_timing.time_function("variable block updates")
    def __update_variable_blocks(self):
        """Check all blocks with varaible surfaces that potentially need to be changed if that is the case redraw the
        surface"""
        # copy is required because of generation potentially adding blocks while looping
        for block in self.variable_blocks.copy():
            if block.changed:
                self.add_blocks(block, update=False)

    def generate_chunks(
        self,
        col_coords_load: List,
        row_coords_load: List,
        thread_it: bool = True,
        progress_var: Union[List[str], None] = None
    ):
        for row_li, row_gi in enumerate(row_coords_load):
            for col_li, col_gi in enumerate(col_coords_load):
                if progress_var:
                    current_chunk = (row_li * len(con.START_LOAD_AREA[1])) + col_li + 1
                    progress_var[0] = f"Generating chunk {current_chunk} out of {con.TOTAL_START_CHUNKS}..."
                # make sure to not generate chunks outside the board
                if row_gi < 0 or row_gi > ceil(con.ORIGINAL_BOARD_SIZE.height / con.CHUNK_SIZE.height) - 1 or \
                        col_gi < 0 or col_gi > ceil(con.ORIGINAL_BOARD_SIZE.width / con.CHUNK_SIZE.width) - 1:
                    continue
                # make sure 2 threads are not working on the same thing
                if self.chunk_matrix[row_gi][col_gi] is not None or (col_gi, row_gi) in self._loading_chunks:
                    continue
                self._loading_chunks.add((col_gi, row_gi))
                if thread_it:
                    Thread(target=self.generate_chunk, args=(row_gi, col_gi)).start()
                else:
                    self.generate_chunk(row_gi, col_gi)

    def generate_chunk(self, row_i, col_i):
        point_pos = (col_i * con.CHUNK_SIZE.width, row_i * con.CHUNK_SIZE.height)
        for_string_matrix, back_string_matrix = self.board_generator.generate_chunk(point_pos)
        if (col_i, row_i) == con.START_CHUNK_POS:
            chunk = chunks.StartChunk(point_pos, for_string_matrix, back_string_matrix, self.main_sprite_group,
                                      self.all_plants, changed=(False, True))
        else:
            chunk = chunks.Chunk(point_pos, for_string_matrix, back_string_matrix, self.main_sprite_group,
                                 self.all_plants)
        self.chunk_matrix[row_i][col_i] = chunk
        self.loaded_chunks.add(chunk)
        self.pathfinding.pathfinding_tree.add_chunk(chunk.pathfinding_chunk)
        self._loading_chunks.remove((col_i, row_i))
        update_blocks = chunk.get_board_update_blocks()
        self.add_blocks(*update_blocks)

    def get_start_chunk(self):
        return self.chunk_matrix[con.START_CHUNK_POS[1]][con.START_CHUNK_POS[0]]

    def get_chunks_from_rect(self, rect):
        affected_chunks = []
        tl_column, tl_row = interface_util.p_to_cp(rect.topleft)
        br_column, br_row = interface_util.p_to_cp(pygame.Vector2(rect.bottomright) - pygame.Vector2(1, 1))
        top = rect.top
        for row in range((br_row - tl_row) + 1):
            if row == 0:
                height = min(con.CHUNK_SIZE.height - (top % con.CHUNK_SIZE.height), rect.height)
            elif row == br_row - tl_row:
                height = ((rect.bottom - top) % con.CHUNK_SIZE.height)
            else:
                height = con.CHUNK_SIZE.height
            left = rect.left
            for column in range((br_column - tl_column) + 1):
                if column == 0:
                    width = min(con.CHUNK_SIZE.width - (left % con.CHUNK_SIZE.width), rect.width)
                elif column == br_column - tl_column:
                    width = ((rect.right - left) % con.CHUNK_SIZE.width)
                else:
                    width = con.CHUNK_SIZE.width
                topleft = (left, top)
                new_rect = pygame.Rect((*topleft, width, height))
                chunk = self.chunk_from_point(topleft)
                if chunk is not None:
                    affected_chunks.append([chunk, new_rect])
                left += width
            top += height
        return affected_chunks

    def get_blocks_from_rect(self, rect):
        blocks = []
        for chunk, rect in self.get_chunks_from_rect(rect):
            for y_coord in range(rect.top, rect.bottom, con.BLOCK_SIZE.height):
                for x_coord in range(rect.left, rect.right, con.BLOCK_SIZE.width):
                    point = (x_coord, y_coord)
                    blocks.append(chunk.get_block(point))
        return blocks

    def surrounding_blocks(
        self,
        block: block_classes.Block
    ) -> List[Union[None, util.BlockPointer]]:
        """
        Calculate the surrounding block_classes of a certain block in the order NESW and None if there is no block
        (edge of the playing field).

        It is important to note that this function returns pointers to the matrix blocks, this means that if the block
        in the matrix changes the pointer will change.
        """
        blocks = [None for _ in range(4)]
        for index, new_position in enumerate([(0, -1), (1, 0), (0, 1), (-1, 0)]):
            surrounding_pos = (block.rect.x + new_position[0] * con.BLOCK_SIZE.width,
                               block.rect.y + new_position[1] * con.BLOCK_SIZE.height)
            # Make sure within range
            if surrounding_pos[0] > con.ORIGINAL_BOARD_SIZE.width or surrounding_pos[0] < 0 or \
                    surrounding_pos[1] > con.ORIGINAL_BOARD_SIZE.height or surrounding_pos[1] < 0:
                continue
            chunk = self.chunk_from_point(surrounding_pos)
            if chunk:
                surrounding_block = chunk.get_block(surrounding_pos)
                blocks[index] = surrounding_block
        return blocks

    def surrounding_chunks(self, chunk):
        chunks = [None for _ in range(4)]
        for index, new_position in enumerate([(0, -1), (1, 0), (0, 1), (-1, 0)]):
            surrounding_pos = (chunk.rect.x + new_position[0] * con.CHUNK_SIZE.width, chunk.rect.y + new_position[1] * con.CHUNK_SIZE.height)
            # Make sure within range
            if surrounding_pos[0] > con.ORIGINAL_BOARD_SIZE.width or \
                surrounding_pos[0] < 0 or \
                surrounding_pos[1] > con.ORIGINAL_BOARD_SIZE.height or \
                surrounding_pos[1] < 0:
                continue
            surrounding_chunk = self.chunk_from_point(surrounding_pos)
            chunks[index] = surrounding_chunk
        return chunks

    def remove_blocks(
        self,
        *blocks: Union[block_classes.Block, util.BlockPointer]
    ):
        removed_items = []
        for block in blocks:
            if isinstance(block, util.BlockPointer):
                block = block.block
            if isinstance(block.material, build_materials.Building):
                removed_items.extend(self.remove_building(block))
            elif isinstance(block.material, environment_materials.MultiFloraMaterial):
                removed_items.extend(self.remove_plant(block))
            else:
                if isinstance(block.material, build_materials.ConveyorBelt):
                    self.conveyor_network.remove(block)
                if isinstance(block, block_classes.VariableSurfaceBlock):
                    self.variable_blocks.remove(block)
                chunk = self.chunk_from_point(block.rect.topleft)
                removed_items.extend(chunk.remove_blocks(block))

            surrounding_blocks = self.surrounding_blocks(block)
            for index, s_block in enumerate(surrounding_blocks):
                if s_block is None:
                    continue
                # check if the block a surrounding plant is attached to is still solid
                elif block.is_solid() and isinstance(s_block.material, environment_materials.EnvironmentMaterial) and\
                        index == (s_block.material.START_DIRECTION + 2) % 4:
                    removed_items.extend(self.remove_blocks(s_block))
        return removed_items

    def remove_plant(self, plant_block):
        removed_items = []
        plant = None
        if plant_block in self.all_plants:
            plant = self.all_plants.get(plant_block.id)
        if plant is None:
            return []
        removed_blocks = plant.remove_block(plant_block)

        for plant_block in removed_blocks:
            chunk = self.chunk_from_point(plant_block.rect.topleft)
            removed_items.extend(chunk.remove_blocks(plant_block))
        if plant.size() == 0:
            self.all_plants.remove(plant_block.id)
        else:
            # redraw the tip of the plant
            self.add_blocks(plant.grow_block)
        return removed_items

    def remove_building(self, block):
        building_instance = self.buildings.pop(block.id, None)
        if building_instance is None:
            return []
        blocks = building_instance.blocks
        removed_items = building_instance.destroy()
        for row in blocks:
            for block in row:
                chunk = self.chunk_from_point(block.rect.topleft)
                chunk.remove_blocks(block)
        return removed_items

    def add_blocks(
        self,
        *blocks: Union[block_classes.Block, util.BlockPointer],
        update: bool = True
    ):
        for block in blocks:
            if isinstance(block, util.BlockPointer):
                block = block.block
            if isinstance(block.material, build_materials.Building):
                if update and isinstance(block, block_classes.VariableSurfaceBlock):
                    self.variable_blocks.add(block)
                self.add_building(block)
                continue
            if isinstance(block.material, build_materials.ConveyorBelt):
                self.conveyor_network.add(block)
            if update and isinstance(block, block_classes.VariableSurfaceBlock):
                self.variable_blocks.add(block)
            if update and isinstance(block, block_classes.SurroundableBlock):
                block.surrounding_blocks = self.surrounding_blocks(block)
            chunk = self.chunk_from_point(block.coord)
            if update:
                self.__set_block_lighting(block)
            chunk.add_blocks(block)

    def __set_block_lighting(
        self,
        block: block_classes.Block
    ):
        """Set the lighting for one block specifically"""
        surrounding_blocks = self.surrounding_blocks(block)
        valid_surrounding_blocks = [b for b in surrounding_blocks if b is not None]
        if len(valid_surrounding_blocks) == 0:
            return
        max_light_block = max(valid_surrounding_blocks, key=lambda x: x.light_level)
        change = con.DECREASE_SPEED_SOLID if max_light_block.is_solid() else con.DECREASE_SPEED
        block.light_level = max_light_block.light_level - change

    def add_building(self, block_of_building: Union[block_classes.Block, buildings.Building]):
        # if the incomming block is a single block part of a building, create the full building first
        if not isinstance(block_of_building, buildings.Building):
            if isinstance(block_of_building, block_classes.ContainerBlock):
                block_of_building = buildings.material_mapping[block_of_building.material.name()](
                    block_of_building.rect.topleft, self.main_sprite_group, starting_items=block_of_building.inventory)
            else:
                block_of_building = buildings.material_mapping[block_of_building.material.name()](
                    block_of_building.rect.topleft, self.main_sprite_group, )
        self.buildings[block_of_building.id] = block_of_building
        for row in block_of_building.blocks:
            for block in row:
                if hasattr(block, "inventory"):
                    self.inventorie_blocks.append(block)
                chunk = self.chunk_from_point(block.coord)
                chunk.add_blocks(block)

    def adjust_lighting(
        self,
        point: Union[Tuple[int, int], List[int]],
        radius: int,
        point_light: int
    ):
        """extend in a diamond around a center point and assign new light values based on the light point. This is a
        function for updating the light around a light source"""
        point_light = min(point_light, con.MAX_LIGHT)

        start_block = self.__block_from_point(point)
        if start_block is None:
            return
        if start_block.light_level < point_light:
            start_block.light_level = point_light
            self.changed_light_blocks.add(start_block)
        total_column_blocks = int(radius / con.BLOCK_SIZE.width)
        total_row_blocks = int(radius / con.BLOCK_SIZE.height)

        light_level = [point_light, point_light]
        for row_i in range(total_row_blocks):
            for row_s_i, sign in enumerate((-1, 1)):
                if light_level[row_s_i] <= 0:
                    continue
                if light_level[0] <= 0 and light_level[1] <= 0:
                    break
                new_block_y = point[1] + sign * row_i * con.BLOCK_SIZE.height
                next_block = self.__block_from_point((point[0], new_block_y))
                if next_block is None:
                    continue
                self.__select_col_light_blocks(total_column_blocks + 1 - row_i, [point[0], new_block_y],
                                               light_level[row_s_i], sign)
                change = con.DECREASE_SPEED_SOLID if next_block.is_solid() else con.DECREASE_SPEED
                light_level[row_s_i] -= change

    def __select_col_light_blocks(
        self,
        extend_total: int,
        point: Union[Tuple[int, int], List],
        point_light: int,
        row_sign: int
    ):
        light_level = [point_light, point_light]
        for col_i in range(extend_total):
            for col_s_i, sign in enumerate((-1, 1)):
                if light_level[col_s_i] <= 0:
                    continue
                if light_level[0] <= 0 and light_level[1] <= 0:
                    break
                new_block_x = point[0] + sign * col_i * con.BLOCK_SIZE.width
                next_block = self.__block_from_point((new_block_x, point[1]))
                adjacent_block = self.__block_from_point((new_block_x, point[1] +
                                                          (row_sign * - 1) * con.BLOCK_SIZE.height))
                if next_block is None:
                    continue
                if light_level[col_s_i] != next_block.light_level:
                    self.__change_block_light_level(light_level[col_s_i], next_block)
                change = con.DECREASE_SPEED_SOLID if next_block.is_solid() else con.DECREASE_SPEED
                if adjacent_block is not None and adjacent_block.light_level > light_level[col_s_i]:
                    light_level[col_s_i] = adjacent_block.light_level - change
                else:
                    light_level[col_s_i] -= change

    def __change_block_light_level(
        self,
        light_level: int,
        block: block_classes.Block
    ):
        if block is not None and block.light_level < light_level:
            block.light_level = light_level
            self.changed_light_blocks.add(block)

    @game_timing.time_function("light updates")
    def change_light_levels(self):
        for block in self.changed_light_blocks:
            chunk = self.chunk_from_point(block.rect.topleft)
            alpha = max(min(255 - block.light_level * int(255 / con.MAX_LIGHT), 255), 0)
            chunk.add_rectangle(block.rect, (0, 0, 0, alpha), layer=0)

    def closest_inventory(self, start, *item_names, deposit=True):
        """
        """
        #any distance should be shorter possible on the board
        shortest_distance = con.BOARD_SIZE.width * con.BOARD_SIZE.height
        closest_block = None
        for building in self.buildings.values():
            if not building.has_inventory():
                continue
            inventory = building.blocks[0][0].inventory
            if (deposit == False and all([inventory.check_item_get(name) for name in item_names])):
                pass
            elif (deposit == True and all([inventory.check_item_deposit(name) for name in item_names])):
                pass
            else:
                continue

            distance = util.manhattan_distance(start.center, building.rect.center)
            if distance < shortest_distance:
                shortest_distance = distance
                closest_block = building
        return closest_block

    def add_rectangle(self, rect, color, layer=2, border=0):
        chunk_rectangles = self.get_chunks_from_rect(rect)
        for chunk, rect in chunk_rectangles:
            chunk.add_rectangle(rect, color, layer, border)

    def transparant_collide(
        self,
        point: Union[List, Tuple[int, int]]
    ) -> bool:
        """Check if a point collides with a block that is considered transparant (transparant group != 0). If the point
        is outside the board False is returned"""
        block = self.__block_from_point(point)
        return block is not None and block.transparant_group != 0

    def chunk_from_point(
        self,
        point: Union[List, Tuple[int, int]]
    ) -> Union[chunks.Chunk, None]:
        """Get a chunk on the board given a point in pixels. Coordinates outside the board return None"""
        column, row = interface_util.p_to_cp(point)
        try:
            return self.chunk_matrix[row][column]
        except IndexError:
            return None

    def __block_from_point(
        self,
        point: Union[List, Tuple[int, int]]
    ) -> Union[block_classes.Block, None]:
        """Get the block at a given pixel point. None is returned when the block is not available."""
        chunk = self.chunk_from_point(point)
        if chunk is not None:
            return chunk.get_block(point)
        return None

    def can_add_flora(self, block, flora):
        sur_blocks = self.surrounding_blocks(block)
        if sur_blocks[flora.CONTINUATION_DIRECTION  - 2] != None and \
                sur_blocks[flora.CONTINUATION_DIRECTION - 2].transparant_group == 0:
            return True
        return False

    def __add_starter_buildings(self):
        """
        Add all starter building that should be placed before the game starts
        """
        start_chunk = self.get_start_chunk()
        appropriate_location = pygame.Vector2(int(start_chunk.START_RECTANGLE.centerx / con.BLOCK_SIZE.width) * con.BLOCK_SIZE.width + start_chunk.rect.left,
                                              + start_chunk.START_RECTANGLE.bottom - con.BLOCK_SIZE.height + + start_chunk.rect.top)
        t = buildings.Terminal(appropriate_location + (-40, 0), self.main_sprite_group)
        c = buildings.Factory(appropriate_location + (40, 0), self.main_sprite_group)
        f = buildings.Furnace(appropriate_location + (0, 0), self.main_sprite_group)
        self.add_blocks(t)
        self.add_blocks(c)
        self.add_blocks(f)
        self.terminal = t

    def add_to_terminal_inventory(self, item):
        self.terminal.inventory.add_items(item)
