from python_code.interfaces.widgets import *
from python_code.interfaces.base_interface import Window


class FurnaceWindow(Window):
    def __init__(self, furnace_object, *groups):
        Window.__init__(self, INTERFACE_WINDOW_POS, INTERFACE_WINDOW_SIZE,
                       *groups, layer=INTERFACE_LAYER, title = "FURNACE",
                        allowed_events=[1])
