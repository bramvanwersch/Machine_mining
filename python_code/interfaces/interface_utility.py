from python_code.utility.constants import BOARD_SIZE, SCREEN_SIZE



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
