from abc import ABC, abstractmethod

from python_code.constants import *
from python_code.utilities import rect_from_block_matrix

class EventHandler(ABC):
    """
    Class for handling all sorts of events issued by the user, all events that
    are defined as part of this handler are consumed while looping trough them
    """
    def __init__(self, recordable_keys):
        """
        :param recordable_events: a list of keys that the handler should record
        """
        self._pressed_keys = {key: False for key in recordable_keys}
        self._dragging = False

    def __record_pressed_keys(self, events):
        """
        Record what buttons are pressed in self._pressed_keys dictionary

        :param events: a list of pygame events
        """
        leftover_events = []
        for event in events:
            if event.type == KEYDOWN:
                if event.key in self._pressed_keys:
                    self._pressed_keys[event.key] = True
            elif event.type == KEYUP:
                if event.key in self._pressed_keys:
                    self._pressed_keys[event.key] = False
            elif event.type == MOUSEBUTTONDOWN:
                if event.button in self._pressed_keys:
                    self._pressed_keys[event.button] = True
                    if event.button == 1:
                        self._dragging = True
            elif event.type == MOUSEBUTTONUP:
                if event.button in self._pressed_keys:
                    self._pressed_keys[event.button] = False
                    if event.button == 1:
                        self._dragging = False
            else:
                leftover_events.append(event)
        return leftover_events

    @abstractmethod
    def handle_events(self, events):
        """
        Handles events for the inheriting class.
        :param events:
        :return:
        """
        return self.__record_pressed_keys(events)


class BoardEventHandler(EventHandler, ABC):
    """
    Class for handling events issued to the board. This class has to be
    instantiated by a board object since it relies on board methods and
    variables
    """
    def __init__(self, recordable_keys):
        super().__init__(recordable_keys)
        self._mode = MODES[SELECTING]


    def handle_events(self, events):
        """
        Handle events issued to the board.

        :param events: a list of pygame Event objects
        :return: events that where not processed for wathever reason
        """
        leftover_events = EventHandler.handle_events(self, events)
        for event in events:
            if event.type == MOUSEBUTTONUP or event.type == MOUSEBUTTONDOWN:
                event = self.__handle_mouse_events(event)
            elif event.type == KEYDOWN or event.type == KEYUP:
                event = self.__handle_mode_events(event)
        return leftover_events

    def __handle_mouse_events(self, event):
        """
        Handle mouse events issued by the user.

        :param event: a pygame event
        :return: an event when the event was not processed otherwise None
        """
        if event.type == MOUSEBUTTONDOWN and self._pressed_keys[1]:
            self.selection_image.add_selection_rectangle(event.pos, self._mode.persistent_highlight)

        elif event.type == MOUSEBUTTONUP and event.button == 1:
            self.__process_selection()
            self.selection_image.remove_selection()
        else:
            return event

    def __process_selection(self):
        """
        Process when the user is done selecting and a highlight should appear of the area
        :return:
        """
        blocks = self.overlapping_blocks(self.selection_image.selection_rectangle.orig_rect)
        # the user is selecting blocks
        if len(blocks) > 0:
            rect = rect_from_block_matrix(blocks)
            self.selection_image.add_highlight_rectangle(rect, self._mode.color)
            task_rectangles = self._get_task_rectangles(blocks, self._mode.name)
            for rect in task_rectangles:
                self.selection_image.add_rect(rect, INVISIBLE_COLOR)
            self._add_tasks(blocks)


    def __handle_mode_events(self, event):
        """
        Change the mode of the user and draw some text to notify the user.

        :param event: a pygame event
        """
        if event.key in self._pressed_keys and self._pressed_keys[event.key]:
            #make sure to clear the board of any remnants before switching
            self.selection_image.reset_selection_and_highlight(self._mode.persistent_highlight)

            self._mode = MODES[event.key]
            #for now print what the mode is, TODO add this into the gui somewhere
            print(self._mode.name)


