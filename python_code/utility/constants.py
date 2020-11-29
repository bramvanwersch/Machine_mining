import pygame, os
from pygame.locals import *

from utility.utilities import Size

#innitialize fonts to pre load a font
pygame.font.init()
FONTS = {i : pygame.font.SysFont("roboto", i) for i in range(12,35)}

GAME_TIME = pygame.time.Clock()

# the space in the path is to stay alert
MAIN_DIR = os.path.split(os.path.abspath(__file__))[0].rsplit(os.sep, 2)[0]
IMAGE_DIR = "{}{}images".format(MAIN_DIR, os.sep)
SAVE_DIR = "{}{}saves".format(MAIN_DIR, os.sep)

#location parameters
#1920, 1080
SCREEN_SIZE = Size(820, 820)
CHUNK_SIZE = Size(510, 510)
CHUNK_GRID_SIZE = Size(4, 4)
BOARD_SIZE = Size(CHUNK_GRID_SIZE.width * CHUNK_SIZE.width, CHUNK_GRID_SIZE.height * CHUNK_SIZE.height)
#y should not be lower then 1
START_CHUNK_POS = (1, 1)

#constant to tell when to recalculate the full chunk
PF_UPDATE_TIME = 1000

INTERFACE_WINDOW_SIZE = Size(500, 700)
DYNAMIC_INTERFACE_WINDOW_POS = (int((SCREEN_SIZE.width - INTERFACE_WINDOW_SIZE.width) / 2),
                                int((SCREEN_SIZE.height - INTERFACE_WINDOW_SIZE.height) / 2))
ORIGINAL_BOARD_SIZE = BOARD_SIZE.copy()

#layers
BOTTOM_LAYER = 0
BACKGROUND_LAYER = BOTTOM_LAYER + 1
BOARD_LAYER = BACKGROUND_LAYER + 1
HIGHLIGHT_LAYER = BOARD_LAYER + 1
LIGHT_LAYER = HIGHLIGHT_LAYER + 1
INTERFACE_LAYER = LIGHT_LAYER + 1

ORE_LIST = ["Iron", "Gold", "Copper", "Zinc", "Coal", "Titanium"]
FILLER_LIST = ["TopDirt", "Stone", "Granite", "FinalStone"]
BLOCK_SIZE = Size(10, 10)
MAX_DEPTH = BOARD_SIZE.height / BLOCK_SIZE.height

GAME_TIME = pygame.time.Clock()
INVISIBLE_COLOR = (0, 0, 0, 0)

GROW_CYCLE_UPDATE_TIME = 10_000 #every 10 seconds
MAX_LIGHT = 7
DECREASE_SPEED = 0.75

KEYBOARD_KEYS = [KEYDOWN, KEYUP, KMOD_ALT, KMOD_CAPS, KMOD_CTRL, KMOD_LALT, KMOD_LCTRL, KMOD_LMETA, KMOD_LSHIFT, KMOD_META,
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
             K_p, K_q, K_r, K_s, K_t, K_u, K_v, K_w, K_x, K_y, K_z, 1, 2,3,4,5]

#camera controls
UP = K_w
DOWN = K_s
RIGHT = K_d
LEFT = K_a
CAMERA_KEYS = [UP, DOWN, RIGHT, LEFT]

#mode controls
MINING = K_m
BUILDING = K_b
CANCEL = K_x
SELECTING = K_k

class Mode:
    def __init__(self, key, name, color, persisten_highlight = True):
        self.key = key
        self.name = name
        self.color = color
        self.persistent_highlight = persisten_highlight

MODE_KEYS = [MINING, BUILDING, CANCEL, SELECTING]
MODES = {MINING : Mode(MINING, "Mining", (9, 108, 128, 100)),
         BUILDING : Mode(BUILDING, "Building", (255, 64, 229, 100)),
         CANCEL : Mode(CANCEL, "Cancel", (255, 0, 0, 100), False),
         SELECTING : Mode(SELECTING, "Selecting", (59, 191, 70, 100), False)}
MULTI_TASKS = {"Mining" : False, "Building" : False, "Cancel" : False, "Selecting" : False, "Empty inventory" : True, "Fetch" : True, "Request" : True, "Deliver" : True}

#interface control
CRAFTING = K_c

INTERFACE_KEYS = [CRAFTING, K_ESCAPE, BUILDING]

#visual control
SHOW_BLOCK_BORDER = True
FPS = True
ENTITY_NMBR = True
AIR_RECTANGLES = False
WARNINGS = True
ZOOM = True