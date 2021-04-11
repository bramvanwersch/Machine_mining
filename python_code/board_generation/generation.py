from random import randint, choices, uniform, choice
from math import pi, cos, sin, ceil, sqrt
from typing import List, Dict, Union, ClassVar, Set, Tuple, Iterable
from pygame import Rect

from utility import constants as con, utilities as util
import interfaces.interface_utility as interface_util
from block_classes import ground_materials, block_utility as block_util
import board_generation.biomes as biome_classes
import board_generation.structures.abandoned_mine


class BoardGenerator:
    """
    This class has 3 separate layers of generation:
    1. a broad layer that generates caves and environment far outside the visible surroudings. This is done to ensure
    that caves and structures are not forced to generate in a certain way because of how the player has explored
    2. a much smaller layer that generates special blocks that can span chunk borders. This layer goes one chunk
    further then the visible layer and ensures that things like ore clusters can be generated over chunk borders as well
    as bigger environment things.
    3. The smallest layer directly around the player that is generated as soon as a player enters a chunk that has no
    loaded chunk next to it.
    """
    # BIOME values
    # extend loading of biomes and structures by this much everytime terrain has to be loaded
    __EXTENDED_LOAD_AMOUNT: ClassVar[int] = 2000

    # the size of quadrants where a new biome is chosen
    BIOME_SIZES: ClassVar[Dict[str, util.Size]] = \
        {"tiny": util.Size(100, 100), "small": util.Size(200, 200), "normal": util.Size(500, 500),
         "big": util.Size(750, 7500), "massive": util.Size(1000, 1000), "huge": util.Size(1500, 1500),
         "just one pls": util.Size(3000, 3000)}  # in blocks

    # determines the standard deviation of the biomes, high values means very broad distributions
    BIOME_BLEND: ClassVar[Dict[str, int]] = \
        {"very low": 1, "low": 5, "normal": 15, "severe": 30, "extreme": 50, "what are biomes?": 100}

    # CAVE values
    MAX_CAVES: ClassVar[Dict[str, int]] = \
        {"one_caves": 1, "low": 5, "normal": 15, "lots": 30, "I WANT CAVES!!!": 50}  # per 100_000 blocks
    # the fraction of the distance between points based on the shortest side of the board
    MAX_POINT_DISTANCE: ClassVar[int] = 100
    # number of points a cave consists of
    CAVE_LENGTH: ClassVar[Dict[str, int]] = \
        {"short": 25, "normal": 50, "long": 100, "very long": 200, "when does it stop?": 500}
    # the chance for a cave to stop extending around its core. Do not go lower then 0.0005 --> takes a long time
    CAVE_STOP_SPREAD_CHANCE: ClassVar[Dict[str, int]] = \
        {"very thin": 0.1, "thin": 0.8, "normal": 0.05, "wide": 0.01, "very wide": 0.005}

    # BORDER values
    BORDER_SPREAD_LIKELYHOOD: ClassVar[util.Gaussian] = util.Gaussian(0, 2)
    MAX_BORDER_SPREAD_DISTANCE: ClassVar[int] = 4

    __environment_material_names: Set[str]
    __generated_chunks_matrix: List[List[int]]
    __predefined_blocks: "PredefinedBlocks"
    __minimum_generation_length: int
    __generation_rect: Rect

    __cave_length: int
    __cave_quadrant_size: util.Size
    __cave_stop_spread_chance: float

    __biome_definition: biome_classes.BiomeGenerationDefinition
    __biome_size: util.Size
    __biome_blend: int
    __biome_matrix: List[List[Union[biome_classes.Biome, None]]]

    def __init__(
        self,
        biome_generation_def: Union[biome_classes.BiomeGenerationDefinition, str] = None,
        biome_size: Union[str, util.Size] = "normal",
        biome_blend: Union[str, int] = "normal",
        nr_caves: Union[str, int] = "normal",
        cave_length: Union[str, int] = "normal",
        cave_broadness: Union[str, float] = "normal",
        progress_var: Union[None, List[str]] = None
    ):
        self.__environment_material_names = {mat.name() for mat in block_util.environment_materials}

        # for tracking what chunks have been covered by generation 0 is not covered 1 is covered by ores and environment
        # 2 is covered with filler blocks
        self.__generated_chunks_matrix = [[0 for _ in range(ceil(con.ORIGINAL_BOARD_SIZE.width / con.CHUNK_SIZE.width))]
                                          for _ in range(ceil(con.ORIGINAL_BOARD_SIZE.height / con.CHUNK_SIZE.height))]
        # structure for efficiently storing a variable number of blocks from a matrix that are not neccesairily
        # consecutive
        self.__predefined_blocks = PredefinedBlocks()

        # amount of cave points
        self.__cave_length = self.CAVE_LENGTH.get(cave_length, cave_length)
        # the square where one cave occurs
        self.__cave_quadrant_size = self.__determine_cave_quadrant_size(self.MAX_CAVES.get(nr_caves, nr_caves))
        self.__cave_stop_spread_chance = max(self.CAVE_STOP_SPREAD_CHANCE.get(cave_broadness, cave_broadness), 0.0005)

        # minimum distance (x and y) between the closest generated chunk and the non-generated structures and biomes
        self.__minimum_generation_length = ceil(self.__cave_length * self.MAX_POINT_DISTANCE)
        # tracks what part of the board the structures and biomes have been generated for.
        self.__generation_rect = Rect(
            (max(0, con.START_LOAD_AREA[0][0] * con.CHUNK_SIZE.width - self.__minimum_generation_length),
             max(0, con.START_LOAD_AREA[1][0] * con.CHUNK_SIZE.height - self.__minimum_generation_length),
             min(len(con.START_LOAD_AREA[0]) * con.CHUNK_SIZE.width + 2 * self.__minimum_generation_length,
                 con.ORIGINAL_BOARD_SIZE.width),
             min(len(con.START_LOAD_AREA[1]) * con.CHUNK_SIZE.height + 2 * self.__minimum_generation_length,
                 con.ORIGINAL_BOARD_SIZE.height))
        )

        self.__biome_definition = biome_generation_def if biome_generation_def else\
            biome_classes.NormalBiomeGeneration()
        self.__biome_size = self.BIOME_SIZES.get(biome_size, biome_size)
        self.__biome_blend = self.BIOME_BLEND.get(biome_blend, biome_blend)
        # fill the biome matrix with empty values
        self.__biome_matrix = [[None for _ in range(ceil(con.ORIGINAL_BOARD_SIZE.width / self.__biome_size.width))]
                               for _ in range(ceil(con.ORIGINAL_BOARD_SIZE.height / self.__biome_size.height))]

        self.__generate_biomes(self.__generation_rect, progress_var)
        self.__generate_structures(self.__generation_rect, progress_var)

    def generate_chunk(
        self,
        topleft: Union[Tuple[int, int], List[int]]
    ) -> Tuple[Union[None, List[List]], Union[None, List[List]]]:
        """Generate a chunk with the given topleft"""
        matrix = [[None for _ in range(interface_util.p_to_c(con.CHUNK_SIZE.width))]
                  for _ in range(interface_util.p_to_r(con.CHUNK_SIZE.height))]
        background_matrix = [[None for _ in range(interface_util.p_to_c(con.CHUNK_SIZE.width))]
                             for _ in range(interface_util.p_to_r(con.CHUNK_SIZE.height))]
        chunk_rect = Rect((topleft[0], topleft[1], con.CHUNK_SIZE.width, con.CHUNK_SIZE.height))
        chunk_coord = interface_util.p_to_cp(topleft)

        # if the chunk was already generated do not do it again
        if self.__generated_chunks_matrix[chunk_coord[1]][chunk_coord[0]] == 2:
            return None, None
        # extend structures as caves and biomes when needed
        self.__extend_surrounding_generation(chunk_rect)
        # generate ores and environment one chunk out from the generated boundary to allow generation over chunks
        self.__add_special_blocks(chunk_coord)
        # add all blocks that have been pre-defined by surrounding generation and ore and environment
        self.__add_pre_defined_blocks(chunk_rect, matrix)
        self.__add_filler_blocks(chunk_rect, matrix, background_matrix)
        self.__add_border(matrix, topleft)

        # save that this chunk was covered by generation
        self.__generated_chunks_matrix[chunk_coord[1]][chunk_coord[0]] = 2
        return matrix, background_matrix

# LAYER1: cave biome and structure generation
    def __extend_surrounding_generation(
        self,
        rect: Rect
    ) -> None:
        # check if surrounding generation needs to be extended
        if self.__generation_rect.top > 0 and \
                rect.top - self.__minimum_generation_length < self.__generation_rect.top:
            self.__generate_biome_structures("N")
        elif self.__generation_rect.right < con.ORIGINAL_BOARD_SIZE.width and \
                rect.right + self.__minimum_generation_length > self.__generation_rect.right:
            self.__generate_biome_structures("E")
        elif self.__generation_rect.bottom < con.ORIGINAL_BOARD_SIZE.height and \
                rect.bottom + self.__minimum_generation_length > self.__generation_rect.bottom:
            self.__generate_biome_structures("S")
        elif self.__generation_rect.left > 0 and \
                rect.left - self.__minimum_generation_length < self.__generation_rect.left:
            self.__generate_biome_structures("W")

    def __generate_biome_structures(
        self,
        direction: str
    ) -> None:
        """Generate biomes structures and environment to a certain direction with __EXTENDED_LOAD_AMOUNT"""
        # create a rectangle that does not overlap with the __generation_rectangle and extends one of four directions
        if direction == "N":
            rect = Rect(
                (self.__generation_rect.left,
                 max(0, self.__generation_rect.top - self.__EXTENDED_LOAD_AMOUNT),
                 self.__generation_rect.width,
                 min(self.__generation_rect.top, self.__EXTENDED_LOAD_AMOUNT))
            )
        elif direction == "E":
            rect = Rect(
                (min(con.ORIGINAL_BOARD_SIZE.width, self.__generation_rect.right + self.__EXTENDED_LOAD_AMOUNT),
                 self.__generation_rect.top,
                 min(con.ORIGINAL_BOARD_SIZE.width - self.__generation_rect.right, self.__EXTENDED_LOAD_AMOUNT),
                 self.__generation_rect.height)
            )
        elif direction == "S":
            rect = Rect(
                (self.__generation_rect.left,
                 min(con.ORIGINAL_BOARD_SIZE.height, self.__generation_rect.bottom + self.__EXTENDED_LOAD_AMOUNT),
                 self.__generation_rect.width,
                 min(con.ORIGINAL_BOARD_SIZE.height - self.__generation_rect.bottom, self.__EXTENDED_LOAD_AMOUNT))
            )
        elif direction == "W":
            rect = Rect(
                (max(0, self.__generation_rect.left - self.__EXTENDED_LOAD_AMOUNT),
                 self.__generation_rect.top,
                 min(self.__generation_rect.left, self.__EXTENDED_LOAD_AMOUNT),
                 self.__generation_rect.height)
            )
        else:
            raise util.GameException("Expected N, E, S or W not {}".format(direction))
        self.__generate_biomes(rect)
        self.__generate_structures(rect)
        self.__generation_rect.union_ip(rect)

    def __generate_biomes(
        self,
        rect: Rect,
        progress_var: Union[None, List[str]] = None
    ) -> None:
        """Fill the biome matrix within within the given rect with biome classes based using the __biome_definition"""
        row_start = int(rect.top / self.__biome_size.height)
        col_start = int(rect.left / self.__biome_size.width)

        total_biomes = int(rect.height / self.__biome_size.height) * int(rect.width / self.__biome_size.width)
        for row_i in range(ceil(rect.height / self.__biome_size.height)):
            for col_i in range(ceil(rect.width / self.__biome_size.width)):
                if progress_var:
                    current_biome_nr = (row_i * int(rect.width / self.__biome_size.width)) + col_i
                    progress_var[0] = f"Generating biome {current_biome_nr} out of {total_biomes}..."
                row_i += row_start
                col_i += col_start
                # allow the shapes of the distributions to be a bit different (more oval)
                sd_x = self.__biome_size.width * self.__biome_blend * uniform(0.6, 1.4)
                sd_y = self.__biome_size.height * self.__biome_blend * uniform(0.6, 1.4)
                # allow the distribution to be tilted
                cov1 = uniform(-sd_x, sd_x)
                cov2 = uniform(-sd_y, sd_y)
                mean_x = col_i * self.__biome_size.width + 0.5 * self.__biome_size.width
                mean_y = row_i * self.__biome_size.height + 0.5 * self.__biome_size.height

                # check depths in blocks
                biome_type = self.__biome_definition.get_biome(int(mean_y / con.BLOCK_SIZE.height))
                biome_instance = biome_type(util.Gaussian(mean_x, sd_x), util.Gaussian(mean_y, sd_y), cov1, cov2)
                self.__biome_matrix[row_i][col_i] = biome_instance

    def __generate_structures(
        self,
        rect: Rect,
        progress_var: Union[None, List[str]] = None
    ) -> None:
        """Generate caves and structures within a given rectangle and save them in a PredefinedBlocks structure"""
        row_start = int(rect.top / self.__cave_quadrant_size.height)
        col_start = int(rect.left / self.__cave_quadrant_size.width)
        total_caves = int(rect.height / self.__cave_quadrant_size.height) * \
                      int(rect.width / self.__cave_quadrant_size.width) # noqa
        for row_i in range(int(rect.height / self.__cave_quadrant_size.height)):
            for col_i in range(int(rect.width / self.__cave_quadrant_size.width)):
                if progress_var:
                    current_cave_nr = (row_i * int(rect.width / self.__cave_quadrant_size.width)) + col_i
                    progress_var[0] = f"Carving out cave {current_cave_nr} out of {total_caves}..."
                row_i += row_start
                col_i += col_start
                x_coord = randint(int(col_i * self.__cave_quadrant_size.height),
                                  int((col_i + 1) * self.__cave_quadrant_size.height))
                y_coord = randint(int(row_i * self.__cave_quadrant_size.width),
                                  int((row_i + 1) * self.__cave_quadrant_size.width))
                self.__generate_cave([x_coord, y_coord])

        # TODO temporary test remove later
        mine = board_generation.structures.abandoned_mine.AbandonedMineStructure()
        matrix = mine.get_structure_matrix()
        coord = [50, 50]
        for r_index, row in enumerate(matrix):
            for c_index, material in enumerate(row):
                self.__predefined_blocks.add((coord[0] + c_index, coord[1] + r_index), material)

    def __generate_cave(
        self,
        start_point: Union[Tuple[int, int], List[int]]
    ) -> None:
        """Add air spaces to the PredefinedBlocks instance"""
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
                matrix_x = min(x, int(con.ORIGINAL_BOARD_SIZE.width / con.BLOCK_SIZE.width) - 1)
                y = int(y_values[index2])
                matrix_y = min(y, int(con.ORIGINAL_BOARD_SIZE.height / con.BLOCK_SIZE.height) - 1)
                self.__predefined_blocks.add((matrix_x, matrix_y), "Air")
                surrounding_coords = \
                    [coord for coord in self.__get_surrounding_block_coords(x, y) if coord is not None
                     and not self.__predefined_blocks.check(coord, ["Air"])]
                # extend the cave around the direct line at random.
                while len(surrounding_coords) > 0:
                    if uniform(0, 1) < self.__cave_stop_spread_chance:
                        break
                    remove_coord = choice(surrounding_coords)
                    surrounding_coords.remove(remove_coord)
                    self.__predefined_blocks.add(remove_coord, "Air")
                    additional_surrounding_coords = \
                        [coord for coord in self.__get_surrounding_block_coords(*remove_coord) if coord is not None
                         and not self.__predefined_blocks.check(coord, ["Air"])]
                    surrounding_coords.extend(additional_surrounding_coords)

    def __get_cave_points(
        self,
        start_point: Union[Tuple[int, int], List[int]]
    ) -> List[List[int]]:
        """Get points from a start point within the con.BOARD_SIZE and shaped nicely"""
        cave_points = [start_point]
        prev_direction = uniform(0, 2 * pi)
        amnt_points = randint(int(max(self.__cave_length / 2, 1)), self.__cave_length)
        while len(cave_points) < amnt_points:
            radius = randint(max(1, int(self.MAX_POINT_DISTANCE / 2)), self.MAX_POINT_DISTANCE)
            prev_direction = uniform(prev_direction - 0.5 * pi, prev_direction + 0.5 * pi)
            new_x = min(max(int(cave_points[-1][0] + cos(prev_direction) * radius), 0), con.ORIGINAL_BOARD_SIZE.width)
            new_y = min(max(int(cave_points[-1][1] + sin(prev_direction) * radius), 0), con.ORIGINAL_BOARD_SIZE.height)
            # make sure no double points and no straight lines
            if [new_x, new_y] in cave_points or \
                    int(new_x / con.BLOCK_SIZE.width) == int(cave_points[-1][0] / con.BLOCK_SIZE.width) or \
                    int(new_y / con.BLOCK_SIZE.height) == int(cave_points[-1][1] / con.BLOCK_SIZE.height):
                continue
            cave_points.append([new_x, new_y])
        return [[int(x / con.BLOCK_SIZE.width), int(y / con.BLOCK_SIZE.height)] for x, y in cave_points]

    def __add_pre_defined_blocks(
        self, rect: Rect,
        matrix: List[List]
    ) -> None:
        """Get all predefined blocks in a rectangle and add them to matrix"""
        for row_i in range(int(rect.height / con.BLOCK_SIZE.height)):
            for col_i in range(int(rect.width / con.BLOCK_SIZE.width)):
                block_x_coord = int(rect.left / con.BLOCK_SIZE.width) + col_i
                block_y_coord = int(rect.top / con.BLOCK_SIZE.height) + row_i
                # add pre_defined_blocks
                if (block_x_coord, block_y_coord) in self.__predefined_blocks:
                    matrix[row_i][col_i] = self.__predefined_blocks.get((block_x_coord, block_y_coord))

# LAYER2: special block generation that can cross chunk borders
    def __add_special_blocks(
        self,
        chunk_coord: Union[Tuple[int, int], List[int]]
    ) -> None:
        """Add blocks that span accros chunks but are not bigger then a chunk"""
        # check in a 3 * 3 around the chunk_coord if there is still special blocks to generate
        for chunk_row in \
                range(max(0, chunk_coord[1] - 1),
                      min(chunk_coord[1] + 2, ceil(con.ORIGINAL_BOARD_SIZE.height / con.CHUNK_SIZE.height) - 1)):
            for chunk_col in \
                    range(max(0, chunk_coord[0] - 1),
                          min(chunk_coord[0] + 2, ceil(con.ORIGINAL_BOARD_SIZE.width / con.CHUNK_SIZE.width) - 1)):
                if self.__generated_chunks_matrix[chunk_row][chunk_col] != 0:
                    continue
                rect = Rect((chunk_col * con.CHUNK_SIZE.width, chunk_row * con.CHUNK_SIZE.height,
                             con.CHUNK_SIZE.width, con.CHUNK_SIZE.height))
                for row_i in range(int(rect.height / con.BLOCK_SIZE.height)):
                    for col_i in range(int(rect.width / con.BLOCK_SIZE.width)):
                        block_x_coord = int(rect.left / con.BLOCK_SIZE.width) + col_i
                        block_y_coord = int(rect.top / con.BLOCK_SIZE.height) + row_i
                        # determine biome based on coordinate

                        biome_liklyhoods = self.__biome_liklyhoods_from_point(block_x_coord * con.BLOCK_SIZE.width,
                                                                              block_y_coord * con.BLOCK_SIZE.height)
                        biome = choices(list(biome_liklyhoods.keys()), list(biome_liklyhoods.values()), k=1)[0]
                        # only add plants in caves
                        if self.__predefined_blocks.check((block_x_coord, block_y_coord), ["Air"]) \
                                and uniform(0, 1) < biome.FLORA_LIKELYHOOD:
                            flora_likelyhoods = biome.get_flora_lh_at_depth(block_y_coord)
                            self.__add_environment(block_x_coord, block_y_coord, flora_likelyhoods)
                        elif uniform(0, 1) < biome.CLUSTER_LIKELYHOOD:
                            ore_likelyhoods = biome.get_ore_lh_at_depth(block_y_coord)
                            self.__add_ore_cluster(block_x_coord, block_y_coord, ore_likelyhoods,
                                                   biome.MAX_CLUSTER_SIZE)
                self.__generated_chunks_matrix[chunk_row][chunk_col] = 1

    def __add_environment(
        self,
        block_x_coord: int,
        block_y_coord: int,
        flora_likelyhoods: List[Dict[str, float]]
    ) -> None:
        """Add environment blocks like plants"""
        s_coords = self.__get_surrounding_block_coords(block_x_coord, block_y_coord)
        elligable_indexes = []
        for coord in s_coords:
            try:
                if coord is not None and \
                        not self.__predefined_blocks.check(coord, {"Air", *self.__environment_material_names}):
                    elligable_indexes.append(coord)
            except IndexError:
                # ignore coords outside the chunk to not cover them twice
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
        self.__predefined_blocks.add((block_x_coord, block_y_coord), flora, overwrite=False)

    def __add_ore_cluster(
        self,
        block_x_coord: int,
        block_y_coord: int,
        ore_likelyhoods: Dict[str, float],
        max_cluster_size: int
    ) -> None:
        """Add ores in a cluster"""
        ore = choices(list(ore_likelyhoods.keys()), list(ore_likelyhoods.values()), k=1)[0]
        ore_locations = self.__create_ore_cluster(ore, (block_x_coord, block_y_coord), max_cluster_size)
        ore_locations.append([block_x_coord, block_y_coord])
        for loc in ore_locations:
            if self.__predefined_blocks.check((block_x_coord, block_y_coord), ["Air"]):
                continue
            self.__predefined_blocks.add(loc, ore, overwrite=False)

    def __create_ore_cluster(
        self,
        ore: str,
        center: Union[Tuple[int, int], List[int]],
        max_cluster_size: int
    ) -> List[List[int]]:
        """Create a cluster of ores around a center up until a certain size is reached"""
        size = getattr(ground_materials, ore).get_cluster_size()  # -> this number is a random return
        ore_locations = []
        while len(ore_locations) <= size:
            location = [0, 0]
            for index in range(2):
                pos = choice([-1, 1])
                # assert index is bigger then 0
                location[index] = max(0, pos * randint(0, max_cluster_size) + center[index])
            if location not in ore_locations:
                ore_locations.append(location)
        return ore_locations

# LAYER3: filler blocks that fill in the rest of the chunk
    def __add_filler_blocks(
        self,
        rect: Rect,
        matrix: List[List],
        background_matrix: List[List]
    ) -> None:
        """Add blocks to all unfilled places in the matrix and to the background matrix"""
        for row_i in range(int(rect.height / con.BLOCK_SIZE.height)):
            for col_i in range(int(rect.width / con.BLOCK_SIZE.width)):
                block_x_coord = int(rect.left / con.BLOCK_SIZE.width) + col_i
                block_y_coord = int(rect.top / con.BLOCK_SIZE.height) + row_i
                block = matrix[row_i][col_i]
                # determine biome based on coordinate
                biome_liklyhoods = self.__biome_liklyhoods_from_point(block_x_coord * con.BLOCK_SIZE.width,
                                                                      block_y_coord * con.BLOCK_SIZE.height)
                biome = choices(list(biome_liklyhoods.keys()), list(biome_liklyhoods.values()), k=1)[0]
                if block is None:
                    filler_likelyhoods = biome.get_filler_lh_at_depth(block_y_coord)
                    filler = choices(list(filler_likelyhoods.keys()), list(filler_likelyhoods.values()), k=1)[0]
                    matrix[row_i][col_i] = filler
                # reget the biome to get slightly different front and backgrounds
                biome = choices(list(biome_liklyhoods.keys()), list(biome_liklyhoods.values()), k=1)[0]
                background_likelyhoods = biome.get_background_lh_at_depth(block_y_coord)
                background_mat = choices(list(background_likelyhoods.keys()),
                                         list(background_likelyhoods.values()), k=1)[0]
                background_matrix[row_i][col_i] = background_mat

    def __add_border(
        self,
        matrix: List[List],
        topleft: Union[Tuple[int, int], List[int]]
    ) -> None:
        """add a border if neccesairy and determine the direction of set border"""
        if topleft[1] <= 0:
            self.__add_directional_border(matrix, "north")
        elif topleft[1] + con.CHUNK_SIZE.height >= con.ORIGINAL_BOARD_SIZE.height:
            self.__add_directional_border(matrix, "south")
        if topleft[0] <= 0:
            self.__add_directional_border(matrix, "west")
        elif topleft[0] + con.CHUNK_SIZE.width >= con.ORIGINAL_BOARD_SIZE.width:
            self.__add_directional_border(matrix, "east")

    def __add_directional_border(
        self,
        matrix: List[List],
        direction: str
    ) -> None:
        """Add a border for a certain direction"""
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
        elif direction == "west":
            for row_i in range(len(matrix)):
                for col_i in range(len(matrix[row_i][0:self.MAX_BORDER_SPREAD_DISTANCE])):
                    border_block_chance = self.BORDER_SPREAD_LIKELYHOOD.cumulative_probability(col_i)
                    if uniform(0, 1) < border_block_chance:
                        matrix[row_i][col_i] = "BorderMaterial"
        elif direction == "east":
            for row_i in range(len(matrix)):
                for col_i in range(len(matrix[row_i][- (self.MAX_BORDER_SPREAD_DISTANCE + 1):-1])):
                    border_block_chance = self.BORDER_SPREAD_LIKELYHOOD.cumulative_probability(col_i)
                    if uniform(0, 1) < border_block_chance:
                        matrix[- (row_i + 1)][- (col_i + 1)] = "BorderMaterial"
        else:
            raise util.GameException("Unrecognized direction for border: {}".format(direction))

# utility methods
    def __determine_cave_quadrant_size(
        self,
        caves_nr: int
    ) -> util.Size:
        total_blocks = (con.ORIGINAL_BOARD_SIZE.width / con.BLOCK_SIZE.width) *\
                       (con.ORIGINAL_BOARD_SIZE.height / con.BLOCK_SIZE.height)
        total_caves = (total_blocks / 100_000) * caves_nr
        # Me brother : )
        cave_quadrant_side = int(sqrt((con.ORIGINAL_BOARD_SIZE.width * con.ORIGINAL_BOARD_SIZE.height) / total_caves))
        return util.Size(cave_quadrant_side, cave_quadrant_side)

    def __biome_liklyhoods_from_point(
        self,
        x: int,
        y: int
    ) -> Dict[biome_classes.Biome, float]:
        biome_matrix_col = int(x / self.__biome_size.width)
        biome_matrix_row = int(y / self.__biome_size.height)
        main_biome = self.__biome_matrix[biome_matrix_row][biome_matrix_col]
        surrounding_biomes = [main_biome]
        # collect all surrounding biomes
        for new_position in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            surrounding_coord = [biome_matrix_col + new_position[0], biome_matrix_row + new_position[1]]
            if surrounding_coord[0] >= len(self.__biome_matrix[0]) - 1 or surrounding_coord[0] < 0 \
                    or surrounding_coord[1] >= len(self.__biome_matrix) - 1 or surrounding_coord[1] < 0:
                continue
            surrounding_biomes.append(self.__biome_matrix[surrounding_coord[1]][surrounding_coord[0]])
        surrounding_biomes = [b for b in surrounding_biomes if b is not None]
        wheights = util.normalize([b.get_likelyhood_at_coord(x, y) for b in surrounding_biomes])
        biome_likelyhoods = {biome: wheights[index] for index, biome in enumerate(surrounding_biomes)}
        return biome_likelyhoods

    def __get_surrounding_block_coords(
        self,
        x: int,
        y: int
    ) -> List[Union[List[int], None]]:
        surrounding_coords = [None for _ in range(4)]
        for index, new_position in enumerate([(0, -1), (1, 0), (0, 1), (-1, 0)]):
            surrounding_coord = [x + new_position[0], y + new_position[1]]
            # Make sure within range
            if surrounding_coord[0] >= con.ORIGINAL_BOARD_SIZE.width / con.BLOCK_SIZE.width or \
                    surrounding_coord[0] < 0 or \
                    surrounding_coord[1] >= con.ORIGINAL_BOARD_SIZE.height / con.BLOCK_SIZE.height or \
                    surrounding_coord[1] < 0:
                continue
            surrounding_coords[index] = surrounding_coord  # noqa --> because there seems no reason for complaint here
        return surrounding_coords


class PredefinedBlocks:
    """Save at what coordinate there are pre_defined materials for blocks generated outside the matrixes directly
    generated"""
    __internal_tree: Dict[int, Dict[int, str]]

    def __init__(self):
        self.__internal_tree = {}

    def add(
        self,
        coord: Union[Tuple[int, int], List[int]],
        value: str,
        overwrite=True
    ) -> None:
        if coord[1] in self.__internal_tree:
            # do not overwrite if requested
            if not overwrite and coord[0] in self.__internal_tree[coord[1]]:
                return
            self.__internal_tree[coord[1]][coord[0]] = value
        else:
            if coord[1] > con.MAX_DEPTH:
                print("Carefull {} is outside the board".format(coord))
                return
            self.__internal_tree[coord[1]] = {coord[0]: value}

    def get(
        self,
        coord: Union[Tuple[int, int], List[int]]
    ) -> str:
        """Get and remove an item from this collection, for checking use check or 'in'"""
        return self.__internal_tree[coord[1]].pop(coord[0])

    def check(
        self,
        coord: Union[Tuple[int, int], List[int]],
        values: Iterable
    ) -> bool:
        return coord in self and any(value == self.__internal_tree[coord[1]][coord[0]] for value in values)

    def __contains__(
        self,
        item: Union[Tuple[int, int], List[int]]
    ) -> bool:
        return item[1] in self.__internal_tree and item[0] in self.__internal_tree[item[1]]
