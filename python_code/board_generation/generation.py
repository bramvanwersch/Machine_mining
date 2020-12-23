from random import randint, choices, uniform, choice
from math import pi, cos, sin, ceil
from typing import List, Dict, Union, ClassVar, Set

from utility import constants as con, utilities as util
import interfaces.interface_utility as interface_util
from block_classes import ground_materials, block_utility as block_util
import board_generation.biomes as biome_classes


class BoardGenerator:
    # the size of quadrants where a new biome is chosen
    __BIOME_SIZES: ClassVar[Dict[str, util.Size]] = \
        {"tiny": util.Size(100, 100), "small": util.Size(200, 200), "normal": util.Size(500, 500),
         "big": util.Size(750, 7500), "massive": util.Size(1000, 1000), "huge": util.Size(1500, 1500)}  # in blocks

    # determines the standard deviation of the biomes, high values means very broad distributions
    __BIOME_BLEND: ClassVar[Dict[str, int]] = \
        {"tiny": 1, "small": 5, "normal": 15, "severe": 30, "extreme": 50}

    # CAVE values
    MAX_CAVES = max(int((con.CHUNK_GRID_SIZE.width * con.CHUNK_GRID_SIZE.height) / 6), 1)
    # the fraction of the distance between points based on the shortest side of the board
    POINT_FRACTION_DISTANCE = 0.35
    # distance the center of the cave should at least be away from the border 10%
    CAVE_X_BORDER_DISTANCE = int(0.1 * con.BOARD_SIZE.width)
    CAVE_Y_BORDER_DISTANCE = int(0.1 * con.BOARD_SIZE.height)
    # number of points a cave consists of
    NUMBER_OF_CAVE_POINTS = int(con.CHUNK_GRID_SIZE.width * con.CHUNK_GRID_SIZE.height * 1.3)
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

        # TODO make these dynamically grow when new areas are loaded
        self.biome_matrix = self.generate_biome_matrix()
        self.foreground_matrix, self.backgroun_matrix = self.__generate_foreground_string_matrix()

    def generate_biome_matrix(self) -> List[List[biome_classes.Biome]]:
        """Generate a list of lists whit biomes in quadrants of th"""
        biome_matrix = []
        # sufficient amount of overlap
        sd_x = self.__biome_size.width * self.__biome_blend
        sd_y = self.__biome_size.height * self.__biome_blend
        # make sure that even partial areas of the board are covered by a biome
        for row_i in range(ceil(con.BOARD_SIZE.height / self.__biome_size.height)):
            row = []
            for col_i in range(ceil(con.BOARD_SIZE.width / self.__biome_size.width)):
                # make sure that distribution centers are not right at the edge of the quadrant
                mean_x = randint(int(col_i * self.__biome_size.width * 1.1),
                                 int((col_i + 1) * self.__biome_size.width * 0.9))
                mean_y = randint(int(row_i * self.__biome_size.height * 1.1),
                                 int((row_i + 1) * self.__biome_size.height * 0.9))
                # check depths in blocks
                biome_type = self.__biome_definition.get_biome(int(mean_y / con.BLOCK_SIZE.height))
                biome_instance = biome_type(util.Gaussian(mean_x, sd_x), util.Gaussian(mean_y, sd_y))
                row.append(biome_instance)
            biome_matrix.append(row)
        return biome_matrix

    def biome_liklyhoods_from_point(self, x, y):
        biome_matrix_col = int(x / self.__biome_size.width)
        biome_matrix_row = int(y / self.__biome_size.height)
        main_biome = self.biome_matrix[biome_matrix_row][biome_matrix_col]
        surrounding_biomes = [main_biome]
        # collect all surrounding biomes
        for new_position in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            surrounding_coord = [biome_matrix_col + new_position[0], biome_matrix_row + new_position[1]]
            if surrounding_coord[0] >= len(self.biome_matrix[0]) - 1 or surrounding_coord[0] < 0 \
                    or surrounding_coord[1] >= len(self.biome_matrix) - 1 or surrounding_coord[1] < 0:
                continue
            surrounding_biomes.append(self.biome_matrix[surrounding_coord[1]][surrounding_coord[0]])
        wheights = util.normalize([b.get_likelyhood_at_coord(x, y) for b in surrounding_biomes])
        biome_likelyhoods = {biome: wheights[index] for index, biome in enumerate(surrounding_biomes)}
        return biome_likelyhoods

    def __generate_foreground_string_matrix(self):
        matrix = [[None for _ in range(interface_util.p_to_c(con.ORIGINAL_BOARD_SIZE.width))]
                  for _ in range(interface_util.p_to_r(con.ORIGINAL_BOARD_SIZE.height))]
        background_matrix = [[None for _ in range(interface_util.p_to_c(con.ORIGINAL_BOARD_SIZE.width))]
                             for _ in range(interface_util.p_to_r(con.ORIGINAL_BOARD_SIZE.height))]
        self.__add_caves(matrix)
        self.__add_blocks(matrix, background_matrix)
        self.__add_border(matrix)
        return matrix, background_matrix

    def __add_blocks(self, matrix, background_matrix):
        for row_i, row in enumerate(matrix):
            for col_i in range(len(row)):
                x = col_i * con.BLOCK_SIZE.width
                y = row_i * con.BLOCK_SIZE.height
                # determine biome based on coordinate
                biome_liklyhoods = self.biome_liklyhoods_from_point(x, y)
                biome = choices(list(biome_liklyhoods.keys()), list(biome_liklyhoods.values()), k=1)[0]
                # only add plants in caves
                if matrix[row_i][col_i] == "Air" and uniform(0, 1) < biome.FLORA_LIKELYHOOD:
                    flora_likelyhoods = biome.get_flora_lh_at_depth(row_i)
                    self.__add_environment(col_i, row_i, flora_likelyhoods, matrix)
                elif uniform(0, 1) < biome.CLUSTER_LIKELYHOOD:
                    ore_likelyhoods = biome.get_ore_lh_at_depth(row_i)
                    self.__add_ore_cluster(col_i, row_i, ore_likelyhoods, matrix, biome)
                elif matrix[row_i][col_i] is None:
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
            if coord is not None and matrix[coord[1]][coord[0]] != "Air" and \
                    matrix[coord[1]][coord[0]] not in self.__environment_material_names:
                elligable_indexes.append(coord)
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
                # if outside board skip
                continue

    def __create_ore_cluster(self, ore, center, biome):
        size = getattr(ground_materials, ore).get_cluster_size()
        ore_locations = []
        while len(ore_locations) <= size:
            location = [0, 0]
            for index in range(2):
                pos = choice([-1, 1])
                # assert index is bigger then 0
                location[index] = max(0, pos * randint(0, biome.MAX_CLUSTER_SIZE) + center[index])
            if location not in ore_locations:
                ore_locations.append(location)
        return ore_locations

    def __add_caves(self, matrix):
        nr_caves = randint(self.MAX_CAVES - int(max(self.MAX_CAVES / 2, 1)), self.MAX_CAVES)
        for _ in range(nr_caves):
            cave_points = self.__get_cave_points()
            #get the line between the points
            for index in range(1, len(cave_points)):
                point1 = cave_points[index - 1]
                point2 = cave_points[index]
                a, b = util.line_from_points(point1, point2)
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
                    matrix[min(y, int(con.BOARD_SIZE.height / con.BLOCK_SIZE.height) -1)][min(x, int(con.BOARD_SIZE.width / con.BLOCK_SIZE.width) - 1)] = "Air"
                    surrounding_coords = [coord for coord in self.__get_surrounding_block_coords(x, y) if coord is not None and matrix[coord[1]][coord[0]] != "Air"]
                    #extend the cave around the direct line.
                    while len(surrounding_coords) > 0:
                        if uniform(0, 1) < self.CAVE_STOP_SPREAD_CHANCE:
                            break
                        remove_block = choice(surrounding_coords)
                        surrounding_coords.remove(remove_block)
                        matrix[remove_block[1]][remove_block[0]] = "Air"
                        surrounding_coords.extend([coord for coord in self.__get_surrounding_block_coords(*remove_block) if coord is not None and matrix[coord[1]][coord[0]] != "Air"])
        return matrix

    def __get_cave_points(self):
        max_radius = int(min(*con.BOARD_SIZE) * self.POINT_FRACTION_DISTANCE)

        # random point on the board within 10% of the boundaries
        first_point = [randint(self.CAVE_X_BORDER_DISTANCE, con.BOARD_SIZE.width - self.CAVE_X_BORDER_DISTANCE),
                       randint(self.CAVE_Y_BORDER_DISTANCE, con.BOARD_SIZE.height - self.CAVE_Y_BORDER_DISTANCE)]
        cave_points = [first_point]
        prev_direction = uniform(0, 2 * pi)
        amnt_points = randint(self.NUMBER_OF_CAVE_POINTS - int(max(self.NUMBER_OF_CAVE_POINTS / 2, 1)), self.NUMBER_OF_CAVE_POINTS)
        while len(cave_points) < amnt_points:
            radius = randint(max(1, int(max_radius / 2)), max_radius)
            prev_direction = uniform(prev_direction - 0.5 * pi, prev_direction + 0.5 * pi)
            new_x = min(max(int(cave_points[-1][0] + cos(prev_direction) * radius), self.CAVE_X_BORDER_DISTANCE),
                        con.BOARD_SIZE.width - self.CAVE_X_BORDER_DISTANCE)
            new_y = min(max(int(cave_points[-1][1] + sin(prev_direction) * radius), self.CAVE_Y_BORDER_DISTANCE),
                        con.BOARD_SIZE.height - self.CAVE_Y_BORDER_DISTANCE)
            #make sure no double points and no straight lines
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
            # Make sure within range
            if surrounding_coord[0] >= con.BOARD_SIZE.width / con.BLOCK_SIZE.width or \
                    surrounding_coord[0] < 0 or \
                    surrounding_coord[1] >= con.BOARD_SIZE.height / con.BLOCK_SIZE.height or \
                    surrounding_coord[1] < 0:
                continue
            surrounding_coords[index] = surrounding_coord
        return surrounding_coords

    def __add_border(self, matrix):
        #north border
        rows = matrix[0:self.MAX_BORDER_SPREAD_DISTANCE]
        for row_i in range(len(rows)):
            border_block_chance = self.BORDER_SPREAD_LIKELYHOOD.cumulative_probability(row_i)
            for col_i in range(len(matrix[row_i])):
                if uniform(0, 1) < border_block_chance:
                    matrix[row_i][col_i] = "BorderMaterial"
        #south border
        rows = matrix[- (self.MAX_BORDER_SPREAD_DISTANCE + 1):-1]
        for row_i in range(len(rows)):
            border_block_chance = self.BORDER_SPREAD_LIKELYHOOD.cumulative_probability(row_i)
            for col_i in range(len(matrix[row_i])):
                if uniform(0, 1) < border_block_chance:
                    matrix[-(row_i + 1)][- (col_i + 1)] = "BorderMaterial"
        #east border
        for row_i in range(len(matrix)):
            for col_i in range(len(matrix[row_i][0:self.MAX_BORDER_SPREAD_DISTANCE])):
                border_block_chance = self.BORDER_SPREAD_LIKELYHOOD.cumulative_probability(col_i)
                if uniform(0, 1) < border_block_chance:
                    matrix[row_i][col_i] = "BorderMaterial"
        #west border
        for row_i in range(len(matrix)):
            for col_i in range(len(matrix[row_i][- (self.MAX_BORDER_SPREAD_DISTANCE + 1):-1])):
                border_block_chance = self.BORDER_SPREAD_LIKELYHOOD.cumulative_probability(col_i)
                if uniform(0, 1) < border_block_chance:
                    matrix[- (row_i + 1)][ - (col_i + 1)] = "BorderMaterial"

        return matrix
