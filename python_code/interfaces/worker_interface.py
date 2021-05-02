from typing import List, Union, Tuple, TYPE_CHECKING

from interfaces import other_interfaces, widgets
import utility.utilities as util
import utility.constants as con
if TYPE_CHECKING:
    from entities import Worker
    from board import sprite_groups
    import pygame


class WorkerWindow(other_interfaces.InventoryWindow):
    """The building window where a building material can be selected"""

    def __init__(
        self,
        rect: "pygame.Rect",
        worker: "Worker",
        *sprite_group: "sprite_groups.CameraAwareLayeredUpdates"
    ):
        self._worker = worker
        super().__init__(rect, worker.inventory, *sprite_group, title="WORKER:")

    def _init_widgets(self):
        self._worker_information_pane = widgets.Pane(util.Size(150, self.orig_rect.height / 2) - (30, 30))
        self.add_widget((15, 15), self._worker_information_pane, adjust=True)
        self.add_border(self._worker_information_pane)

        name_name_lbl = widgets.Label(util.Size(75, 10), text="Name: ", text_pos=("west", "center"))
        self._worker_information_pane.add_widget((5, 5), name_name_lbl)

        self._name_lbl = widgets.Label(util.Size(75, 10), text=str(self._worker.number), text_pos=("west", "center"))
        self._worker_information_pane.add_widget((80, 5), self._name_lbl)

        name_name_lbl = widgets.Label(util.Size(75, 10), text="Current speed: ", text_pos=("west", "center"))
        self._worker_information_pane.add_widget((5, 5), name_name_lbl)

        self._name_lbl = widgets.Label(util.Size(75, 10), text=str(self._worker.speed), text_pos=("west", "center"))
        self._worker_information_pane.add_widget((80, 5), self._name_lbl)

        name_name_lbl = widgets.Label(util.Size(75, 10), text="Max speed", text_pos=("west", "center"))
        self._worker_information_pane.add_widget((5, 5), name_name_lbl)

        self._name_lbl = widgets.Label(util.Size(75, 10), text=str(self._worker.max_speed), text_pos=("west", "center"))
        self._worker_information_pane.add_widget((80, 5), self._name_lbl)

        self._inventory_pane = widgets.ScrollPane(util.Size(300, self.orig_rect.height / 2) - (30, 50),
                                                  color=self.COLOR)
        self.add_widget((15, int(self.orig_rect.height / 2) + 10), self._inventory_pane, adjust=True)
        self.add_border(self._inventory_pane)

    def set_location(self, location: Tuple[int, int]):
        self.orig_rect.topleft = location
