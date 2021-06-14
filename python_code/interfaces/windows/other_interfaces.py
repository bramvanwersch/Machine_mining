import pygame
from typing import List, Union, Tuple, TYPE_CHECKING

import interfaces.widgets as widgets
import utility.constants as con
from interfaces.windows import base_interface, file_explorer_interface
import scenes
import utility.utilities as util
if TYPE_CHECKING:
    from utility import inventories
    from board import sprite_groups

# globals
SELECTED_WIDGET: Union[None, widgets.ItemDisplay] = None


def get_selected_item() -> Union[None, "inventories.Item"]:
    """Get the SELECTED_WIDGET item, in this way the item can be retrieved without having to reimport the value"""
    if SELECTED_WIDGET:
        return SELECTED_WIDGET.item
    return None


def reset_selected_widget():
    global SELECTED_WIDGET
    SELECTED_WIDGET = None


class BuildingWindow(base_interface.Window):
    """The building window where a building material can be selected"""
    WINDOW_SIZE: util.Size = util.Size(400, 300)
    WINDOW_POS: Union[Tuple[int, int], List] = (int((con.SCREEN_SIZE.width - WINDOW_SIZE.width) / 2),
                                                int((con.SCREEN_SIZE.height - WINDOW_SIZE.height) / 2))

    __inventory: "inventories.Inventory"
    __scrollable_inventory_widget: Union[None, widgets.ScrollPane]
    __prev_no_items: int

    def __init__(
        self,
        terminal_inventory: "inventories.Inventory",
        *sprite_group: "sprite_groups.CameraAwareLayeredUpdates"
    ):
        super().__init__(self.WINDOW_POS, self.WINDOW_SIZE, *sprite_group, layer=con.INTERFACE_LAYER,
                         title="PICK AN ITEM TO BUILD:", recordable_keys=[1, con.K_ESCAPE])
        self.__inventory = terminal_inventory
        self.__scrollable_inventory_widget = None
        self.__prev_no_items = 0  # value tracked for efficient drawing of the inventory items

        self.__initiate_widgets()

    def __initiate_widgets(self):
        self.__scrollable_inventory_widget = widgets.ScrollPane(self.WINDOW_SIZE - (50, 50), color=self.COLOR[:-1])
        self.add_widget((25, 25), self.__scrollable_inventory_widget)
        self.add_border(self.__scrollable_inventory_widget)

    def update(self, *args):
        """Entity update method, add labels to the scroll pane when needed."""
        super().update(*args)
        if self.__prev_no_items < self.__inventory.number_of_items:
            self.__prev_no_items = self.__inventory.number_of_items
            self.__add_item_labels()

    def __add_item_labels(self):
        """When more different items are encountered then previously in the inventory a new label is added for an item.
        The labels are added to the scrollpane

        First it is figured out what items are new and then a label for each is constructed"""
        # all widgets that are added are ItemDisplay widgets
        covered_items = [widget.item.name() for widget in self.__scrollable_inventory_widget.widgets]  # noqa
        for item in self.__inventory.items:
            if item.name() not in covered_items and item.material.buildable:
                tooltip = widgets.Tooltip(self.groups()[0], text=item.tooltip_text())
                lbl = widgets.ItemDisplay((42, 42), item, color=self.COLOR[:-1], tooltip=tooltip)

                def set_selected(item_lbl, selected):
                    item_lbl.set_selected(selected)
                    if selected:
                        self.select_an_item(item_lbl)

                lbl.add_key_event_listener(1, set_selected, [lbl, True], ["unpressed"])
                self.__scrollable_inventory_widget.add_widget(lbl)

    def select_an_item(
        self,
        widget: widgets.ItemDisplay
    ):
        """Select an item from this building interface to the SELECTED_WIDGET value in order to make it retrievable for
        other functions without having this specific object"""
        global SELECTED_WIDGET
        if SELECTED_WIDGET and widget != SELECTED_WIDGET:
            SELECTED_WIDGET.set_selected(False)
        SELECTED_WIDGET = widget
        # add an event that presses the building key to exit the interface
        newevent = pygame.event.Event(con.KEYUP, unicode="^/",
                                      key=pygame.locals.K_ESCAPE,
                                      mod=pygame.locals.KMOD_NONE)  # create the event
        pygame.event.post(newevent)


class PauseWindow(base_interface.Window):
    """Pause window when in the game that is called from within the game"""
    WINDOW_SIZE = util.Size(400, 500)
    WINDOW_POS = (int((con.SCREEN_SIZE.width - WINDOW_SIZE.width) / 2),
                  int((con.SCREEN_SIZE.height - WINDOW_SIZE.height) / 2))

    def __init__(self, sprite_group):
        super().__init__(self.WINDOW_POS, self.WINDOW_SIZE, sprite_group, title="PAUSED", movable=False)
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
        from interfaces.managers import game_window_manager
        explorer = \
            file_explorer_interface.SaveFileWindow((self.rect.width / 2 - file_explorer_interface.SaveFileWindow.SIZE.width / 2 +
                                                    self.rect.left,
                                                    self.rect.height / 2 - file_explorer_interface.SaveFileWindow.SIZE.height / 2 +
                                                    self.rect.top), self.groups()[0])
        game_window_manager.add(explorer)


class InventoryWindow(base_interface.Window):
    """Interface for inventory buildings"""
    SIZE = util.Size(300, 200)
    COLOR = (173, 94, 29)

    __inventory: "inventories.Inventory"
    __prev_no_items: int
    _inventory_pane: Union[widgets.ScrollPane, None]

    def __init__(
        self,
        rect: pygame.Rect,
        inventory: "inventories.Inventory",
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        title: str = ""
    ):
        self.__inventory = inventory
        super().__init__(rect.topleft, self.SIZE, sprite_group, layer=con.INTERFACE_LAYER, title=title,
                         recordable_keys=[1, 4, 5, con.K_ESCAPE], static=True)
        self.__prev_no_items = 0
        self._inventory_pane = None

        self._init_widgets()

    def _init_widgets(self):
        self._inventory_pane = widgets.ScrollPane(self.SIZE - (20, 20), color=self.COLOR)
        self.add_widget((10, 10), self._inventory_pane)
        self.add_border(self._inventory_pane)

    def update(self, *args):
        """Entity update method, add labels to the scroll pane when needed."""
        super().update(*args)
        if self.__prev_no_items < self.__inventory.number_of_items:
            self.__prev_no_items = self.__inventory.number_of_items
            self.__add_item_labels()

    def __add_item_labels(self):
        """When more different items are encountered then previously in the inventory a new label is added for an item.
        The labels are added to the scrollpane

        First it is figured out what items are new and then a label for each is constructed"""
        # should always be a ItemDisplay
        covered_items = [widget.item.name() for widget in self._inventory_pane.widgets]   # noqa
        for item in self.__inventory.items:
            if item.name() not in covered_items:
                tooltip = widgets.Tooltip(self.groups()[0], text=item.tooltip_text())
                lbl = widgets.ItemDisplay((42, 42), item, color=self.COLOR, tooltip=tooltip)

                self._inventory_pane.add_widget(lbl)
