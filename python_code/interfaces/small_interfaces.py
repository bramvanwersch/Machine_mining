import pygame
from typing import List, Union, Tuple

import interfaces.widgets as widgets
import utility.constants as con
import interfaces.base_interface as base_interfaces
import scenes
import utility.utilities as util

# globals
SELECTED_WIDGET = None


def select_an_item(widget):
    global SELECTED_WIDGET
    if SELECTED_WIDGET and widget != SELECTED_WIDGET:
        SELECTED_WIDGET.set_selected(False)
    SELECTED_WIDGET = widget
    # add an event that presses the building key to exit the interface
    newevent = pygame.event.Event(con.KEYUP, unicode="^/",
                                  key=pygame.locals.K_ESCAPE,
                                  mod=pygame.locals.KMOD_NONE)  # create the event
    pygame.event.post(newevent)


def get_selected_item():
    if SELECTED_WIDGET:
        return SELECTED_WIDGET.item
    return None


class BuildingWindow(base_interfaces.Window):
    CLOSE_LIST = ["CraftingWindow"]
    WINDOW_SIZE: util.Size = util.Size(400, 300)
    WINDOW_POS: Union[Tuple[int, int], List] = (int((con.SCREEN_SIZE.width - WINDOW_SIZE.width) / 2),
                                                int((con.SCREEN_SIZE.height - WINDOW_SIZE.height) / 2))

    def __init__(self, terminal_inventory, *groups):
        super().__init__(self.WINDOW_POS, self.WINDOW_SIZE,
                         *groups, layer=con.INTERFACE_LAYER, title="PICK AN ITEM TO BUILD:",
                         allowed_events=[1, con.K_ESCAPE])
        self.__inventory = terminal_inventory
        self._inventory_sp = None
        self.__initiate_widgets()

        self.__prev_no_items = self.__inventory.number_of_items

    def update(self, *args):
        """
        Entity update method, add labels to the scroll pane when needed.
        """
        super().update(*args)
        if self.__prev_no_items < self.__inventory.number_of_items:
            self.__prev_no_items = self.__inventory.number_of_items
            self.__add_item_labels()

    def __add_item_labels(self):
        """
        When more different items are encountered then previously in the
        inventory a new label is added for an item. The labels are added to the
        scrollpane

        First it is figured out what items are new and then a label for each is
        constructed
        """
        covered_items = [widget.item.name() for widget in self._inventory_sp.widgets]
        for item in self.__inventory.items:
            if item.name() not in covered_items and item.material.buildable:
                # remove the alpha channel
                tooltip = widgets.Tooltip(self.groups()[0], text=item.tooltip_text())
                lbl = widgets.ItemDisplay((42, 42), item, color=self.COLOR[:-1], tooltip=tooltip)

                def set_selected(self, selected):
                    self.set_selected(selected)
                    if selected:
                        select_an_item(self)

                lbl.add_key_event_listener(1, set_selected, [lbl, True], ["pressed"])
                self._inventory_sp.add_widget(lbl)

    def __initiate_widgets(self):
        # create scrollable inventory
        self._inventory_sp = widgets.ScrollPane(self.WINDOW_SIZE - (50, 50), color=self.COLOR[:-1])
        self.add_widget((25, 25), self._inventory_sp)
        self.add_border(self._inventory_sp)


class PauseWindow(base_interfaces.Window):
    WINDOW_SIZE = util.Size(400, 500)
    WINDOW_POS = (int((con.SCREEN_SIZE.width - WINDOW_SIZE.width) / 2),
                  int((con.SCREEN_SIZE.height - WINDOW_SIZE.height) / 2))

    def __init__(self, sprite_group):
        super().__init__(self.WINDOW_POS, self.WINDOW_SIZE, sprite_group, title="PAUSED")
        self.__init_widgets()

    def __init_widgets(self):
        button_size = util.Size(120, 40)
        y_coord = 150

        continue_button = widgets.Button(button_size, color=(100, 100, 100), text="CONTINUE", font_size=30)
        continue_button.add_key_event_listener(1, self._close_window, types=["unpressed"])
        self.add_widget(("center", y_coord), continue_button)

        y_coord += 50
        save_button = widgets.Button(button_size, color=(100, 100, 100), text="SAVE", font_size=30)
        save_button.add_key_event_listener(1, self.__save, types=["unpressed"])
        self.add_widget(("center", y_coord), save_button)

        y_coord += 50
        exit_button = widgets.Button(button_size, color=(100, 100, 100), text="EXIT", font_size=30)
        exit_button.add_key_event_listener(1, self.__back_to_main_menu, types=["unpressed"])
        self.add_widget(("center", y_coord), exit_button)

    def __back_to_main_menu(self):
        scenes.scenes.set_active_scene("MainMenu")

    def __save(self):
        scenes.scenes["Game"].save()


class TerminalWindow(base_interfaces.Window):
    SIZE = util.Size(200, 100)
    COLOR = (173, 94, 29)

    def __init__(self, terminal_object, *groups, recipes=None):
        self.__terminal = terminal_object
        self.__terminal_inv = self.__terminal.blocks[0][0].inventory
        fr = self.__terminal.rect
        location = fr.bottomleft
        super().__init__(location, self.SIZE,
                         *groups, layer=con.INTERFACE_LAYER, title="TERMINAL",
                         allowed_events=[1, 4, 5, con.K_ESCAPE], static=True)
        self.__add_widgets()
        self.__prev_no_items = self.__terminal_inv.number_of_items

    def update(self, *args):
        """
        Entity update method, add labels to the scroll pane when needed.
        """
        super().update(*args)
        if self.__prev_no_items < self.__terminal_inv.number_of_items:
            self.__prev_no_items = self.__terminal_inv.number_of_items
            self.__add_item_labels()

    def __add_item_labels(self):
        """
        When more different items are encountered then previously in the
        inventory a new label is added for an item. The labels are added to the
        scrollpane

        First it is figured out what items are new and then a label for each is
        constructed
        """
        covered_items = [widget.item.name() for widget in self.__inventory_pane.widgets]
        for item in self.__terminal_inv.items:
            if item.name() not in covered_items:
                tooltip = widgets.Tooltip(self.groups()[0], text=item.tooltip_text())
                lbl = widgets.ItemDisplay((42, 42), item, color=self.COLOR, tooltip=tooltip)

                self.__inventory_pane.add_widget(lbl)

    def __add_widgets(self):
        self.__inventory_pane = widgets.ScrollPane(self.SIZE - (20, 20), color=self.COLOR)
        self.add_widget((10, 10), self.__inventory_pane)
        self.add_border(self.__inventory_pane)
