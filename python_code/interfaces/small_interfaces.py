from python_code.interfaces.widgets import *
from python_code.interfaces.base_interface import Window
from python_code.utility.utilities import Size


class FurnaceWindow(Window):
    SIZE = Size(100, 100)

    def __init__(self, furnace_object, *groups):
        self.furnace = furnace_object
        fr = self.furnace.rect
        location = fr.bottomleft
        Window.__init__(self,location , self.SIZE,
                       *groups, layer=INTERFACE_LAYER, title = "FURNACE",
                        allowed_events=[1, K_ESCAPE], static=True)

class TerminalWindow(Window):
    SIZE = Size(200, 100)

    def __init__(self, terminal_object, *groups):
        self.terminal = terminal_object
        fr = self.terminal.rect
        location = fr.bottomleft
        Window.__init__(self, location, self.SIZE,
                        *groups, layer=INTERFACE_LAYER, title="TERMINAL",
                        allowed_events=[1, K_ESCAPE], static=True)