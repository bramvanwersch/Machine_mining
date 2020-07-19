from abc import ABC, abstractmethod

from python_code.constants import *

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

    def __record_pressed_keys(self, events):
        """
        Record what buttons are pressed in self._pressed_keys dictionary

        :param events: a list of pygame events
        """
        for event in events:
            if event.type == KEYDOWN:
                if event.key in self._pressed_keys:
                    self._pressed_keys[event.key] = True
            elif event.type == KEYUP:
                if event.key in self._pressed_keys:
                    self._pressed_keys[event.key] = False

    @abstractmethod
    def handle_events(self, events):
        """
        Handles events for the inheriting class.
        :param events:
        :return:
        """
        return self.__record_pressed_keys(events)