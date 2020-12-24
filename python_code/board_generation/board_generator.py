from random import randint, choices, uniform, choice
from math import pi, cos, sin, ceil, sqrt
from typing import List, Dict, Union, ClassVar, Set, Tuple
import pygame

from utility import constants as con, utilities as util
import interfaces.interface_utility as interface_util
from block_classes import ground_materials, block_utility as block_util
import board_generation.biomes as biome_classes


class BoardGenerator:
    # the size of quadrants where a new biome is chosen
    __BIOME_SIZES: ClassVar[Dict[str, util.Size]] = \
        {"tiny": util.Size(100, 100), "small": util.Size(200, 200), "normal": util.Size(500, 500),
         "big": util.Size(750, 7500), "massive": util.Size(1000, 1000), "huge": util.Size(1500, 1500)}  # in pixels

    # determines the standard deviation of the biomes, high values means very broad distributions
    __BIOME_BLEND: ClassVar[Dict[str, int]] = \
        {"tiny": 1, "small": 5, "normal": 15, "severe": 30, "extreme": 50}

    # CAVE values TODO change these when generating dynamic map
    MAX_CAVES = 6
    MAX_POINT_DISTANCE = 1000
    # number of points a cave consists of
    MAX_NUMBER_OF_CAVE_POINTS = 10
    MAX_CAVE_TURN = pi  # the max change in direction between 2 cave points
    # the chance for a cave to stop extending around its core. Do not go lower then 0.0001 --> takes a long time
    CAVE_STOP_SPREAD_CHANCE = 0.01

    # BORDER values
    BORDER_SPREAD_LIKELYHOOD = util.Gaussian(0, 2)
    MAX_BORDER_SPREAD_DISTANCE = 4

    __environment_material_name: Set[str]
    __biome_definition: biome_classes.BiomeGenerationDefinition
    __biome_size: util.Size
    __biome_blend: int

    def __init__(
        self,
        biome_generation_def: Union[biome_classes.BiomeGenerationDefinition, str] = None,
        biome_size: Union[str, util.Size] = "normal",
        biome_blend: Union[str, int] = "normal"
    ):
        self.__environment_material_names = {mat.name() for mat in block_util.environment_materials}
        self.__biome_definition = biome_generation_def if biome_generation_def else\
            biome_classes.NormalBiomeGeneration()
        self.__biome_size = self.__BIOME_SIZES[biome_size] if biome_size in self.__BIOME_SIZES else biome_size
        self.__biome_blend = self.__BIOME_BLEND[biome_blend] if biome_blend in self.__BIOME_BLEND else biome_blend
        self.__predefined_blocks = PredefinedBlocks()

        # TODO make these dynamically grow when new areas are loaded
        self.__biome_matrix = BiomeMatrix(self.__biome_size)
        innitial_outer_load_rect = pygame.Rect((0 - int(con.INIT_BIOME_LOAD_SPACE / 2), 0,
                                                con.INIT_BIOME_LOAD_SPACE, con.MAX_DEPTH))
        self.__generate_biomes(innitial_outer_load_rect)
        # a tree of blocks that are already defined as part of the structure/cave generation
        self.__generate_structure_locations(innitial_outer_load_rect)

    def __generate_biomes(self, rect) -> None:
        # make sure that even partial areas of the board are covered by a biome
        for col_i in range(ceil(rect.width / self.__biome_size.width)):
            column = []
            tl_x = rect.left + col_i * self.__biome_size.width  # in pixels
            for row_i in range(ceil(con.MAX_DEPTH / self.__biome_size.height)):
                tl_y = rect.top + row_i * self.__biome_size.height  # in pixels
                column.append(self.__generate_biome(tl_x, tl_y))
            self.__biome_matrix.add(int(tl_x / self.__biome_size.width), column)

    def __generate_structure_locations(self, rect):
        """generate structures in a given rectangle by adding blocks to the __predefined_blocks tree"""
        # TODO add structures here
        nr_caves = randint(self.MAX_CAVES - int(max(self.MAX_CAVES / 2, 1)), self.MAX_CAVES)
        # Me brother : )
        square_size = sqrt((rect.width * rect.height) / nr_caves)
        for row_i in range(round(rect.height / square_size)):
            for col_i in range(round(rect.width / square_size)):
                x_coord = randint(int(col_i * square_size), int((col_i + 1) * square_size))
                y_coord = randint(int(row_i * square_size), int((row_i + 1) * square_size))
                self.__generate_cave([x_coord, y_coord])

    def __generate_biome(self, tl_x, tl_y) -> biome_classes.Biome:
        # allow the shapes of the distributions to be a bit different
        sd_x = self.__biome_size.width * self.__biome_blend * uniform(0.8, 1.2)
        sd_y = self.__biome_size.height * self.__biome_blend * uniform(0.8, 1.2)
        # make sure that distribution centers are not right at the edge of the quadrant
        mean_x = randint(tl_x, int(tl_x + self.__biome_size.width / 2))
        mean_y = randint(tl_y, int(tl_y + self.__biome_size.height / 2))
        # check depths in blocks
        biome_type = self.__biome_definition.get_biome(int(mean_y / con.BLOCK_SIZE.height))
        biome_instance = biome_type(util.Gaussian(mean_x, sd_x), util.Gaussian(mean_y, sd_y))
        return biome_instance

    def generate_chunk(self, topleft):
        matrix = [[None for _ in range(interface_util.p_to_c(con.CHUNK_SIZE.width))]
                  for _ in range(interface_util.p_to_r(con.CHUNK_SIZE.height))]
        background_matrix = [[None for _ in range(interface_util.p_to_c(con.CHUNK_SIZE.width))]
                             for _ in range(interface_util.p_to_r(con.CHUNK_SIZE.height))]
        self.__add_blocks(pygame.Rect((*topleft, *con.CHUNK_SIZE.size)), matrix, background_matrix)
        # add a border if neccesairy
        if topleft[1] == 0:
            self.__add_border(matrix, "north")
        elif topleft[1] + con.CHUNK_SIZE.height >= con.MAX_DEPTH:
            self.__add_border(matrix, "south")
        return matrix, background_matrix

    def __add_blocks(self, rect, matrix, background_matrix):
        for row_i in range(int(rect.height / con.BLOCK_SIZE.height)):
            for col_i in range(int(rect.width / con.BLOCK_SIZE.width)):
                x = col_i * con.BLOCK_SIZE.width - int(rect.left / con.BLOCK_SIZE.width)
                y = row_i * con.BLOCK_SIZE.height - int(rect.top / con.BLOCK_SIZE.height)
                # add pre_defined_blocks
                if (x, y) in self.__predefined_blocks:
                    matrix[row_i][col_i] = self.__predefined_blocks.get((x, y))
                block = matrix[row_i][col_i]
                # determine biome based on coordinate
                biome_liklyhoods = self.__biome_matrix.liklyhoods_from_point(x, y)
                biome = choices(list(biome_liklyhoods.keys()), list(biome_liklyhoods.values()), k=1)[0]
                # only add plants in caves
                if block == "Air" and uniform(0, 1) < biome.FLORA_LIKELYHOOD:
                    flora_likelyhoods = biome.get_flora_lh_at_depth(row_i)
                    self.__add_environment(col_i, row_i, flora_likelyhoods, matrix)
                elif block is None and uniform(0, 1) < biome.CLUSTER_LIKELYHOOD:
                    ore_likelyhoods = biome.get_ore_lh_at_depth(row_i)
                    self.__add_ore_cluster(col_i, row_i, ore_likelyhoods, matrix, biome)
                elif block is None:
                    filler_likelyhoods = biome.get_filler_lh_at_depth(row_i)
                    filler = choices(list(filler_likelyhoods.keys()), list(filler_likelyhoods.values()), k=1)[0]
                    matrix[row_i][col_i] = filler
                # reget the biome to get slightly different front and backgrounds
                biome = choices(list(biome_liklyhoods.keys()), list(biome_liklyhoods.values()), k=1)[0]
                background_likelyhoods = biome.get_background_lh_at_depth(row_i)
                background_mat = choices(list(background_likelyhoods.keys()),
                                         list(background_likelyhoods.values()), k=1)[0]
                background_matrix[row_i][col_i] = background_mat

    def __add_environment(self, col_i, row_i, flora_likelyhoods, matrix):
        s_coords = self.__get_surrounding_block_coords(col_i, row_i)
        elligable_indexes = []
        for coord in s_coords:
            try:
                if coord is not None and matrix[coord[1]][coord[0]] != "Air" and \
                        matrix[coord[1]][coord[0]] not in self.__environment_material_names:
                    elligable_indexes.append(coord)
            except IndexError:
                # skip coords outside the chunk
                continue
        # if direction cant have a flora return
        if len(elligable_indexes) == 0:
            return
        chosen_index = s_coords.index(choice(elligable_indexes))
        # if the chosen index has no plant options return
        if len(flora_likelyhoods[chosen_index]) == 0:
            return
        flora = choices(list(flora_likelyhoods[chosen_index].keys()),
                        list(flora_likelyhoods[chosen_index].values()), k=1)[0]
        matrix[row_i][col_i] = flora

    def __add_ore_cluster(self, col_i, row_i, ore_likelyhoods, matrix, biome):
        ore = choices(list(ore_likelyhoods.keys()), list(ore_likelyhoods.values()), k=1)[0]
        ore_locations = self.__create_ore_cluster(ore, (col_i, row_i), biome)
        ore_locations.append([col_i, row_i])
        for loc in ore_locations:
            try:
                if matrix[loc[1]][loc[0]] == "Air":
                    continue
                matrix[loc[1]][loc[0]] = ore
            except IndexError:
                # ores cannot generate over chunk boundaries as of yet
                continue

    def __create_ore_cluster(self, ore, center, biome):
        size = getattr(ground_materials, ore).get_cluster_size()
        ore_locations = []
        while len(ore_locations) <= size:
            location = [0, 0]
            for index in range(2):
                pos = choice([-1, 1])
                # make sure index is bigger then 0
                location[index] = max(0, pos * randint(0, biome.MAX_CLUSTER_SIZE) + center[index])
            if location not in ore_locations:
                ore_locations.append(location)
        return ore_locations

    def __generate_cave(self, start_point):
        """Save air_blocks in the pre-defined tree"""
        cave_points = self.__get_cave_points(start_point)
        # get the line between the points
        for index1 in range(1, len(cave_points)):
            point1 = cave_points[index1 - 1]
            point2 = cave_points[index1]
            a, b = util.line_from_points(point1, point2)
            if abs(a) < 1:
                number_of_breaks = int(abs(point1[0] - point2[0]) * abs(1 / a))
            else:
                number_of_breaks = int(abs(point1[0] - point2[0]) * abs(a))
            break_size = (point2[0] - point1[0]) / number_of_breaks
            x_values = [point1[0] + index * break_size for index in range(0, number_of_breaks)]
            y_values = [a * x + b for x in x_values]
            # make all block_classes air on the direct line
            for index2 in range(len(x_values)):
                x = int(x_values[index2])
                matrix_x = min(x, int(con.BOARD_SIZE.width / con.BLOCK_SIZE.width) - 1)
                y = int(y_values[index2])
                matrix_y = min(y, int(con.BOARD_SIZE.height / con.BLOCK_SIZE.height) - 1)
                self.__predefined_blocks.add((matrix_x, matrix_y), "Air")
                surrounding_coords = \
                    [coord for coord in self.__get_surrounding_block_coords(x, y) if coord is not None
                     and not self.__predefined_blocks.check(coord, "Air")]
                # extend the cave around the direct line.
                while len(surrounding_coords) > 0:
                    if uniform(0, 1) < self.CAVE_STOP_SPREAD_CHANCE:
                        break
                    remove_coord = choice(surrounding_coords)
                    surrounding_coords.remove(remove_coord)
                    self.__predefined_blocks.add(remove_coord, "Air")
                    additional_surrounding_coords = \
                        [coord for coord in self.__get_surrounding_block_coords(*remove_coord) if coord is not None
                         and not self.__predefined_blocks.check(coord, "Air")]
                    surrounding_coords.extend(additional_surrounding_coords)

    def __get_cave_points(self, start_point):
        cave_points = [start_point]
        prev_direction = uniform(0, 2 * pi)
        amnt_points = randint(self.MAX_NUMBER_OF_CAVE_POINTS - int(max(self.MAX_NUMBER_OF_CAVE_POINTS / 2, 1)),
                              self.MAX_NUMBER_OF_CAVE_POINTS)
        while len(cave_points) < amnt_points:
            radius = randint(max(1, int(self.MAX_POINT_DISTANCE / 2)), self.MAX_POINT_DISTANCE)
            prev_direction = uniform(prev_direction - self.MAX_CAVE_TURN / 2, prev_direction + self.MAX_CAVE_TURN / 2)
            new_x = int(cave_points[-1][0] + cos(prev_direction) * radius)
            new_y = min(max(int(cave_points[-1][1] + sin(prev_direction) * radius), 0), con.MAX_DEPTH)
            # make sure no double points and no straight lines
            if [new_x, new_y] in cave_points or \
                    int(new_x / con.BLOCK_SIZE.width) == int(cave_points[-1][0] / con.BLOCK_SIZE.width) or \
                    int(new_y / con.BLOCK_SIZE.height) == int(cave_points[-1][1] / con.BLOCK_SIZE.height):
                continue
            cave_points.append([new_x, new_y])
        return [[int(x / con.BLOCK_SIZE.width), int(y / con.BLOCK_SIZE.height)] for x, y in cave_points]

    def __get_surrounding_block_coords(self, x, y) -> List[Union[List[int], None]]:
        surrounding_coords = [None for _ in range(4)]
        for index, new_position in enumerate([(0, -1), (1, 0), (0, 1), (-1, 0)]):
            surrounding_coord = [x + new_position[0], y + new_position[1]]
            # Only y range is limited
            if surrounding_coord[1] >= con.MAX_DEPTH or surrounding_coord[1] < 0:
                continue
            surrounding_coords[index] = surrounding_coord
        return surrounding_coords

    def __add_border(self, matrix, direction):
        if direction == "north":
            rows = matrix[0:self.MAX_BORDER_SPREAD_DISTANCE]
            for row_i in range(len(rows)):
                border_block_chance = self.BORDER_SPREAD_LIKELYHOOD.cumulative_probability(row_i)
                for col_i in range(len(matrix[row_i])):
                    if uniform(0, 1) < border_block_chance:
                        matrix[row_i][col_i] = "BorderMaterial"
        elif direction == "south":
            rows = matrix[- (self.MAX_BORDER_SPREAD_DISTANCE + 1):-1]
            for row_i in range(len(rows)):
                border_block_chance = self.BORDER_SPREAD_LIKELYHOOD.cumulative_probability(row_i)
                for col_i in range(len(matrix[row_i])):
                    if uniform(0, 1) < border_block_chance:
                        matrix[-(row_i + 1)][- (col_i + 1)] = "BorderMaterial"
        else:
            raise util.GameException("Unrecognized direction for border: {}".format(direction))


class BiomeMatrix:
    """List of lists in the coordinate system of the biomes, making things more convenient"""
    def __init__(self, biome_size: util.Size):
        self.__internal_tree = {}
        self.__biome_size = biome_size
        self.__expected_column_size = ceil(con.MAX_DEPTH / self.__biome_size.height)

    def add(self, x_coord: int, column: List[biome_classes.Biome]):
        if len(column) != self.__expected_column_size:
            raise util.GameException("Expected a column of len {} got {}".
                                     format(self.__expected_column_size, len(column)))
        elif len(self.__internal_tree) > 0 and x_coord - 1 not in self.__internal_tree and \
                x_coord + 1 not in self.__internal_tree:
            raise util.GameException("Can only add adjacent columns {} is not close enough".format(x_coord))
        self.__internal_tree[x_coord] = column

    def liklyhoods_from_point(self, x, y):
        biome_matrix_col = int(x / self.__biome_size.width)
        biome_matrix_row = int(y / self.__biome_size.height)
        main_biome = self.__internal_tree[biome_matrix_row][biome_matrix_col]
        surrounding_biomes = [main_biome]
        # collect all surrounding biomes
        for new_position in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            surrounding_coord = [biome_matrix_col + new_position[0], biome_matrix_row + new_position[1]]
            if surrounding_coord[0] not in self.__internal_tree\
                    or surrounding_coord[1] > self.__expected_column_size or surrounding_coord[1] < 0:
                continue
            surrounding_biomes.append(self.__internal_tree[surrounding_coord[1]][surrounding_coord[0]])
        wheights = util.normalize([b.get_likelyhood_at_coord(x, y) for b in surrounding_biomes])
        biome_likelyhoods = {biome: wheights[index] for index, biome in enumerate(surrounding_biomes)}
        return biome_likelyhoods


class PredefinedBlocks:
    """Save at what coordinate there are pre_defined materials for blocks generated outside the matrixes directly
    generated"""
    __internal_tree: Dict[int, Dict[int, str]]

    def __init__(self):
        self.__internal_tree = {}

    def add(self, coord: Union[Tuple[int, int], List[int]], value: str, overwrite=True):
        if coord[1] in self.__internal_tree:
            self.__internal_tree[coord[1]][coord[0]] = value
        # do not overwrite if requested
        elif not overwrite and coord[0] in self.__internal_tree[coord[1]]:
            return
        else:
            if coord[1] > con.MAX_DEPTH:
                print("Carefull {} is outside the board".format(coord))
                return
            self.__internal_tree[coord[1]] = {coord[0]: value}

    def get(self, coord: Union[Tuple[int, int], List[int]]) -> str:
        return self.__internal_tree[coord[1]].pop(coord[0])

    def check(self, coord: Union[Tuple[int, int], List[int]], value: str) -> bool:
        return coord in self and self.__internal_tree[coord[1]][coord[0]] == value

    def __contains__(self, item: Union[Tuple[int, int], List[int]]):
        return item[1] in self.__internal_tree and item[0] in self.__internal_tree[item[1]]
