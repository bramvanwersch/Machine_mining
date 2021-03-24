from random import uniform
import pygame
from math import ceil
from typing import List, Union, Tuple
from threading import Thread

import utility.utilities as util
import utility.constants as con
import block_classes.blocks as block_classes
import block_classes.buildings as buildings
import block_classes.building_materials as build_materials
import block_classes.ground_materials as ground_materials
import block_classes.environment_materials as environment_materials
import interfaces.interface_utility as interface_util
from board import flora, chunks, pathfinding
import network.conveynetwork


class Board(util.Serializer):

    START_RECTANGLE = pygame.Rect((con.BOARD_SIZE.width / 2 - 125, 0, 250, 50))
    BLOCK_PER_CLUSRTER = 500

    chunk_matrix: List[List[Union[chunks.Chunk, None]]]

    def __init__(self, board_generator, main_sprite_group, progress_var, chunk_matrix=None, pipe_network=None, grow_update_time=0):
        self.inventorie_blocks = []
        self.main_sprite_group = main_sprite_group

        # setup the board
        progress_var[0] = "Innitialising pathfinding..."
        self.pathfinding = pathfinding.PathFinder()
        self.all_plants = flora.Flora()

        self.board_generator = board_generator
        self.chunk_matrix = [[None for _ in range(int(con.BOARD_SIZE.width / con.CHUNK_SIZE.width))]
                             for _ in range(int(con.BOARD_SIZE.height / con.CHUNK_SIZE.height))]
        self.loaded_chunks = set()
        # chunks that are currently loading to make sure that no double chunks are generated
        self._loading_chunks = set()
        self.main_sprite_group = main_sprite_group
        self.generate_chunks(*con.START_LOAD_AREA, thread_it=False, progress_var=progress_var)

        # last placed highlighted rectangle
        self.__highlight_rectangle = None

        # pipe network
        progress_var[0] = "Innitialising pipe network..."
        self.conveyor_network = network.conveynetwork.ConveyorNetwork()

        self.buildings = {}
        self.changed_light_blocks = set()

        self.__grow_update_time = grow_update_time
        self.__terminal = None

    def setup_board(self):
        self.__add_starter_buildings()
        for _ in range(10):
            self.update_board()

    def update_board(self):

        # update lighting
        self.change_light_levels()
        self.changed_light_blocks = set()

        self.pathfinding.update()

        self.__update_conveyor_network()

        self.__update_plants()

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

    def __update_conveyor_network(self):
        for belt in self.conveyor_network:
            surrounding_blocks = self.surrounding_blocks(belt)
            belt.check_item_movement(surrounding_blocks)
            if belt.changed:
                self.add_blocks(belt)
                belt.changed = False

    def to_dict(self):
        return {
            "chunk_matrix": [chunk.to_dict() for row in self.chunk_matrix for chunk in row],
            "buildings": [building.to_dict() for building in self.buildings.values()],
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
                                      self.all_plants, first_time=True)
        else:
            chunk = chunks.Chunk(point_pos, for_string_matrix, back_string_matrix, self.main_sprite_group,
                                 self.all_plants)
        self.chunk_matrix[row_i][col_i] = chunk
        self.loaded_chunks.add(chunk)
        self.pathfinding.pathfinding_tree.add_chunk(chunk.pathfinding_chunk)
        self._loading_chunks.remove((col_i, row_i))

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
    ) -> List[Union[None, block_classes.Block]]:
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
            if surrounding_pos[0] > con.BOARD_SIZE.width or \
                surrounding_pos[0] < 0 or \
                surrounding_pos[1] > con.BOARD_SIZE.height or \
                surrounding_pos[1] < 0:
                continue
            surrounding_chunk = self.chunk_from_point(surrounding_pos)
            chunks[index] = surrounding_chunk
        return chunks

    def remove_blocks(self, *blocks):
        removed_items = []
        for block in blocks:
            if isinstance(block.material, build_materials.Building):
                removed_items.extend(self.remove_building(block))
            elif isinstance(block.material, environment_materials.MultiFloraMaterial):
                removed_items.extend(self.remove_plant(block))
            else:
                if isinstance(block, block_classes.ConveyorNetworkBlock):
                    self.conveyor_network.remove(block)
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

    def add_blocks(self, *blocks: List[block_classes.Block]):
        for block in blocks:
            if isinstance(block, buildings.Building):
                self.add_building(block)
                return
            if isinstance(block, block_classes.ConveyorNetworkBlock):
                self.conveyor_network.add(block)
            chunk = self.chunk_from_point(block.coord)
            self.__set_block_lighting(block)
            chunk.add_blocks(block)

    def __set_block_lighting(self, block):
        """Set the lighting for one block specifically"""
        surrounding_blocks = self.surrounding_blocks(block)
        max_light_block = max([b for b in surrounding_blocks if b is not None], key=lambda x: x.light_level)
        change = con.DECREASE_SPEED_SOLID if max_light_block.is_solid() else con.DECREASE_SPEED
        block.light_level = max_light_block.light_level - change

    def add_building(self, building_instance):
        self.buildings[building_instance.id] = building_instance
        for row in building_instance.blocks:
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

    def change_light_levels(self):
        for block in self.changed_light_blocks:
            chunk = self.chunk_from_point(block.rect.topleft)
            alpha = 255 - block.light_level * int(255 / con.MAX_LIGHT)
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
        t = buildings.Terminal(appropriate_location + (-20, -10), self.main_sprite_group)
        c = buildings.Factory(appropriate_location + (20, -10), self.main_sprite_group)
        f = buildings.Furnace(appropriate_location + (0, -10), self.main_sprite_group)
        self.add_building(t)
        self.add_building(c)
        self.add_building(f)
        self.__terminal = t

    def add_to_terminal_inventory(self, item):
        self.__terminal.inventory.add_items(item)
