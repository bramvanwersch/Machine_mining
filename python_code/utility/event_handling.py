from abc import ABC
from typing import List, TYPE_CHECKING

import utility.constants as con

if TYPE_CHECKING:
    import pygame


class EventHandler(ABC):
    """
    Class for handling all sorts of events issued by the user, all events that
    are defined as part of this handler are consumed while looping trough them
    """
    def __init__(self, recordable_keys=None):
        """
        :param recordable_events: a list of keys that the handler should record
        """
        if recordable_keys == "ALL":
            self.__pressed_keys = {key: Key(key) for key in con.KEYBOARD_KEYS}
        elif recordable_keys:
            self.__pressed_keys = {key: Key(key) for key in recordable_keys}
        else:
            self.__pressed_keys = {}
        self._dragging = False

    def add_recordable_key(self, key):
        if key not in self.__pressed_keys:
            self.__pressed_keys[key] = Key(key)

    def __record_pressed_keys(self, events, consume_events=True):
        """
        Record what buttons are pressed in self.__pressed_keys dictionary

        :param events: a list of pygame events
        """
        leftover_events = []
        for event in events:
            if event.type == con.KEYDOWN:
                if event.key in self.__pressed_keys:
                    self.__pressed_keys[event.key].press(event)
                else:
                    leftover_events.append(event)

            elif event.type == con.KEYUP:
                if event.key in self.__pressed_keys:
                    self.__pressed_keys[event.key].unpress(event)
                else:
                    leftover_events.append(event)
            elif event.type == con.MOUSEBUTTONDOWN:
                if event.button in self.__pressed_keys:
                    self.__pressed_keys[event.button].press(event)
                    if event.button == 1:
                        self._dragging = True
                else:
                    leftover_events.append(event)
            elif event.type == con.MOUSEBUTTONUP:
                if event.button in self.__pressed_keys:
                    self.__pressed_keys[event.button].unpress(event)
                    if event.button == 1:
                        self._dragging = False
                else:
                    leftover_events.append(event)
            elif event.type == con.HOVER:
                if event.button in self.__pressed_keys:
                    self.__pressed_keys[event.button].press(event)
                else:
                    leftover_events.append(event)
            elif event.type == con.UNHOVER:
                if event.button in self.__pressed_keys:
                    self.__pressed_keys[event.button].unpress(event)
                else:
                    leftover_events.append(event)
            else:
                leftover_events.append(event)
        if consume_events:
            return leftover_events
        else:
            return events

    def get_key(self, key):
        if key in self.__pressed_keys:
            return self.__pressed_keys[key]
        return None

    def pressed(self, key, continious = False):
        if key in self.__pressed_keys:
            return self.__pressed_keys[key].pressed(continious)
        return False

    def get_all_pressed(self, continious = False):
        pressed_keys = []
        for key in self.__pressed_keys:
            if key in self.__pressed_keys and self.__pressed_keys[key].pressed(continious):
                pressed_keys.append(self.__pressed_keys[key])
        return pressed_keys

    def unpressed(self, key, continious = False):
        if key in self.__pressed_keys:
            return self.__pressed_keys[key].unpressed(continious)
        return False

    def get_all_unpressed(self, continious = False):
        unpressed_keys = []
        for key in self.__pressed_keys:
            if key in self.__pressed_keys and self.__pressed_keys[key].unpressed(continious):
                unpressed_keys.append(self.__pressed_keys[key])
        return unpressed_keys

    def handle_events(
        self,
        events: List["pygame.event.Event"],
        consume_events: bool = True
    ) -> List["pygame.event.Event"]:
        """Base handle event case where all relevant events are recorded and all ignored events are pushed on"""
        return self.__record_pressed_keys(events, consume_events)


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

    def __str__(self):
        return "Key {}. Is pressed {}/ is unpressed {}.".format(self.name, self.__pressed, self.__unpressed)
