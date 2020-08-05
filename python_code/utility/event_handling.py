from abc import ABC

from python_code.utility.constants import *
from python_code.utility.utilities import rect_from_block_matrix

class EventHandler(ABC):
    """
    Class for handling all sorts of events issued by the user, all events that
    are defined as part of this handler are consumed while looping trough them
    """
    def __init__(self, recordable_keys):
        """
        :param recordable_events: a list of keys that the handler should record
        """
        if recordable_keys == "ALL":
            self.__pressed_keys = {key : Key(key) for key in KEYBOARD_KEYS}
        else:
            self.__pressed_keys = {key: Key(key) for key in recordable_keys}
        self._dragging = False

    def __record_pressed_keys(self, events):
        """
        Record what buttons are pressed in self.__pressed_keys dictionary

        :param events: a list of pygame events
        """
        leftover_events = []
        for event in events:
            if event.type == KEYDOWN:
                if event.key in self.__pressed_keys:
                    self.__pressed_keys[event.key].press(event)
            elif event.type == KEYUP:
                if event.key in self.__pressed_keys:
                    self.__pressed_keys[event.key].unpress(event)
            elif event.type == MOUSEBUTTONDOWN:
                if event.button in self.__pressed_keys:
                    self.__pressed_keys[event.button].press(event)
                    if event.button == 1:
                        self._dragging = True
            elif event.type == MOUSEBUTTONUP:
                if event.button in self.__pressed_keys:
                    self.__pressed_keys[event.button].unpress(event)
                    if event.button == 1:
                        self._dragging = False
            else:
                leftover_events.append(event)
        return leftover_events

    def get_key(self, key):
        if key in self.__pressed_keys:
            return self.__pressed_keys[key]
        return None

    def pressed(self, key, continious = False):
        if key in self.__pressed_keys:
            return self.__pressed_keys[key].pressed(continious)
        return False

    def get_pressed(self, continious = False):
        pressed_keys = []
        for key in self.__pressed_keys:
            if key in self.__pressed_keys and self.__pressed_keys[key].pressed(continious):
                pressed_keys.append(self.__pressed_keys[key])
        return pressed_keys

    def unpressed(self, key, continious = False):
        if key in self.__pressed_keys:
            return self.__pressed_keys[key].unpressed(continious)
        return False

    def get_unpressed(self, continious = False):
        unpressed_keys = []
        for key in self.__pressed_keys:
            if key in self.__pressed_keys and self.__pressed_keys[key].unpressed(continious):
                unpressed_keys.append(self.__pressed_keys[key])
        return unpressed_keys

    def handle_events(self, events):
        """
        Handles events for the inheriting class.
        :param events:
        :return:
        """
        return self.__record_pressed_keys(events)

class Key:
    def __init__(self, name):
        self.name = name
        self.__pressed = False
        self.__unpressed = False
        self.event = None

    def press(self, event):
        self.__pressed = True
        self.event = event
        self.__unpressed = False

    def unpress(self, event):
        self.__unpressed = True
        self.event = event
        self.__pressed = False

    def pressed(self, continious = False):
        """
        Make sure that an event is only triggered once on a key press

        :param continious: if set to True this means that a key will continously
        be triggered as long as the key is not unpressed
        :return:
        """
        p = self.__pressed
        if not continious:
            self.__pressed = False
        return p

    def unpressed(self, continious = False):
        """
        Records if the button was unpressed after the last time of it being
        pressed. This event can be checked once. It tracks a BUTTONUP event
        """
        up = self.__unpressed
        if not continious:
            self.__unpressed = False
        return up


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
        self.__handle_mouse_events()
        self.__handle_mode_events()
        return leftover_events

    def __handle_mouse_events(self):
        """
        Handle mouse events issued by the user.
        """
        #mousebutton1
        if self.pressed(1):
            self.selection_image.add_selection_rectangle(self.get_key(1).event.pos, self._mode.persistent_highlight)

        elif self.unpressed(1):
            self.__process_selection()
            self.selection_image.remove_selection()


    def __process_selection(self):
        """
        Process when the user is done selecting and a highlight should appear of the area
        :return:
        """
        if self.selection_image == None or self.selection_image.selection_rectangle == None:
            return
        blocks = self.overlapping_blocks(self.selection_image.selection_rectangle.orig_rect)
        # the user is selecting blocks
        if len(blocks) > 0:
            rect = rect_from_block_matrix(blocks)
            self.selection_image.add_highlight_rectangle(rect, self._mode.color)
            task_rectangles = self._get_task_rectangles(blocks, self._mode.name)
            for rect in task_rectangles:
                self.selection_image.add_rect(rect, INVISIBLE_COLOR)
            self._add_tasks(blocks)


    def __handle_mode_events(self):
        """
        Change the mode of the user and draw some text to notify the user.

        :param event: a pygame event
        """
        pressed_modes = self.get_pressed()
        if len(pressed_modes):
            #make sure to clear the board of any remnants before switching
            self.selection_image.reset_selection_and_highlight(self._mode.persistent_highlight)

            self._mode = MODES[pressed_modes[0].name]
            #for now print what the mode is, TODO add this into the gui somewhere
            print(self._mode.name)

