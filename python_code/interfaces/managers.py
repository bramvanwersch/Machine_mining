import pygame

from python_code.utility.constants import SCREEN_SIZE, BOARD_SIZE, INTERFACE_LAYER, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from python_code.interfaces.interface_utility import screen_to_board_coordinate

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
        close_all = False
        for name in window.CLOSE_LIST:
            if name == 'ALL':
                close_all = True
            for index in range(len(self.window_order) - 1, -1, -1):
                open_window = self.window_order[index]
                if open_window.name() == name or close_all:
                    self.remove(open_window)
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

    def __set_top_window(self, window):
        #set as top window if not already top
        if window != self.window_order[-1]:
            self.remove(window)
            self.add(window)

    def __find_hovered_window(self, mouse_pos):
        board_coord = screen_to_board_coordinate(mouse_pos, self.__target, 1)
        selected_window = None
        for window in self.windows.values():
            if window.static:
                if window.rect.collidepoint(board_coord) and \
                        (selected_window == None or selected_window._layer < window._layer):
                    selected_window = window
            else:
                if window.orig_rect.collidepoint(mouse_pos) and \
                        (selected_window == None or selected_window._layer < window._layer):
                    selected_window = window
        return selected_window

    def handle_events(self, events):
        """
        Handle events for the topmost window that the mouse is over
        :param events:
        :return:
        """
        if len(self.windows) == 0:
            return events
        hovered_window = self.__find_hovered_window(pygame.mouse.get_pos())
        window_events = []
        ignored_events = []
        #select a window when the user clicks it and collect all mouse events (and others)
        #if hovering over the window
        for event in events:
            if event.type in (MOUSEBUTTONDOWN, MOUSEBUTTONUP):
                if hovered_window != None:
                    if event.button == 1:
                        self.__set_top_window(hovered_window)
                    window_events.append(event)
                else:
                    ignored_events.append(event)
            else:
                window_events.append(event)
        leftover_events = []
        if len(self.window_order) > 0:
            event_handling_window = self.window_order[-1]
            leftover_events = event_handling_window.handle_events(window_events)
        return leftover_events + ignored_events
