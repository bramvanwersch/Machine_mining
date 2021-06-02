import random
from typing import List, Dict, Union, ClassVar, Set, TYPE_CHECKING, Tuple, Any

import utility.constants as con
import utility.utilities as util
import interfaces.windows.interface_utility as interface_util
from utility import loading_saving
if TYPE_CHECKING:
    from block_classes import blocks
    import pygame


class PathFinder:
    """Pathfinder object for continiously mapping the current board to a network of rectangles and finding paths using
    that network.

    TODO: pathfinding will be done repeadatly if there is no possible but the start and end rectangle are valid. This
     can slow down the game significantly because a far distance is checked repeadetly
    """
    DIRECTIONS: ClassVar[List[str]] = ["N", "E", "S", "W"]
    pathfinding_tree: "PathfindingTree"

    def __init__(self):
        self.pathfinding_tree = PathfindingTree()

    def update(self):
        """Update all the pathfinding chunks"""
        for pf_chunk in self.pathfinding_tree.pathfinding_chunks:
            pf_chunk.update()

    def get_path(
        self,
        start_rect: "pygame.Rect",
        end_rect: "pygame.Rect"
    ) -> Union[None, "Path"]:
        """Get a Path or None from the starting rectangle to the end rectangle.

        The start rectangle has to be within a transparant rectangle of the pathfinding tree. The end rectangle can be
        within a non-transparant block but has to be side by side with a transparant block"""
        # find start rectangle
        direction_index = interface_util.relative_closest_direction(start_rect.center)
        found = False
        for key in self.pathfinding_tree.rectangle_network[direction_index]:
            if (direction_index == 0 and key < start_rect.centery) or \
                    (direction_index == 1 and key > start_rect.centerx) or \
                    (direction_index == 2 and key > start_rect.centery) or \
                    (direction_index == 3 and key < start_rect.centerx):
                adjacent_rects = self.pathfinding_tree.rectangle_network[direction_index][key]
            else:
                continue
            for rect in adjacent_rects:
                if rect.collidepoint(start_rect.center):
                    start_rect = rect
                    found = True
                    break
            if found:
                break
        if not found:
            return None

        # check if there is a rectangle next to the end rectangle
        can_find = False
        for index, direction_size in enumerate((end_rect.top, end_rect.right, end_rect.bottom, end_rect.left)):
            if direction_size in self.pathfinding_tree.rectangle_network[index - 2]:
                for rect in self.pathfinding_tree.rectangle_network[index - 2][direction_size]:
                    if util.side_by_side(end_rect, rect) is not None:
                        can_find = True
                        break
                if can_find:
                    break
        # there is no rectangle adjacent that could find a path
        if not can_find:
            return None
        end_node = self.__pathfind(start_rect, end_rect)
        if not end_node:
            return None
        path = self.__retrace_path(end_node, start_rect.topleft)
        return path

    def __retrace_path(
        self,
        node: "Node",
        start: Tuple[int, int]
    ) -> "Path":
        """Retraces the path from the last node of the pathfinding algorithm to the first node in the chain

        The direction of connection is used to determine the coordinates to move to in the current node.rect that
        results in a path trough the node.rect that ends at a location that is open to the connecting rect."""
        path = Path(start)
        prev_node = node
        node = node.parent
        while node is not None:
            direction = self.DIRECTIONS[prev_node.direction_index]
            if direction in ["N", "S"]:
                if direction == "N":
                    y = prev_node.rect.bottom
                else:
                    y = prev_node.rect.top - con.BLOCK_SIZE.height
                y = [y, y]
                x = [max(prev_node.rect.left, node.rect.left),
                     min(prev_node.rect.right, node.rect.right - con.BLOCK_SIZE.width)]
            elif direction in ["E", "W"]:
                if direction == "E":
                    x = prev_node.rect.left - con.BLOCK_SIZE.width
                else:
                    x = prev_node.rect.right
                x = [x, x]
                y = [max(prev_node.rect.top, node.rect.top),
                     min(prev_node.rect.bottom, node.rect.bottom) - con.BLOCK_SIZE.height]
            else:
                raise util.GameException("Invalid direction")
            path.append([x, y])
            prev_node = node
            node = node.parent
        return path

    def __pathfind(
        self,
        start: "pygame.Rect",
        end: "pygame.Rect"
    ) -> Union[None, "Node"]:
        """
        Find a path from a starting rectangle to an end rectangle by traversing the rectangle network using the A*
        pathfinding algorithm aproach

        Inspired and derived from:
        https://gist.github.com/Nicholas-Swift/003e1932ef2804bebef2710527008f44#file-astar-py
        """

        # Create start and end node
        start_node = Node(None, start, None)
        start_node.distance_from_start = start_node.total_for_both = 0
        end_node = Node(None, end, None)
        end_node.distance_from_start = end_node.distance_to_end = end_node.total_for_both = 0
        start_node.distance_to_end = util.manhattan_distance(start_node.position, end_node.position)
        if start == end:
            return end_node
        # Initialize both open and closed list
        open_list = []
        closed_list = []

        # Add the start node
        open_list.append(start_node)

        # Loop until you find the end
        while len(open_list) > 0:

            # Get the current node with lowest f
            current_node = open_list[0]
            current_index = 0
            for index, item in enumerate(open_list):
                if item.total_for_both < current_node.total_for_both:
                    current_node = item
                    current_index = index

            # Pop current off open list, add to closed list
            open_list.pop(current_index)
            closed_list.append(current_node)

            # Found the goal on block infront of destination
            connection_direction = util.side_by_side(current_node.rect, end_node.rect)
            if connection_direction is not None:
                end_node.parent = current_node
                end_node.direction_index = connection_direction
                return end_node

            # Generate children
            children = []
            for direction_index, direction in enumerate(current_node.rect.connecting_rects):
                for rect in direction:
                    # Create new node
                    new_node = Node(current_node, rect, direction_index)

                    # Append
                    children.append(new_node)

            # Loop through children
            for child in children:

                # Child is on the closed list
                if len([closed_child for closed_child in closed_list if closed_child.rect == child.rect]) > 0:
                    continue

                child.distance_from_start = current_node.distance_from_start +\
                                util.manhattan_distance(child.position, current_node.position) # noqa --> this shit is stupid
                child.distance_to_end = util.manhattan_distance(child.position, end_node.position)
                child.total_for_both = child.distance_from_start + child.distance_to_end

                # Child is already in the open list
                if len([open_node for open_node in open_list if child.rect == open_node.rect]) > 0:
                    continue

                # Add the child to the open list
                open_list.append(child)
        return None


class Path(loading_saving.Loadable, loading_saving.Savable):
    """Track a path and its lenght"""
    start_location: Union[Tuple[int, int], List[int]]
    __coordiantes: List[List[List[int]]]
    __length: float

    def __init__(
        self,
        start: Union[Tuple[int, int], List[int]]
    ):
        self.start_location = start
        self.__coordinates = []  # coordinates that give an allowed range
        self.__length = 0

    def __init_load__(self, start_location, coordinates, length):
        self.start_location = start_location
        self.__coordinates = coordinates
        self.__length = length

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_location": self.start_location,
            "coordinates": self.__coordinates,
            "length": self.__length
        }

    @classmethod
    def from_dict(cls, dct):
        return cls.load(**dct)

    def append(
        self,
        point: List[List[int]]
    ):
        """Add a value to the path"""
        self.__coordinates.append(point)
        # distance will be zero for the first addition
        point1 = (sum(point[0]) / 2, sum(point[1]) / 2)
        point2 = (sum(self.__coordinates[-1][0]) / 2, sum(self.__coordinates[-1][1]) / 2)
        self.__length += util.manhattan_distance(point1, point2)

    def pop(
        self,
        index: int = -1
    ) -> List[List[int]]:
        """Pop the last item of the list"""
        return self.__coordinates.pop(index)

    def __getitem__(self, item) -> Any:
        return self.__coordinates[item]

    def __len__(self) -> float:
        return len(self.__coordinates)

    @property
    def path_lenght(self):
        """Give the length of the full path from the location of the path that is available"""
        return self.__length + util.manhattan_distance(self.__coordinates[-1], self.start_location)


class Node:
    """Node class for the A* pathfinding. Saves nodes with an AirRectangle Object and a direction index for tracing
    back the path"""
    parent: Union[None, "Node"]
    rect: Union["AirRectangle", "pygame.Rect"]
    direction_index: Union[None, int]
    distance_from_start: int
    distance_to_end: int
    total_for_both: int

    def __init__(
        self,
        parent: Union[None, "Node"],
        rect: Union["AirRectangle", "pygame.Rect"],
        direction_index: Union[int, None]
    ):
        self.parent = parent  # node that comes before this node
        self.rect = rect  # the rectangle of this node
        self.direction_index = direction_index  # the direction from the parent node to this Node

        self.distance_from_start = 0
        self.distance_to_end = 0
        self.total_for_both = 0

    @property
    def position(self) -> Tuple[int, int]:
        """Give the topleft position of the entity within this node based on the parent node"""
        if self.direction_index is None:
            return self.rect.center
        elif self.direction_index == 0:
            return self.rect.centerx, self.rect.bottom
        elif self.direction_index == 1:
            return self.rect.right, self.rect.centery
        elif self.direction_index == 2:
            return self.rect.centerx, self.rect.top - con.BLOCK_SIZE.height
        elif self.direction_index == 3:
            return self.rect.left - con.BLOCK_SIZE.width, self.rect.centery


class PathfindingTree:
    """Collections of all rectangle chunks into one tree to be accessed by the pathfinding class"""
    rectangle_network: List[Dict]
    pathfinding_chunks: List["PathfindingChunk"]

    def __init__(self):
        # shared dictionary that acts as the tree of connections between rectangles in the chunks
        self.rectangle_network = [{}, {}, {}, {}]
        self.pathfinding_chunks = []

    def add_chunk(
        self,
        pf_chunk: "PathfindingChunk"
    ):
        self.pathfinding_chunks.append(pf_chunk)
        pf_chunk.configure(self.rectangle_network)


class PathfindingChunk:
    """Class for tracking rectangles used in pathfinding trough the chunk associated with this pathfinding chunk. This
    class needs updates and is updated from the board.

    TODO: see if it is possible to avoid recalculating the full chunk every so often. At the moment the fast methods
     are not consistent enough en will create to many rectangles. On the other hand the performance seems to not be
     affected to much
    """
    matrix: List[List["blocks.Block"]]
    rectangle_network: Union[List[Dict], None]
    __local_rectangles: Set["AirRectangle"]
    added_rects: List["pygame.Rect"]
    removed_rects: List["pygame.Rect"]
    __time_passed: List[int]

    def __init__(
        self,
        matrix: List[List["blocks.Block"]]
    ):
        # matrix of a chunk
        self.matrix = matrix
        self.rectangle_network = None

        self.__local_rectangles = set()  # rectangles only present in this chunk
        self.added_rects = []  # list where rectangles can be added that need to be updated
        self.removed_rects = []  # list where rectangles can be added that need to be removed
        # make sure that the updates are not synchronized
        self.__time_passed = [random.randint(0, con.PF_UPDATE_TIME), con.PF_UPDATE_TIME]

    def configure(
        self,
        rectangles: List[Dict]
    ):
        """Innitially configure this pathfindign chunk"""
        self.rectangle_network = rectangles
        covered_coordinates = [[False for _ in range(len(self.matrix[0]))] for _ in range(len(self.matrix))]

        # innitial configuration
        self.get_air_rectangles(self.matrix, covered_coordinates)

    def update(self):
        """Add rectangles when they are available and recalculate the pathfinding chunk every second to fix small
        mistakes that the fast adding makes"""
        self.__time_passed[0] += con.GAME_TIME.get_time()
        # fix mistakes in the fast updating
        if self.__time_passed[0] > self.__time_passed[1] and \
                (len(self.removed_rects) > 0 or len(self.added_rects) > 0):
            self.__time_passed[0] = 0
            for rect in self.__local_rectangles.copy():
                self.__remove_rectangle(rect)
            covered_coordinates = [[False for _ in range(len(self.matrix[0]))] for _ in range(len(self.matrix))]

            # innitial configuration
            self.get_air_rectangles(self.matrix, covered_coordinates)
            self.added_rects = []
            self.removed_rects = []
        else:
            if len(self.removed_rects) > 0:
                for rect in self.removed_rects:
                    sub_matrix, covered_coordinates = self.__find_removal_sub_matrix(rect)
                    self.get_air_rectangles(sub_matrix, covered_coordinates)
                    self.removed_rects.remove(rect)
            if len(self.added_rects) > 0:
                for rect in self.added_rects:
                    sub_matrix, covered_coordinates = self.__find_add_sub_matrix(rect)
                    self.get_air_rectangles(sub_matrix, covered_coordinates)
                    self.added_rects.remove(rect)

    def __find_add_sub_matrix(
        self,
        rect: "pygame.Rect"
    ) -> Tuple[List[List], List[List[bool]]]:
        adjacent_rectangles = []

        corners = [rect.left, rect.top, rect.bottom, rect.right]
        direction_index = interface_util.relative_closest_direction(rect.center)
        all_found = False
        for key in self.rectangle_network[direction_index]:
            if (direction_index == 0 and key < rect.centery) or (direction_index == 1 and key > rect.centerx) or\
                    (direction_index == 2 and key > rect.centery) or (direction_index == 3 and key < rect.centerx):
                adjacent_rects = self.rectangle_network[direction_index][key].copy()
            else:
                continue
            for adj_rect in adjacent_rects:
                # rectangles in different chunks do not take the matrix
                if interface_util.p_to_cp(adj_rect.topleft) != interface_util.p_to_cp(rect.topleft):
                    continue
                if adj_rect.colliderect(rect):
                    adjacent_rectangles.append(adj_rect)
                    self.__remove_rectangle(adj_rect)
                    if adj_rect.left < corners[0]:
                        corners[0] = adj_rect.left
                    if adj_rect.top < corners[1]:
                        corners[1] = adj_rect.top
                    if adj_rect.bottom > corners[2]:
                        corners[2] = adj_rect.bottom
                    if adj_rect.right > corners[3]:
                        corners[3] = adj_rect.right
                    if adj_rect.contains(rect):
                        all_found = True
                        break
            if all_found:
                break
        all_rectangles = [rect] + adjacent_rectangles
        return self.__sub_matrix_from_corners(corners, all_rectangles)

    def __find_removal_sub_matrix(
        self,
        rect: "pygame.Rect"
    ) -> Tuple[List[List], List[List[bool]]]:
        adjacent_rectangles = []

        # find all adacent rectangles and the box that contains them all
        corners = [rect.left, rect.top, rect.bottom, rect.right]
        for index, direction_size in enumerate((rect.top, rect.right, rect.bottom, rect.left)):
            if direction_size not in self.rectangle_network[index - 2]:
                continue
            for adj_rect in self.rectangle_network[index - 2][direction_size].copy():
                # rectangles in different chunks do not take the matrix
                if interface_util.p_to_cp(adj_rect.topleft) != interface_util.p_to_cp(rect.topleft):
                    continue
                if util.side_by_side(rect, adj_rect) is not None:
                    if adj_rect.left < corners[0]:
                        corners[0] = adj_rect.left
                    if adj_rect.top < corners[1]:
                        corners[1] = adj_rect.top
                    if adj_rect.bottom > corners[2]:
                        corners[2] = adj_rect.bottom
                    if adj_rect.right > corners[3]:
                        corners[3] = adj_rect.right
                    adjacent_rectangles.append(adj_rect)
                    self.__remove_rectangle(adj_rect)

        # get the sub matrix and all coordinates that are transaparant but do not need recalculation
        all_rectangles = [rect] + adjacent_rectangles
        return self.__sub_matrix_from_corners(corners, all_rectangles)

    def __sub_matrix_from_corners(
        self,
        corners: List[int],
        all_rectangles: List["pygame.Rect"]
    ) -> Tuple[List[List], List[List[bool]]]:
        start_column, start_row = (int((corners[0] % con.CHUNK_SIZE.width) / con.BLOCK_SIZE.width),
                                   int((corners[1] % con.CHUNK_SIZE.height) / con.BLOCK_SIZE.height))
        row_lenght = interface_util.p_to_r(corners[3] - corners[0])
        column_lenght = interface_util.p_to_c(corners[2] - corners[1])
        sub_matrix = []
        covered_coordinates = [[False for _ in range(row_lenght)] for _ in range(column_lenght)]
        for row_index in range(column_lenght):
            row = self.matrix[start_row + row_index][start_column:start_column + row_lenght]
            sub_matrix.append(row)
            for col_index, block in enumerate(row):
                # if transparant block in sub matrix but not adjacent pre ignore it.
                if block.transparant_group != 0 and block.rect.collidelist(all_rectangles) == -1:
                    covered_coordinates[row_index][col_index] = True
        return sub_matrix, covered_coordinates

    def __add_rectangle(
        self,
        rect: "AirRectangle"
    ):
        self.__local_rectangles.add(rect)
        for index, direction_size in enumerate((rect.top, rect.right, rect.bottom, rect.left)):
            if direction_size in self.rectangle_network[index]:
                self.rectangle_network[index][direction_size].add(rect)
            else:
                self.rectangle_network[index][direction_size] = {rect}
            # add connections
            if direction_size in self.rectangle_network[index - 2]:
                for adj_rect in self.rectangle_network[index - 2][direction_size].copy():
                    if util.side_by_side(rect, adj_rect) is not None:
                        rect.connecting_rects[index].add(adj_rect)
                        adj_rect.connecting_rects[index - 2].add(rect)

    def __remove_rectangle(
        self,
        rect: "AirRectangle"
    ):
        # TODO this failsafe should not be neccesairy
        if rect in self.__local_rectangles:
            self.__local_rectangles.remove(rect)
            rect.delete()
            direction_sizes = (rect.top, rect.right, rect.bottom, rect.left)
            for i in range(4):
                self.rectangle_network[i][direction_sizes[i]].remove(rect)

    def get_air_rectangles(
        self,
        block_matrix: List[List["blocks.Block"]],
        covered_coordinates: List[List[bool]]
    ):
        # covered coordinates is a matrix with the same amount of rows and column coords for all checked coords.

        # find all rectangles in the block matrix
        for n_row, row in enumerate(block_matrix):
            for n_col, block in enumerate(row):
                # find solid block
                if block.is_solid() or covered_coordinates[n_row][n_col]:
                    continue

                sub_matrix = [sub_row[n_col:] for sub_row in block_matrix[n_row:]]
                sub_covered_matrix = [sub_row[n_col:] for sub_row in covered_coordinates[n_row:]]
                lm_coord = self.__find_air_rectangle(sub_matrix, sub_covered_matrix)

                # add newly covered coordinates
                for x in range(lm_coord[0] + 1):
                    for y in range(lm_coord[1] + 1):
                        covered_coordinates[n_row + y][n_col + x] = True

                # add the air rectangle to the list of rectangles
                air_matrix = [sub_row[n_col:n_col + lm_coord[0] + 1] for sub_row in
                              block_matrix[n_row:n_row + lm_coord[1] + 1]]
                rect = AirRectangle(util.rect_from_block_matrix(air_matrix))
                self.__add_rectangle(rect)

    def __find_air_rectangle(
        self,
        block_matrix: List[List["blocks.Block"]],
        covered_coordinates: List[List[bool]]
    ) -> List[int]:
        """Find starting from a transparant block all the same transparant  block_classes in a rectangle given
         a certain matrix"""
        # first find how far the column is filled cannot fill on 0 since 0 is guaranteed to be a air block
        x_size = 0
        group = block_matrix[0][0].transparant_group
        for n_col, block in enumerate(block_matrix[0][1:]):
            if block.transparant_group != group or covered_coordinates[0][n_col + 1]:
                break
            x_size += 1
        matrix_coordinate = [x_size, 0]

        # skip the first row since this was checked already
        block = None
        for n_row, row in enumerate(block_matrix[1:]):
            n_col = 0
            for n_col, block in enumerate(row[:x_size + 1]):
                if block.transparant_group != group or covered_coordinates[n_row][n_col]:
                    break
            if block.transparant_group != group or covered_coordinates[n_row][n_col]:
                break
            matrix_coordinate[1] += 1
        return matrix_coordinate


class AirRectangle:
    """Pygame rectangle that tracks the rectangles it is connected to in a network of rectangles. This is a simple
    wrapper of a pygame rectangle that includes connecting rectangles."""
    rect: "pygame.Rect"
    connected_rects: List[Set]

    def __init__(
        self,
        rect: "pygame.Rect"
    ):
        self.rect = rect
        # all AirRectangles connected to this one. Connections are always 2 ways in the order N, E, S, W
        self.connecting_rects = [set() for _ in range(4)]

    def delete(self):
        """delete any reference from connecting rectangles"""
        for direction_index in range(len(self.connecting_rects)):
            for connection in self.connecting_rects[direction_index]:
                connection.connecting_rects[direction_index - 2].remove(self)

    def __getattr__(self, item) -> Any:
        return getattr(self.rect, item)

    def __str__(self) -> str:
        return str(self.rect)
