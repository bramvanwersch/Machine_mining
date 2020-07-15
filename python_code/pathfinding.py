import threading

from python_code.constants import BLOCK_SIZE
from python_code.utilities import rect_from_block_matrix, manhattan_distance

class PathFinder:
    """
    Pathfinder object for continiously mapping the current board to a network
    of rectangles and finding paths using that network
    """
    DIRECTIONS = ["N", "E", "S", "W"]
    def __init__(self, matrix):
        #calculation thread for continously updating the network
        self.calculation_thread = PathfindingTree(matrix)

        self.calculation_thread.start()

    def get_path(self, start, end_rect):
        """
        Pathfinds a path between the start and end rectangle

        :param start: a pygame rect
        :param end_rect: a pygame rect
        :return: a list of coordinates that constitutes a path
        """
        start_rect = None
        #find start rectangle
        for rect in self.calculation_thread.rectangles:
            if rect.collidepoint(start.topleft):
                start_rect = rect
                break
        if start_rect == None:
            return None

        #check if there is a rectangle next to the end rectangle
        can_find = False
        for rect in self.calculation_thread.rectangles:
            if self.calculation_thread._side_by_side(end_rect, rect) != None:
                can_find = True
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
                    top_distance = abs(prev_node.rect.top - target_location[1])
                else:
                    top_distance = abs(node.rect.top - target_location[1])
                if prev_node.rect.bottom < node.rect.bottom:
                    bottom_distance = abs(prev_node.rect.bottom - target_location[1])
                else:
                    bottom_distance = abs(node.rect.bottom - target_location[1])

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
            connection_direction = self.calculation_thread._side_by_side(current_node.rect, end_node.rect)
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

    def stop(self):
        self.calculation_thread.keep_calculating = False

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

    def lenght(self):
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

class PathfindingTree(threading.Thread):
    """
    Tree that is continiously recalculated for the pathfinding algorithm to use

    Note: the self.rectangles could be a more efficient format then a list
    """
    def __init__(self, matrix):
        """
        :param matrix: a matrix over which changes are made.
        """
        threading.Thread.__init__(self)
        self.matrix = matrix
        self.rectangles = self.get_air_rectangles(self.matrix)
        self.build_tree(self.rectangles)
        self.keep_calculating = True

    def run(self):
        """
        Funtion for starting the calculation thread.
        """
        while self.keep_calculating:
            self.lazzy_update()

    def lazzy_update(self):
        """
        A protocol for lazily updating all the air rectangles.

        Note: in the future a function that would take only removed rectangles
        should replace this function for updating the air rectangles
        """
        ar = self.get_air_rectangles(self.matrix)
        self.rectangles = ar

        self.build_tree(ar)

    def build_tree(self, rectangles):
        """
        Figure out how all rectangles in a set of rectangles are connected to
        one another based on if these are adjacent or not

        :param rectangles: a list of AirRectangle objects
        """
        for rect1 in rectangles:
            for rect2 in rectangles:
                if rect1 == rect2:
                    continue
                direction_index = self._side_by_side(rect1, rect2)
                if direction_index != None:
                    rect1.connecting_rects[direction_index].append(rect2)


    def _side_by_side(self, rect1, rect2):
        """
        Check if two rectangles are side by side and are touching.

        :param rect1: pygame rect 1
        :param rect2:  pygame rect 2
        :return: a number giving a direction index that coresponds to the list
        [N, E, S, W]
        """

        if rect1.bottom == rect2.top:
            if (rect1.left <= rect2.left and rect1.right > rect2.left) or\
                (rect1.left < rect2.right and rect1.right >= rect2.right):
                return 2
            elif (rect2.left <= rect1.left and rect2.right > rect1.left) or \
                (rect2.left < rect1.right and rect2.right >= rect1.right):
                return 2
        elif rect1.top == rect2.bottom:
            if (rect1.left <= rect2.left and rect1.right > rect2.left) or\
                (rect1.left < rect2.right and rect1.right >= rect2.right):
                return 0
            elif (rect2.left <= rect1.left and rect2.right > rect1.left) or \
                (rect2.left < rect1.right and rect2.right >= rect1.right):
                return 0
        elif rect1.right == rect2.left:
            if (rect1.top <= rect2.top and rect1.bottom > rect2.top) or \
                (rect1.top < rect2.bottom and rect1.bottom >= rect2.bottom):
                return 1
            elif (rect2.top <= rect1.top and rect2.bottom > rect1.top) or \
                (rect2.top < rect1.bottom and rect2.bottom >= rect1.bottom):
                return 1
        elif rect1.left == rect2.right:
            if (rect1.top <= rect2.top and rect1.bottom > rect2.top) or \
                (rect1.top < rect2.bottom and rect1.bottom >= rect2.bottom):
                return 3
            elif (rect2.top <= rect1.top and rect2.bottom > rect1.top) or \
                (rect2.top < rect1.bottom and rect2.bottom >= rect1.bottom):
                return 3
        else:
            return None


    def get_air_rectangles(self, blocks):
        """
        Get all air spaces in the given matrix of blocks as a collection of
        rectangles

        :param blocks: a matrix of blocks
        :return: a list of rectangles
        """
        air_rectangles = []

        #save covered coordinates in a same lenght matrix for faster checking
        covered_coordinates = [[] for row in blocks]

        #find all rectangles in the block matrix
        for n_row, row in enumerate(blocks):
            for n_col, block in enumerate(row):
                if block != "Air" or n_col in covered_coordinates[n_row]:
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
                lm_coord = self.__find_air_rectangle(sub_matrix)

                # add newly covered coordinates
                for x in range(lm_coord[0]+ 1):
                    for y in range(lm_coord[1] + 1):
                        covered_coordinates[n_row + y].append(n_col + x)

                # add the air rectangle to the list of rectangles
                air_matrix = [sub_row[n_col:n_col + lm_coord[0] + 1] for sub_row in blocks[n_row:n_row + lm_coord[1] + 1]]
                rect = AirRectangle(rect_from_block_matrix(air_matrix))
                air_rectangles.append(rect)
        return air_rectangles

    def __find_air_rectangle(self, blocks):
        """
        Find starting from an air block all the air blocks in a rectangle

        :param blocks: a selection of blocks in a matrix
        :return: the matrix coordinate of the local blocks matrix in form
        (column, row) that is the bottom right of the air rectangle
        """
        #first find how far the column is filled cannot fill on 0 since 0 is guaranteed to be a air block
        x_size = 0
        for block in blocks[0][1:]:
            if block != "Air":
                break
            x_size += 1
        matrix_coordinate = [x_size, 0]

        #skip the first row since this was checked already
        block = None
        for n_row, row in enumerate(blocks[1:]):
            for n_col, block in enumerate(row[:x_size + 1]):
                if block != "Air":
                    break
            if block != "Air":
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
        self.connecting_rects = [[] for _ in range(4)]

    def remove_connection(self, index, rect):
        """
        Remove a connection from a certain direction

        :param index: the direction_index
        :param rect: an Air rectangle
        :return:
        """
        for pos, c_rect in enumerate(self.connecting_rects[index]):
            if c_rect == rect:
                del self.connecting_rects[index][pos]
                break

    def __getattr__(self, item):
        return getattr(self.rect, item)

    def __str__(self):
        return str(self.rect)


##Failed idea for later mb. This is an idea for non lazy loading approach

   # def update_tree(self, blocks):
   #      new_rect = rect_from_block_matrix(blocks)
   #      print(len(self.rectangles))
   #
   #
   #      #find an adjacent rectangle if any to the new matrix and remove them
   #      #from the list of rectangles
   #      adjacent_rectangles = []
   #      for index in range(len(self.rectangles)):
   #          direction = self.__side_by_side(new_rect, self.rectangles[index])
   #          if direction != None:
   #              adjacent_rectangles.append(self.rectangles[index])
   #
   #      #get rectangle that covers the blocks and all adjacent rectangles
   #      all_rect = new_rect.unionall(adjacent_rectangles)
   #      # print(all_rect)
   #      # print("ASJACENT")
   #      # for r in adjacent_rectangles:
   #      #     print(r)
   #
   #      colliding_indexes = all_rect.collidelistall(self.rectangles)
   #      colliding_indexes.sort(reverse  = True)
   #
   #      all_affected_rectangles = []
   #      for index in colliding_indexes:
   #          all_affected_rectangles.append(self.rectangles[index])
   #          del self.rectangles[index]
   #
   #      #dereference the all_affected_rectangles in all theire neighbours
   #      adjacent_neighbours = {}
   #      for rect in all_affected_rectangles:
   #          for index, c_rects in enumerate(rect.connecting_rects):
   #              for c_rect in c_rects:
   #                  c_rect.remove_connection(index - 2, rect)
   #                  if c_rect not in adjacent_rectangles:
   #                      adjacent_neighbours[str(c_rect)] = c_rect
   #
   #      #get a new matrix that covers all blocka and get air rectangles and build a tree
   #      new_matrix = self.board.overlapping_blocks(all_rect)
   #      # for row in new_matrix:
   #      #     print(row)
   #      new_air_rectangles = self.get_air_rectangles(new_matrix)
   #
   #      # print("NEW RECT")
   #      unique_rectangles= []
   #      for n_rect in new_air_rectangles:
   #          # print(n_rect)
   #          if n_rect not in self.rectangles:
   #              self.rectangles.append(n_rect)
   #              unique_rectangles.append(n_rect)
   #      self.build_tree([*unique_rectangles, *adjacent_neighbours.values()])
   #
   #      #finally append the new rectangles
   #
   #
   #      # print("ALL FO THEM")
   #      # for r in self.rectangles:
   #      #     print(r)
   #
