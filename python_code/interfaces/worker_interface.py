from typing import List, Union, Tuple, TYPE_CHECKING

from interfaces import other_interfaces, widgets
import utility.utilities as util
import utility.constants as con
if TYPE_CHECKING:
    from utility import inventories
    from board import sprite_groups
    import pygame


class WorkerWindow(other_interfaces.InventoryWindow):
    """The building window where a building material can be selected"""

    def __init__(
        self,
        rect: "pygame.Rect",
        worker_inventory: "inventories.Inventory",
        *sprite_group: "sprite_groups.CameraAwareLayeredUpdates"
    ):
        super().__init__(rect, worker_inventory, *sprite_group, title="WORKER:")

    def _innit_widgets(self):
        self.__scrollable_inventory_widget = widgets.ScrollPane(util.Size(*self.orig_rect.size) - (50, 100),
                                                                color=self.COLOR)
        self.add_widget((25, 25), self.__scrollable_inventory_widget)
        self.add_border(self.__scrollable_inventory_widget)

    def set_location(self, location: Tuple[int, int]):
        self.orig_rect.topleft = location
