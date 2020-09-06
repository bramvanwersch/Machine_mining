import pygame
from python_code.utility.constants import SCREEN_SIZE, BOARD_SIZE, INTERFACE_LAYER, MOUSEBUTTONDOWN

window_manager = None

def create_window_manager(camera_target):
    global window_manager
    window_manager = WindowManager(camera_target)


class WindowManager:
    def __init__(self, target):
        self.windows = {}
        self.window_order = []
        self.__target = target

    def add(self, window):
        #dont add the same window multiple times
        if window.id in self.windows:
            return
        self.windows[window.id] = window
        if len(self.window_order) == 0:
            window._layer = INTERFACE_LAYER
        else:
            window._layer = self.window_order[-1]._layer + 1
        self.window_order.append(window)
        window.show(True)

    def remove(self, window):
        del self.windows[window.id]
        rem_index = self.window_order.index(window)
        if rem_index + 1 == len(self.window_order):
            self.window_order.pop()
        else:
            self.window_order.pop(rem_index)
            for window in self.window_order[rem_index +1 :]:
                window._layer -= 1
        window.show(False)

    def __set_top_window(self, event_pos):

        #determine what window was clicked
        board_coord = self._screen_to_board_coordinate(event_pos)
        selected_window = None
        for window in self.windows.values():
            if window.static:
                if window.orig_rect.collidepoint(event_pos) and \
                    (selected_window == None or selected_window._layer < window._layer):
                    selected_window = window
            else:
                if window.orig_rect.collidepoint(board_coord) and \
                    (selected_window == None or selected_window._layer < window._layer):
                    selected_window = window
        #set as top window if not already top
        if selected_window != None and selected_window != self.window_order[-1]:
            self.remove(selected_window)
            self.add(selected_window)

    def handle_events(self, events):
        """
        Handle events for the topmost window that the mouse is over
        :param events:
        :return:
        """
        if len(self.windows) == 0:
            return events
        for event in events:
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                self.__set_top_window(event.pos)
        if len(self.window_order) > 0:
            event_handling_window = self.window_order[-1]
            events = event_handling_window.handle_events(events)
        return events

    def _screen_to_board_coordinate(self, coord):
        """

        """
        c = self.__target.rect.center
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
        return [x, y]





