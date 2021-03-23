import pygame
from pygame.locals import *
from typing import List, Union, Tuple, TYPE_CHECKING

import interfaces.managers as window_managers
import interfaces.interface_utility as interfacer_util
import utility.utilities as util
import utility.constants as con
import interfaces.widgets as widgets
from utility import image_handling as image_handlers, event_handling
if TYPE_CHECKING:
    from board import sprite_groups


class Window(widgets.Frame):
    """A basic window with a top bar and keybinds for closing with escape. It wraps a Frame"""

    TOP_SIZE: util.Size = util.Size(0, 25)
    EXIT_BUTTON_SIZE: util.Size = util.Size(25, 25)
    COLOR: Union[Tuple[int, int, int, int], Tuple[int, int, int], List[int]] = (173, 94, 29, 150)
    TOP_BAR_COLOR: Union[Tuple[int, int, int], List[int]] = (195, 195, 195)
    TEXT_COLOR: Union[Tuple[int, int, int], List[int]] = (0, 0, 0)
    ID: int = 0
    # optional list of class names of windows that should be closed when this
    # window ia opened or ['ALL'] if all windows need to be closed
    CLOSE_LIST: List[str] = []

    window_manager: Union[None, window_managers.WindowManager]
    __previous_board_pos: Union[None, Tuple[int, int], List[int]]
    _is_window_moving: bool  # track if the window is being moved by the user
    _is_window_showing: bool  # track if the window is within the users fov
    _is_window_focussed: bool  # track if the window is focussed and if it should recieve keyboard events as a result
    id: str  # track the window with a unique id that is not presee instance dependant

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        size: Union[util.Size, Tuple[int, int], List[int]],
        *groups: "sprite_groups.CameraAwareLayeredUpdates",
        color=COLOR,
        title: Union[str, None] = None,
        static: bool = False,
        **kwargs
    ):
        super().__init__(pos, size + self.TOP_SIZE, *groups, color=color, static=static, **kwargs)

        if not isinstance(size, util.Size):
            size = util.Size(*size)
        self.window_manager = window_managers.game_window_manager

        # values for moving static windows
        self._is_window_moving = False
        self.__previous_board_pos = None

        self._is_window_showing = False
        self._is_window_focussed = False
        self.id = "window {}".format(self.ID)
        Window.ID += 1

        # make closable with escape
        self.add_key_event_listener(K_ESCAPE, self._close_window, types=["unpressed"])
        self.__add_top_border(size, title)

    def update(self, *args):
        super().update(*args)
        if self._is_window_moving:
            self.__move_window()

    def is_showing(self) -> bool:
        """If the window is within the fov of the user and the window itself if visible based on user input."""
        return self._visible and self._is_window_showing

    def __add_top_border(
        self,
        size: util.Size,
        title: Union[str, None]
    ):
        """Add the top bar of the window with the exit button"""
        top_label = widgets.Label(util.Size(size.width - self.EXIT_BUTTON_SIZE.width, self.TOP_SIZE.height),
                                  color=self.TOP_BAR_COLOR, selectable=False)
        # add the move listeners
        top_label.add_key_event_listener(1, self.__top_label_action, values=[True], types=["pressed"])
        top_label.add_key_event_listener(1, self.__top_label_action, values=[False], types=["unpressed"])
        self.add_widget((0, 0), top_label, adjust=False)

        if title is not None:
            top_label.set_text(title, (10, 5), self.TEXT_COLOR, font_size=25)
        button_image = image_handlers.image_sheets["general"].image_at((20, 0), self.EXIT_BUTTON_SIZE)
        hover_image = image_handlers.image_sheets["general"].image_at((45, 0), self.EXIT_BUTTON_SIZE)
        exit_button = widgets.Button(self.EXIT_BUTTON_SIZE, image=button_image, hover_image=hover_image,
                                     selectable=False)
        exit_button.add_key_event_listener(1, self._close_window, types=["unpressed"])
        self.add_widget((size.width - self.EXIT_BUTTON_SIZE.width, 0), exit_button, adjust=False)

    def __top_label_action(
        self,
        is_moving: bool
    ):
        """Function for the action of moving the top label"""
        self._is_window_moving = is_moving
        if is_moving is True:
            # as far as i know this is the best way to acces the main sprite group of this sprite
            self.__previous_board_pos = \
                interfacer_util.screen_to_board_coordinate(pygame.mouse.get_pos(), self.groups()[0].target, self._zoom)  # noqa

    def add_widget(
        self,
        pos: Union[Tuple[Union[int, str], Union[int, str]], List[Union[int, str]]],
        widget: widgets.Widget,
        adjust: bool = True
    ):
        """Add a widget to this window. Wraps the Frame method but allows a adjust argument to adjust the widgut
        downwards based on the size of the topbar"""
        if adjust:
            widget.rect.move_ip([*self.TOP_SIZE])
        super().add_widget(pos, widget, add_topleft=adjust)

    def __move_window(self):
        """Move the window based on the previous position and the current one on the board"""
        board_pos = \
            interfacer_util.screen_to_board_coordinate(pygame.mouse.get_pos(), self.groups()[0].target, self._zoom)  # noqa
        moved_x = board_pos[0] - self.__previous_board_pos[0]
        moved_y = board_pos[1] - self.__previous_board_pos[1]
        self.__previous_board_pos = board_pos
        self.orig_rect.move_ip((moved_x, moved_y))

    def _close_window(self):
        """Press the escape key to close the window"""
        if self.window_manager is None:
            self.window_manager = window_managers.game_window_manager
        self.window_manager.remove(self)
        mock_key = event_handling.Key(con.BTN_HOVER)
        self._reset_hovers(mock_key)

    def set_focus(
        self,
        is_focussed: bool
    ):
        """actions performed when losing focus of the window"""
        self._is_window_focussed = is_focussed
        if is_focussed is False:
            self._is_window_moving = False

    def show_window(
        self,
        is_showing: bool
    ):
        """Show the window when in the fov of the user"""
        self._is_window_showing = is_showing
        if is_showing is False:
            self._is_window_moving = False

    def handle_mouse_events(
        self,
        events: List[pygame.event.Event],
        consume_events: bool = True
    ) -> List[pygame.event.Event]:
        """Handle mouse events issued by the user. These events trigger when this window is hovered"""
        if self.is_showing():
            leftovers = super().handle_mouse_events(events, consume_events=consume_events)
            return leftovers
        else:
            return events

    def handle_other_events(
        self,
        events: List[pygame.event.Event],
        consume_events: bool = True
    ) -> List[pygame.event.Event]:
        """Handle keyboard events issued by the user. These events trigger when the window is focussed"""
        if self.is_showing():
            leftovers = super().handle_other_events(events, consume_events=consume_events)
            return leftovers
        else:
            return events

    @classmethod
    def name(cls):
        return cls.__name__
