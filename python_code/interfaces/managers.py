import pygame

import utility.constants as con
import interfaces.windows.interface_utility as util
from interfaces.windows import base_interface


game_window_manager = None


def create_window_managers(camera_target):
    global game_window_manager
    game_window_manager = WindowManager(camera_target)


class WindowManager:
    def __init__(self, target):
        self.windows = {}
        self.window_order = []
        self.__target = target

    def add(self, window):
        # dont add the same window multiple times
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
            window._layer = con.INTERFACE_LAYER
        else:
            window._layer = self.window_order[-1]._layer + 1
        self.window_order.append(window)
        window.show_window(True)

    def remove(self, window):
        del self.windows[window.id]
        rem_index = self.window_order.index(window)
        if rem_index + 1 == len(self.window_order):
            self.window_order.pop()
        else:
            self.window_order.pop(rem_index)
            for w in self.window_order:
                w._layer = max(w._layer - 1, con.INTERFACE_LAYER)
        window.show_window(False)

    def __set_top_window(self, window):
        # remove then re-add the window without changing the visibility or closing other windows
        # set as top window if not already top
        if window != self.window_order[-1]:
            # remove the window first
            del self.windows[window.id]
            rem_index = self.window_order.index(window)
            if rem_index + 1 == len(self.window_order):
                self.window_order.pop()
            else:
                self.window_order.pop(rem_index)
                for w in self.window_order:
                    w._layer = max(w._layer - 1, con.INTERFACE_LAYER)

            # then re-add it.
            self.windows[window.id] = window
            if len(self.window_order) == 0:
                window._layer = con.INTERFACE_LAYER
            else:
                window._layer = self.window_order[-1]._layer + 1
            self.window_order.append(window)

    def __find_hovered_window(self, mouse_pos):
        board_coord = util.screen_to_board_coordinate(mouse_pos, self.__target, 1)
        selected_window = None
        for window in self.windows.values():
            if window.static:
                if window.rect.collidepoint(board_coord) and \
                        (selected_window is None or selected_window.layer < window.layer):
                    selected_window = window
            else:
                if window.orig_rect.collidepoint(mouse_pos) and \
                        (selected_window is None or selected_window.layer < window.layer):
                    selected_window = window
        return selected_window

    def handle_events(self, events):
        """
        Handle keyboard evets for the selected window and mouse events for the hovered window

        :param events:
        :return:
        """
        if len(self.windows) == 0:
            return events
        hovered_window = self.__find_hovered_window(pygame.mouse.get_pos())
        # if TopWindow is at the top then only process hovered based events for that window
        if hovered_window != self.window_order[-1] and self.window_order[-1].is_top_window:
            hovered_window = None
        window_other_events = []
        window_mouse_events = []
        ignored_events = []
        #select a window when the user clicks it and collect all mouse events (and others)
        #if hovering over the window
        for event in events:
            if event.type in (con.MOUSEBUTTONDOWN, con.MOUSEBUTTONUP):
                #make sure to unfocus when clicking outside
                if hovered_window != self.window_order[-1]:
                    self.window_order[-1].set_focus(False)
                if hovered_window != None:
                    if event.button == 1 and event.type == con.MOUSEBUTTONDOWN:
                        self.__set_top_window(hovered_window)
                        hovered_window.set_focus(True)
                    window_mouse_events.append(event)
                else:
                    ignored_events.append(event)
            else:
                window_other_events.append(event)
        leftover_events = []
        if len(self.window_order) > 0:
            event_handling_window = self.window_order[-1]
            leftover_events = event_handling_window.handle_other_events(window_other_events)
        if hovered_window:
            hovered_window.handle_mouse_events(window_mouse_events)
        return leftover_events + ignored_events
