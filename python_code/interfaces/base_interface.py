import pygame
from pygame.locals import *

import interfaces.managers as window_managers
from utility.event_handling import EventHandler
from interfaces.interface_utility import screen_to_board_coordinate
from utility.utilities import Size
from utility.constants import KEYDOWN, K_ESCAPE, KMOD_NONE
from interfaces.widgets import Frame, Label, Button
from utility.image_handling import image_sheets

class Window(Frame):
    TOP_SIZE = Size(0, 25)
    EXIT_BUTTON_SIZE = Size(25, 25)
    COLOR = (173, 94, 29, 150)
    TOP_BAR_COLOR = (195, 195, 195)
    TEXT_COLOR = (0,0,0)
    ID = 0
    #optional list of class names of windows that should be closed when this
    # window ia opened or ['ALL'] if all windows need to be closed
    CLOSE_LIST = []

    def __init__(self, pos, size, *groups, color=COLOR, title=None, static=False, **kwargs):
        Frame.__init__(self, pos, size + self.TOP_SIZE, *groups, color=color, **kwargs)

        if not isinstance(size, Size):
            size = Size(*size)
        self.window_manager = window_managers.game_window_manager
        self.static = static

        #values for moving static windows
        self.__moving_window = False
        self.__previous_board_pos = None

        self._show_window = False
        self.__focussed = False
        self.id = "window {}".format(self.ID)
        Window.ID += 1

        #make closable with escape
        self.set_action(K_ESCAPE, self._close_window, types=["unpressed"])
        self.__add_top_border(size, title)

    def update(self, *args):
        super().update(*args)
        if self.__moving_window:
            self.__move_window()

    def is_showing(self):
        return self._visible and self._show_window

    def __add_top_border(self, size, title):
        top_label = Label(Size(size.width - self.EXIT_BUTTON_SIZE.width, self.TOP_SIZE.height),
                          color=self.TOP_BAR_COLOR, selectable=False)
        if self.static:
            top_label.set_action(1, self.__top_label_action, values=[True], types=["pressed"])
            top_label.set_action(1, self.__top_label_action, values=[False], types=["unpressed"])
        self.add_widget((0,0), top_label, adjust=False)
        if title != None:
            top_label.set_text(title, (10,5), self.TEXT_COLOR, font_size=25, add=True)
        button_image = image_sheets["general"].image_at((20,0),self.EXIT_BUTTON_SIZE, color_key=(255,255,255))
        hover_image = image_sheets["general"].image_at((45, 0), self.EXIT_BUTTON_SIZE, color_key=(255, 255, 255))
        exit_button = Button(self.EXIT_BUTTON_SIZE, image=button_image, hover_image=hover_image, selectable=False)
        exit_button.set_action(1, self._close_window, types=["unpressed"])
        self.add_widget((size.width - self.EXIT_BUTTON_SIZE.width, 0), exit_button, adjust=False)

    def add_widget(self, pos, widget, adjust=True):
        if adjust:
            widget.rect.move_ip(self.TOP_SIZE)
        super().add_widget(pos, widget, add=adjust)

    def __top_label_action(self, value):
        self.__moving_window = value
        if value == True:
            self.__previous_board_pos = screen_to_board_coordinate(pygame.mouse.get_pos(), self.groups()[0].target, self._zoom)

    def __move_window(self):
        board_pos = screen_to_board_coordinate(pygame.mouse.get_pos(), self.groups()[0].target, self._zoom)
        moved_x = board_pos[0] - self.__previous_board_pos[0]
        moved_y = board_pos[1] - self.__previous_board_pos[1]
        self.__previous_board_pos = board_pos
        self.orig_rect.move_ip((moved_x, moved_y))

    def _set_title(self, title):
        """
        Permanently add a title to the frame. This is displayed at the top of
        the frame

        :param title: String of what should be displayed
        """
        title = FONTS[15].render(title, True, self.TEXTCOLOR)
        tr = title.get_rect()
        #center the title above the widet
        self.orig_image.blit(title, (int(0.5 * self.rect.width - 0.5 * tr.width), 10))

    def _close_window(self):
        """
        Press the escape key to close the window
        """
        if self.window_manager == None:
            self.window_manager = window_managers.game_window_manager
        self.window_manager.remove(self)

    def set_focus(self, value:bool):
        #things called when losing focus of the window
        self.__focussed = value
        if value == False:
            self.__moving_window = False

    def show_window(self, value: bool):
        """
        Show the window when in the fov of the user

        :param value: boolean toggle to show or not
        """
        self._show_window = value
        if value == False:
            self.__moving_window = False

    def handle_events(self, events):
        """
        Handle events issued by the user not consumed by the Main module. This
        function can also be used as an update method for all things that only
        need updates with new inputs.

        Note: this will trager quite often considering that moving the mouse is
        also considered an event.

        :param events: a list of events
        """
        if self.is_showing():
            leftovers = super().handle_events(events)
        else:
            leftovers = events
        return leftovers

    @classmethod
    def name(self):
        return self.__name__
