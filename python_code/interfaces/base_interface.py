import pygame
from pygame.locals import *

import python_code.interfaces.managers as window_managers
from python_code.utility.event_handling import EventHandler
from python_code.interfaces.interface_utility import screen_to_board_coordinate
from python_code.utility.utilities import Size
from python_code.utility.constants import KEYDOWN, K_ESCAPE, KMOD_NONE
from python_code.interfaces.widgets import Frame, Label, Button
from python_code.utility.image_handling import image_sheets

class Window(Frame, EventHandler):
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
        EventHandler.__init__(self, [])
        Frame.__init__(self, pos, size + self.TOP_SIZE, *groups, color=color, **kwargs)
        self.window_manager = window_managers.window_manager
        self.static = static

        #values for moving static windows
        self.__moving_window = False
        self.__previous_board_pos = None

        self.visible = False
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

    def __add_top_border(self, size, title):
        top_label = Label((0,0), Size(size.width - self.EXIT_BUTTON_SIZE.width, self.TOP_SIZE.height), color=self.TOP_BAR_COLOR)
        if self.static:
            top_label.set_action(1, self.__top_label_action, values=[True], types=["pressed"])
            top_label.set_action(1, self.__top_label_action, values=[False], types=["unpressed"])
        self.add_widget(top_label, adjust=False)
        if title != None:
            top_label.set_text(title, (10,5), self.TEXT_COLOR, font_size=25, add=True)
        button_image = image_sheets["general"].image_at((20,0),self.EXIT_BUTTON_SIZE, color_key=(255,255,255))
        hover_image = image_sheets["general"].image_at((45, 0), self.EXIT_BUTTON_SIZE, color_key=(255, 255, 255))
        exit_button = Button((size.width - self.EXIT_BUTTON_SIZE.width, 0), self.EXIT_BUTTON_SIZE, image=button_image, hover_image=hover_image)
        exit_button.set_action(1, self._close_window, types=["unpressed"])
        self.add_widget(exit_button, adjust=False)

    def add_widget(self, widget, adjust=True):
        if adjust:
            widget.rect.move_ip(self.TOP_SIZE)
        super().add_widget(widget)

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
            self.window_manager = window_managers.window_manager
        self.window_manager.remove(self)

    def set_focus(self, value:bool):
        #things called when losing focus of the window
        self.__focussed = value
        if value == False:
            self.__moving_window = False

    def show(self, value: bool):
        """
        Toggle showing the crafting window or not. This also makes sure that no
        real updates are pushed while the window is invisible

        :param value: a boolean
        """
        self.visible = value
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
        if self.visible:
            leftovers = super().handle_events(events)
            #check for events that are not normally triggered twice
            for event in events:
                if event.type == MOUSEBUTTONUP and event.button == 1:
                    self.__moving_window = False
                    break
            return leftovers
        return events

    @classmethod
    def name(self):
        return self.__name__
