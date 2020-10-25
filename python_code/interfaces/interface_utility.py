from python_code.utility.constants import BOARD_SIZE, SCREEN_SIZE, CHUNK_SIZE, BLOCK_SIZE



def screen_to_board_coordinate(coord, target, zoom):
    """
    Calculate the screen to current board size coordinate. That is the
    zoomed in board. Then revert the coordinate back to the normal screen

    :param coord: a coordinate with x and y value within the screen region
    :return: a coordinate with x and y vale within the ORIGINAL_BOARD_SIZE.

    The value is scaled back to the original size after instead of
    being calculated as the original size on the spot because the screen
    coordinate can not be converted between zoom levels so easily.
    """
    c = target.rect.center
    # last half a screen of the board
    if BOARD_SIZE.width - c[0] - SCREEN_SIZE.width / 2 < 0:
        x = BOARD_SIZE.width - (SCREEN_SIZE.width - coord[0])
    # the rest of the board
    elif c[0] - SCREEN_SIZE.width / 2 > 0:
        x = coord[0] + (c[0] - SCREEN_SIZE.width / 2)
    # first half a screen of the board
    else:
        x = coord[0]
    if BOARD_SIZE.height - c[1] - SCREEN_SIZE.height / 2 < 0:
        y = BOARD_SIZE.height - (SCREEN_SIZE.height - coord[1])
    elif c[1] - SCREEN_SIZE.height / 2 > 0:
        y = coord[1] + (c[1] - SCREEN_SIZE.height / 2)
    else:
        y = coord[1]
    return [int(x / zoom), int(y / zoom)]

def p_to_r(value):
    """
    Point to row conversion. Convert a coordinate into a block row number

    :param value: a coordinate
    :return: the corresponding row number
    """
    return int(value / BLOCK_SIZE.height)

def p_to_c(value):
    """
    Point to column conversion. Convert a coordinate into a column number

    :param value: a coordinate
    :return: the corresponding column number
    """
    return int(value / BLOCK_SIZE.width)

def p_to_cp(point):
    #poitn to chunk chunk point
    return (p_to_cc(point[0]), p_to_cr(point[1]))

def p_to_cr(value):
    #to chunk row conversion
    return int(value / CHUNK_SIZE.height)

def p_to_cc(value):
    #to chunk column conversion
    return int(value / CHUNK_SIZE.width)


def relative_closest_direction(point):
    distances = []
    #caclulate to what side of the board the point is closest return an index corresponding to N, E, S, W
    distances.append(BOARD_SIZE.height - (BOARD_SIZE.height - point[1]))
    distances.append(BOARD_SIZE.width - point[0])
    distances.append(BOARD_SIZE.height - point[1])
    distances.append(BOARD_SIZE.width - (BOARD_SIZE.width - point[0]))
    return distances.index(min(distances))
