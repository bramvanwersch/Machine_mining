#!/usr/bin/python3

# library imports
import pygame
from typing import Tuple, Dict, Iterable
import os
from pygame.locals import *

# own imports
import utility.utilities as util


# debug controls
class DebugValues(util.ConsoleReadable):
    def __init__(self):
        self.FPS = True
        self.ENTITY_NMBR = True
        self.AIR_RECTANGLES = False
        self.WARNINGS = True
        self.SHOW_ZOOM = True
        self.NO_LIGHTING = False
        self.SHOW_THREADS = True
        self.SHOW_BELT_ITEMS = True


DEBUG = DebugValues()

TESTING = True  # can be used to cheat in items at certain places for easier testing
SHOW_BLOCK_BORDER = True
TEST_BOARD = TESTING

# innitialize fonts to pre load a font
pygame.font.init()
FONTS: Dict[int, pygame.font.Font] = {i: pygame.font.SysFont("roboto", i) for i in range(12, 35)}

# time constants
GAME_TIME = pygame.time.Clock()  # time tracked by pygame
PF_UPDATE_TIME = 1000  # constant to tell when to recalculate the full chunk
GROW_CYCLE_UPDATE_TIME = 10_000 if not TESTING else 100  # ms
MINING_SPEED_PER_HARDNESS = 100   # ms

# path varaibles
MAIN_DIR = os.path.split(os.path.abspath(__file__))[0].rsplit(os.sep, 2)[0]
IMAGE_DIR = "{}{}images".format(MAIN_DIR, os.sep)
SAVE_DIR = "{}{}saves".format(MAIN_DIR, os.sep)
DATA_DIR = "{}{}data".format(MAIN_DIR, os.sep)

# sizes
SCREEN_SIZE = util.Size(820, 820) if TESTING else util.Size(1920, 1080)  # pixels
CHUNK_SIZE = util.Size(500, 500)  # make this always devisible by then 10 and <= 2^x
if TEST_BOARD:
    BOARD_SIZE = util.Size(2000, 2000)  # board size should always be bigger then the SCREEN_SIZE
    # preserve the board size
    ORIGINAL_BOARD_SIZE = BOARD_SIZE.copy()
    # the center of the board
    START_CHUNK_POS = (1, 1)
    START_LOAD_AREA = [list(range(START_CHUNK_POS[0] - 1, START_CHUNK_POS[0] + 2)),
                       list(range(START_CHUNK_POS[1] - 1, START_CHUNK_POS[1] + 2))]  # always consecutive
    TOTAL_START_CHUNKS = 9
else:
    BOARD_SIZE = util.Size(100_000, 5000)  # board size should always be bigger then the SCREEN_SIZE
    # preserve the board size
    ORIGINAL_BOARD_SIZE = BOARD_SIZE.copy()
    # the center of the board
    START_CHUNK_POS = (int(round(BOARD_SIZE.width / CHUNK_SIZE.width) / 2), 2)
    START_LOAD_AREA = [list(range(START_CHUNK_POS[0] - 2, START_CHUNK_POS[0] + 3)),
                       list(range(START_CHUNK_POS[1] - 2, START_CHUNK_POS[1] + 3))]  # always consecutive
    TOTAL_START_CHUNKS = ((START_CHUNK_POS[0] + 3) - (START_CHUNK_POS[0] - 2)) * \
                         ((START_CHUNK_POS[1] + 3) - (START_CHUNK_POS[1] - 2))

BLOCK_SIZE = util.Size(20, 20)
TRANSPORT_BLOCK_SIZE = util.Size(int(BLOCK_SIZE.width * 0.6), int(BLOCK_SIZE.height * 0.6))
MAX_DEPTH = BOARD_SIZE.height / BLOCK_SIZE.height  # in blocks

# layers
BOTTOM_LAYER = 0
BACKGROUND_LAYER = BOTTOM_LAYER + 1
BOARD_LAYER = BACKGROUND_LAYER + 1
HIGHLIGHT_LAYER = BOARD_LAYER + 1
LIGHT_LAYER = HIGHLIGHT_LAYER + 1
INTERFACE_LAYER = LIGHT_LAYER + 1
# make sure that this layer is always on top of the interfaces
TOOLTIP_LAYER = INTERFACE_LAYER + 1000

# this is sort of a green screen color, set this as a color key in order to be transparant when blitting
INVISIBLE_COLOR = (254, 254, 254, 0)

# light varaibles
MAX_LIGHT = 15
DECREASE_SPEED = 1
DECREASE_SPEED_SOLID = 3

STARTING_ENTITIES = 1

KEYBOARD_KEYS = \
    [KEYDOWN, KEYUP, KMOD_ALT, KMOD_CAPS, KMOD_CTRL, KMOD_LALT, KMOD_LCTRL, KMOD_LMETA, KMOD_LSHIFT, KMOD_META,
     KMOD_MODE, KMOD_NONE, KMOD_NUM, KMOD_RALT, KMOD_RCTRL, KMOD_RMETA, KMOD_RSHIFT, KMOD_SHIFT, K_0, K_1, K_2,
     K_3, K_4, K_5, K_6, K_7, K_8, K_9, K_AMPERSAND, K_ASTERISK, K_AT, K_BACKQUOTE, K_BACKSLASH, K_BACKSPACE,
     K_BREAK, K_CAPSLOCK, K_CARET, K_CLEAR, K_COLON, K_COMMA, K_DELETE, K_DOLLAR, K_DOWN, K_END, K_EQUALS,
     K_ESCAPE, K_EURO, K_EXCLAIM, K_F1, K_F10, K_F11, K_F12, K_F13, K_F14, K_F15, K_F2, K_F3, K_F4, K_F5, K_F6,
     K_F7, K_F8, K_F9, K_GREATER, K_HASH, K_HELP, K_HOME, K_INSERT, K_KP0, K_KP1, K_KP2, K_KP3, K_KP4,
     K_KP5, K_KP6, K_KP7, K_KP8, K_KP9, K_KP_DIVIDE, K_KP_ENTER, K_KP_EQUALS, K_KP_MINUS, K_KP_MULTIPLY,
     K_KP_PERIOD, K_KP_PLUS, K_LALT, K_LCTRL, K_LEFT, K_LEFTBRACKET, K_LEFTPAREN, K_LESS, K_LMETA,
     K_LSHIFT, K_LSUPER, K_MENU, K_MINUS, K_MODE, K_NUMLOCK, K_PAGEDOWN, K_PAGEUP, K_PAUSE, K_PERIOD, K_PLUS,
     K_POWER, K_PRINT, K_QUESTION, K_QUOTE, K_QUOTEDBL, K_RALT, K_RCTRL, K_RETURN, K_RIGHT, K_RIGHTBRACKET,
     K_RIGHTPAREN, K_RMETA, K_RSHIFT, K_RSUPER, K_SCROLLOCK, K_SEMICOLON, K_SLASH, K_SPACE, K_SYSREQ, K_TAB,
     K_UNDERSCORE, K_UNKNOWN, K_UP, K_a, K_b, K_c, K_d, K_e, K_f, K_g, K_h, K_i, K_j, K_k, K_l, K_m, K_n, K_o,
     K_p, K_q, K_r, K_s, K_t, K_u, K_v, K_w, K_x, K_y, K_z, 1, 2, 3, 4, 5]

KEY_KEYS = \
    [K_0, K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8, K_9, K_AMPERSAND,
     K_ASTERISK, K_AT, K_BACKQUOTE, K_BACKSLASH, K_BACKSPACE, K_BREAK, K_CARET, K_COLON, K_COMMA, K_DELETE, K_DOLLAR,
     K_DOWN, K_END, K_EQUALS, K_EURO, K_EXCLAIM, K_GREATER, K_HASH, K_HELP, K_HOME, K_INSERT, K_KP0, K_KP1, K_KP2,
     K_KP3, K_KP4, K_KP5, K_KP6, K_KP7, K_KP8, K_KP9, K_KP_DIVIDE, K_KP_ENTER, K_KP_EQUALS, K_KP_MINUS, K_KP_MULTIPLY,
     K_KP_PERIOD, K_KP_PLUS, K_LEFT, K_LEFTBRACKET, K_LEFTPAREN, K_LESS, K_MINUS, K_PERIOD, K_PLUS, K_QUESTION,
     K_RIGHT, K_RIGHTBRACKET, K_RIGHTPAREN, K_RSHIFT, K_SEMICOLON, K_SLASH, K_SPACE, K_TAB, K_UNDERSCORE, K_UP, K_a,
     K_b, K_c, K_d, K_e, K_f, K_g, K_h, K_i, K_j, K_k, K_l, K_m, K_n, K_o, K_p, K_q, K_r, K_s, K_t, K_u, K_v, K_w, K_x,
     K_y, K_z, K_RETURN]

# 2 different hover types
HOVER = USEREVENT + 1
UNHOVER = USEREVENT + 2
# one unique hover button
BTN_HOVER = "hover"

# camera controls
UP = K_w
DOWN = K_s
RIGHT = K_d
LEFT = K_a
CAMERA_KEYS = [UP, DOWN, RIGHT, LEFT]


# mode constants
class ModeConstants:
    key: int
    name: str
    color: Tuple[int, int, int, int]
    persistent_highlight: bool

    def __init__(
        self,
        key: int,
        name: str,
        color: Tuple[int, int, int, int],
        persisten_highlight: bool = True
    ):
        self.key = key
        self.name = name
        self.color = color
        self.persistent_highlight = persisten_highlight


class BoardKeys:
    """A streamlined place for keybinds related to the board. This allows for easier changed later with settings"""

    __keys: Dict[str, int]

    def __init__(self):
        self.__keys = {
            "MINING": K_m,
            "BUILDING": K_b,
            "CANCEL": K_x,
            "SELECTING": K_k,
            "ROTATING": K_r
        }

    def all_keys(self) -> Iterable[int]:
        return self.__keys.values()

    def __getattr__(self, item: str) -> int:
        if item in self.__keys:
            return self.__keys[item]
        raise AttributeError(f"No key bound for {item}")


BOARD_KEYS = BoardKeys()

MODES = {BOARD_KEYS.MINING: ModeConstants(BOARD_KEYS.MINING, "Mining", (9, 108, 128, 100)),
         BOARD_KEYS.BUILDING: ModeConstants(BOARD_KEYS.BUILDING, "Building", (255, 64, 229, 100)),
         BOARD_KEYS.CANCEL: ModeConstants(BOARD_KEYS.CANCEL, "Cancel", (255, 0, 0, 100), False),
         BOARD_KEYS.SELECTING: ModeConstants(BOARD_KEYS.SELECTING, "Selecting", (59, 191, 70, 100), False)}


# tasks constants
class TaskConstants:
    multi: bool

    def __init__(
        self,
        can_multi: bool
    ):
        self.multi = can_multi


MULTI_TASKS = \
    {"Mining": TaskConstants(False), "Building": TaskConstants(False), "Cancel": TaskConstants(False),
     "Selecting": TaskConstants(False), "Empty inventory": TaskConstants(True), "Fetch": TaskConstants(True),
     "Request": TaskConstants(True), "Deliver": TaskConstants(True)}
