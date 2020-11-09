import random

from utility.constants import BLOCK_SIZE, CHUNK_SIZE, BOARD_SIZE, GAME_TIME, PF_UPDATE_TIME
from utility.utilities import rect_from_block_matrix, manhattan_distance, side_by_side
from interfaces.interface_utility import p_to_r, p_to_c, relative_closest_direction, p_to_cp

class PathFinder:
    """
    Pathfinder object for continiously mapping the current board to a network
    of rectangles and finding paths using that network
    """
    DIRECTIONS = ["N", "E", "S", "W"]
    def __init__(self):
        self.pathfinding_tree = PathfindingTree()

    def update(self):
        for pf_chunk in self.pathfinding_tree.pathfinding_chunks:
            pf_chunk.update()

    def get_path(self, start, end_rect):
        """
        Pathfinds a path between the start and end rectangle

        :param start: a pygame rect
        :param end_rect: a pygame rect
        :return: a list of coordinates that constitutes a path
        """
        start_rect = None
        #find start rectangle
        direction_index = relative_closest_direction(start.center)
        found = False
        for key in self.pathfinding_tree.rectangle_network[direction_index]:
            if (direction_index == 0 and key < start.centery) or (direction_index == 1 and key > start.centerx) or\
                (direction_index == 2 and key > start.centery) or (direction_index == 3 and key < start.centerx):
                adjacent_rects = self.pathfinding_tree.rectangle_network[direction_index][key]
            else:
                continue
            for rect in adjacent_rects:
                if rect.collidepoint(start.center):
                    start_rect = rect
                    found = True
                    break
            if found:
                break
        if start_rect == None:
            return None

        #check if there is a rectangle next to the end rectangle
        can_find = False
        for index, direction_size in enumerate((end_rect.top, end_rect.right, end_rect.bottom, end_rect.left)):
            if direction_size in self.pathfinding_tree.rectangle_network[index - 2]:
                for rect in self.pathfinding_tree.rectangle_network[index - 2][direction_size]:
                    if side_by_side(end_rect, rect) != None:
                        can_find = True
                        break
                if can_find:
                    break
        #there is no rectangle adjacent that could find a path
        if not can_find:
            return None
        end_node = self.pathfind(start_rect, end_rect)
        if not end_node:
            return None
        path = self.__retrace_path(end_node, start.topleft)
        return path

    def __retrace_path(self, node, start):
        """
        Retraces the path from the last node of the pathfinding algorithm to
        the first node in the chain

        :param node: a Node object
        :return: a list of coordinates that represents the path between the
        requested start and end.

        The direction of connection is used to determine the coordinates to
        move to in the current node.rect that results in a path trough the
        node.rect that ends at a location that is open to the connecting rect.
        """
        path = Path(start)
        prev_node = node
        node = node.parent
        target_location = prev_node.rect.topleft
        while node is not None:
            direction = self.DIRECTIONS[prev_node.direction_index]
            if direction in ["N", "S"]:
                if direction == "N":
                    y = node.rect.top
                else:
                    y = node.rect.bottom - BLOCK_SIZE.height
                left_distance = right_distance= 0
                #first check if the target should allign with the left or right
                #side
                if prev_node.rect.left > node.rect.left:
                    left_distance = abs(prev_node.rect.left - target_location[0])
                else:
                    left_distance = abs(node.rect.left - target_location[0])
                if prev_node.rect.right < node.rect.right:
                    right_distance = abs(prev_node.rect.right - target_location[0])
                else:
                    right_distance = abs(node.rect.right - target_location[0])

                #configure x
                if left_distance < right_distance:
                    x = max(prev_node.rect.left, node.rect.left)
                else:
                    x = min(prev_node.rect.right, node.rect.right) - BLOCK_SIZE[0]
            elif direction in ["E", "W"]:
                if direction == "E":
                    x = node.rect.right - BLOCK_SIZE.width
                else:
                    x = node.rect.left
                top_distance = bottom_distance = 0
                if prev_node.rect.top > node.rect.top:
                    top_distance = abs(node.rect.top - target_location[1])
                else:
                    top_distance = abs(prev_node.rect.top - target_location[1])
                if prev_node.rect.bottom < node.rect.bottom:
                    bottom_distance = abs(node.rect.bottom - target_location[1])
                else:
                    bottom_distance = abs(prev_node.rect.bottom - target_location[1])

                # configure y
                if top_distance < bottom_distance:
                    y = max(prev_node.rect.top, node.rect.top)
                else:
                    y = min(prev_node.rect.bottom, node.rect.bottom) - BLOCK_SIZE[1]
            path.append((x,y))
            prev_node = node
            node = node.parent
            target_location = (x, y)
        return path

    def pathfind(self, start, end):
        """
        Returns the final node in a pathfinding problem.
        https://gist.github.com/Nicholas-Swift/003e1932ef2804bebef2710527008f44#file-astar-py
        """

        # Create start and end node
        start_node = Node(None, start, None)
        start_node.g = start_node.f = 0
        end_node = Node(None, end, None)
        end_node.g = end_node.h = end_node.f = 0
        start_node.h = manhattan_distance(start_node.position,
                                          end_node.position)
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
                if item.f < current_node.f:
                    current_node = item
                    current_index = index

            # Pop current off open list, add to closed list
            open_list.pop(current_index)
            closed_list.append(current_node)

            # Found the goal on block infront of destination
            connection_direction = side_by_side(current_node.rect, end_node.rect)
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
                if len([closed_child for closed_child in closed_list if
                        closed_child == child]) > 0:
                    continue

                # Create the f, g, and h values
                child.g = current_node.g + 1
                child.h = manhattan_distance(child.position, end_node.position)
                child.f = child.g + child.h

                # Child is already in the open list
                if len([open_node for open_node in open_list if
                        child.position == open_node.position]) > 0:
                    continue

                # Add the child to the open list
                open_list.append(child)
        return None


class Path:
    """
    Track a path and its lenght
    """
    def __init__(self, start):
        self.start_location = start
        self.__coordinates = []
        self.__lenght = 0

    def append(self, item):
        self.__coordinates.append(item)
        #distance will be zero for the first addition
        self.__lenght += manhattan_distance(item, self.__coordinates[-1])

    def pop(self, index = -1):
        return self.__coordinates.pop(index)

    def __getitem__(self, item):
        return self.__coordinates[item]

    def __len__(self):
        return len(self.__coordinates)

    @property
    def path_lenght(self):
        return self.__lenght + manhattan_distance(self.__coordinates[-1], self.start_location)


class Node:
    """
    Node class for the A* pathfinding. Saves nodes with an AirRectangle Object
    and a direction index for tracing back the path
    """
    def __init__(self, parent, rect, direction_index):
        """
        :param parent: The parent Node object this Node comes from
        :param rect: an AirRectangle object that is on the location of the node
        :param direction_index: an direction index fro the list [N, E, S, W]
        """
        self.parent = parent
        # in order y, x
        self.rect = rect
        #value that tells the direction between the parent node en this node
        self.direction_index = direction_index

        #used for the A* algorithm calculation of distance
        self.g = 0
        self.h = 0
        self.f = 0

    @property
    def position(self):
        """
        The position used for calculating the distance measures.

        Note: the center of the rectangle is not always the most informative
        measure when it comes to distance of the path over this node

        :return: the center of the AirRectangle
        """
        return self.rect.center

    def __str__(self):
        return str(self.position[::-1])

    def __eq__(self, other):
        return self.position == other.position


class PathfindingTree:
    """
    Tree that is continiously recalculated for the pathfinding algorithm to use

    Note: the self.rectangles could be a more efficient format then a list
    """
    def __init__(self):
        """
        :param matrix: a matrix over which changes are made.
        """
        #shared dictionary that acts as the tree of connections between rectangles in the chunks
        self.rectangle_network = [{}, {}, {}, {}]
        self.pathfinding_chunks = []

    def add_chunk(self, pf_chunk):
        self.pathfinding_chunks.append(pf_chunk)
        pf_chunk.configure(self.rectangle_network)


class PathfindingChunk:
    def __init__(self, matrix):
        self.matrix = matrix
        self.rectangle_network = None

        #rectangles only present in this chunk
        self.__local_rectangles = set()
        self.added_rects = []
        self.removed_rects = []
        self.__times_passed = [random.randint(0, PF_UPDATE_TIME), PF_UPDATE_TIME]

    def configure(self, rectangles):
        self.rectangle_network = rectangles
        covered_coordinates = [[False for _ in range(len(self.matrix[0]))] for _ in range(len(self.matrix))]

        #innitial configuration
        self.get_air_rectangles(self.matrix, covered_coordinates)

    def update(self):
        self.__times_passed[0] += GAME_TIME.get_time()
        #fix mistakes in the fast updating
        if self.__times_passed[0] > self.__times_passed[1] and (len(self.removed_rects) > 0 or len(self.added_rects) > 0):
            #TODO make this a less temporary fix, is kind of crude right now --> works pretty good
            self.__times_passed[0] == 0
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

    def __find_add_sub_matrix(self, rect):
        adjacent_rectangles = []

        corners = [rect.left, rect.top,
                   rect.bottom, rect.right]
        direction_index = relative_closest_direction(rect.center)
        all_found = False
        for key in self.rectangle_network[direction_index]:
            if (direction_index == 0 and key < rect.centery) or (direction_index == 1 and key > rect.centerx) or\
                (direction_index == 2 and key > rect.centery) or (direction_index == 3 and key < rect.centerx):
                adjacent_rects = self.rectangle_network[direction_index][key]
            else:
                continue
            for adj_rect in adjacent_rects:
                #rectangles in different chunks do not take the matrix
                if p_to_cp(adj_rect.topleft) != p_to_cp(rect.topleft):
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

    def __find_removal_sub_matrix(self, rect):
        adjacent_rectangles = []

        #find all adacent rectangles and the box that ontains them all
        corners = [rect.left, rect.top,
                   rect.bottom, rect.right]
        for index, direction_size in enumerate((rect.top, rect.right, rect.bottom, rect.left)):
            if direction_size not in self.rectangle_network[index - 2]:
                continue
            for adj_rect in self.rectangle_network[index - 2][direction_size].copy():
                #rectangles in different chunks do not take the matrix
                if p_to_cp(adj_rect.topleft) != p_to_cp(rect.topleft):
                    continue
                if side_by_side(rect, adj_rect) is not None:
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

        #get the sub matrix and all coordinates that are transaparant but do not need recalculation
        all_rectangles = [rect] + adjacent_rectangles
        return self.__sub_matrix_from_corners(corners, all_rectangles)

    def __sub_matrix_from_corners(self, corners, all_rectangles):
        start_column, start_row = (int((corners[0] % CHUNK_SIZE.width) / BLOCK_SIZE.width), int((corners[1] % CHUNK_SIZE.height) / BLOCK_SIZE.height))
        row_lenght = p_to_r(corners[3] - corners[0])
        column_lenght = p_to_c(corners[2] - corners[1])
        sub_matrix = []
        covered_coordinates = [[False for _ in range(row_lenght)] for _ in range(column_lenght)]
        for row_index in range(column_lenght):
            row = self.matrix[start_row + row_index][start_column:start_column + row_lenght]
            sub_matrix.append(row)
            for col_index, block in enumerate(row):
                #if transparant block in sub matrix but not adjacent pre ignore it.
                if block.transparant_group != 0 and block.rect.collidelist(all_rectangles) == -1:
                    covered_coordinates[row_index][col_index] = True
        return sub_matrix, covered_coordinates

    def __add_rectangle(self, rect):
        self.__local_rectangles.add(rect)
        for index, direction_size in enumerate((rect.top, rect.right, rect.bottom, rect.left)):
            if direction_size in self.rectangle_network[index]:
                self.rectangle_network[index][direction_size].add(rect)
            else:
                self.rectangle_network[index][direction_size] = set([rect])
            # add connections
            if direction_size in self.rectangle_network[index - 2]:
                for adj_rect in self.rectangle_network[index - 2][direction_size]:
                    if side_by_side(rect, adj_rect) != None:
                        rect.connecting_rects[index].add(adj_rect)
                        adj_rect.connecting_rects[index - 2].add(rect)

    def __remove_rectangle(self, rect):
        self.__local_rectangles.remove(rect)
        rect.delete()
        direction_sizes = (rect.top, rect.right, rect.bottom, rect.left)
        for i in range(4):
            self.rectangle_network[i][direction_sizes[i]].remove(rect)

    def get_air_rectangles(self, blocks, covered_coordinates):
        #covered coordinates is a matrix with the same amount of rows and column coords for all checked coords.

        # find all rectangles in the block matrix
        for n_row, row in enumerate(blocks):
            for n_col, block in enumerate(row):
                if block.transparant_group == 0 or covered_coordinates[n_row][n_col]:
                    continue

                # calculate the maximum lenght of a rectangle based on already
                # established ones
                end_n_col = n_col
                for index, r_block in enumerate(row[n_col:]):
                    if covered_coordinates[n_row][n_col + index]:
                        break
                    end_n_col = n_col + index


                sub_matrix = [sub_row[n_col:end_n_col + 1] for sub_row in blocks[n_row:]]
                sub_covered_matrix = [sub_row[n_col:end_n_col + 1] for sub_row in covered_coordinates[n_row:]]
                lm_coord = self.__find_air_rectangle(sub_matrix, sub_covered_matrix)

                # add newly covered coordinates
                for x in range(lm_coord[0] + 1):
                    for y in range(lm_coord[1] + 1):
                        covered_coordinates[n_row + y][n_col + x] = True

                # add the air rectangle to the list of rectangles
                air_matrix = [sub_row[n_col:n_col + lm_coord[0] + 1] for sub_row in
                              blocks[n_row:n_row + lm_coord[1] + 1]]
                rect = AirRectangle(rect_from_block_matrix(air_matrix))
                self.__add_rectangle(rect)

    def __find_air_rectangle(self, blocks, covered_coordinates):
        """
        Find starting from an air block all the air block_classes in a rectangle

        :param blocks: a selection of block_classes in a matrix
        :return: the matrix coordinate of the local block_classes matrix in form
        (column, row) that is the bottom right of the air rectangle
        """
        # first find how far the column is filled cannot fill on 0 since 0 is guaranteed to be a air block
        x_size = 0
        group = blocks[0][0].transparant_group
        for n_col, block in enumerate(blocks[0][1:]):
            if block.transparant_group != group or covered_coordinates[0][n_col + 1]:
                break
            x_size += 1
        matrix_coordinate = [x_size, 0]

        # skip the first row since this was checked already
        block = None
        for n_row, row in enumerate(blocks[1:]):
            for n_col, block in enumerate(row[:x_size + 1]):
                if block.transparant_group != group or covered_coordinates[n_row][n_col]:
                    break
            if block.transparant_group != group or covered_coordinates[n_row][n_col]:
                break
            matrix_coordinate[1] += 1
        return matrix_coordinate


class AirRectangle:
    """
    Class for trackign rectangles with adjacent rectangles. This rectangle
    essentialy is a node in a network of air rectangles that are connected to
    one another
    """
    def __init__(self, rect):
        """
        :param rect: a pygame Rect object
        """
        self.rect = rect
        # a list of lists representing N, E, S, W connections
        self.connecting_rects = [set() for _ in range(4)]

    def delete(self):
        #delete any reference from connectiing rectangles
        for direction_index in range(len(self.connecting_rects)):
            for connection in self.connecting_rects[direction_index]:
                connection.connecting_rects[direction_index - 2].remove(self)

    def __getattr__(self, item):
        return getattr(self.rect, item)

    def __str__(self):
        return str(self.rect)
