from python_code.widgets import *

class BuildingInterface(EventHandler):
    def __init__(self, board, *groups):
        EventHandler.__init__(self, [])
        self.board = board
        self.__window = BuildingWindow(self.board.inventorie_blocks[0].inventory, *groups)

    def show(self, value):
        """
        Toggle showing the crafting window or not. This also makes sure that no
        real updates are pushed while the window is invisible

        :param value: a boolean
        """
        self.__window.visible = value


class BuildingWindow(Frame):
    COLOR = (173, 94, 29, 150)
    def __init__(self, inventory, *groups):
        Frame.__init__(self, INTERFACE_WINDOW_POS, INTERFACE_WINDOW_SIZE,
                       *groups, layer=INTERFACE_LAYER, color=self.COLOR,
                       title = "PICK ITEM TO BUILD:")
        self.visible = False
        self.static = False
