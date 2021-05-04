from typing import List, Union, Tuple, TYPE_CHECKING

from interfaces import other_interfaces, widgets
import utility.utilities as util
import utility.constants as con
if TYPE_CHECKING:
    from entities import Worker
    from board import sprite_groups
    import pygame
    import tasks


class WorkerWindow(other_interfaces.InventoryWindow):
    """The building window where a building material can be selected"""

    def __init__(
        self,
        rect: "pygame.Rect",
        worker: "Worker",
        *sprite_group: "sprite_groups.CameraAwareLayeredUpdates"
    ):
        self._worker = worker
        self._general_information_pane = None

        self._previous_name = worker.number
        self._name_lbl = None

        self._previous_speed = round(self._worker.speed.x), round(self._worker.speed.y)
        self._speed_lbl = None

        self._previous_max_speed = worker.max_speed
        self._max_speed_lbl = None

        self._previous_location = worker.orig_rect.topleft
        self._location_lbl = None

        self._previous_wheight = worker.inventory.wheight[0], worker.inventory.wheight[1]
        self._wheight_lbl = None

        self._previous_number_tasks = len(worker.task_queue)
        self._task_information_pane = None

        super().__init__(rect, worker.inventory, *sprite_group, title="WORKER:")

    def _init_widgets(self):
        self._general_information_pane = widgets.Pane(util.Size(150, self.orig_rect.height / 2) - (30, 30))
        self.add_widget((15, 15), self._general_information_pane, adjust=True)
        self.add_border(self._general_information_pane)

        y = 5
        name_name_lbl = widgets.Label(util.Size(60, 10), text="Name: ", text_pos=("west", "center"))
        self._general_information_pane.add_widget((5, y), name_name_lbl)

        self._name_lbl = widgets.Label(util.Size(75, 10), text=str(self._worker.number), text_pos=("west", "center"))
        self._general_information_pane.add_widget((70, y), self._name_lbl)

        y += 15
        speed_name_lbl = widgets.Label(util.Size(60, 10), text="Speed: ", text_pos=("west", "center"))
        self._general_information_pane.add_widget((5, y), speed_name_lbl)

        self._speed_lbl = widgets.Label(util.Size(75, 10),
                                        text=f"{self._previous_speed[0]}, {self._previous_speed[1]}",
                                        text_pos=("west", "center"))
        self._general_information_pane.add_widget((70, y), self._speed_lbl)

        y += 15
        max_speed_name_lbl = widgets.Label(util.Size(60, 10), text="Max speed: ", text_pos=("west", "center"))
        self._general_information_pane.add_widget((5, y), max_speed_name_lbl)

        self._max_speed_lbl = widgets.Label(util.Size(75, 10), text=str(self._worker.max_speed),
                                            text_pos=("west", "center"))
        self._general_information_pane.add_widget((70, y), self._max_speed_lbl)

        y += 15
        location_name_lbl = widgets.Label(util.Size(60, 10), text="Location: ", text_pos=("west", "center"))
        self._general_information_pane.add_widget((5, y), location_name_lbl)

        self._location_lbl = widgets.Label(util.Size(75, 10),
                                           text=f"{self._worker.orig_rect.left}, {self._worker.orig_rect.right}",
                                           text_pos=("west", "center"))
        self._general_information_pane.add_widget((70, y), self._location_lbl)

        y += 15
        wheight_name_lbl = widgets.Label(util.Size(60, 10), text="Wheight: ", text_pos=("west", "center"))
        self._general_information_pane.add_widget((5, y), wheight_name_lbl)

        self._wheight_lbl = widgets.Label(util.Size(75, 10), text=str(self._previous_wheight),
                                          text_pos=("west", "center"))
        self._general_information_pane.add_widget((70, y), self._wheight_lbl)

        self._task_information_pane = widgets.ScrollPane(util.Size(150, self.orig_rect.height / 2) - (30, 30))
        self.add_widget((165, 15), self._task_information_pane, adjust=True)
        self.add_border(self._task_information_pane)

        self._inventory_pane = widgets.ScrollPane(util.Size(300, self.orig_rect.height / 2) - (30, 50),
                                                  color=self.COLOR)
        self.add_widget((15, int(self.orig_rect.height / 2) + 10), self._inventory_pane, adjust=True)
        self.add_border(self._inventory_pane)

    def show_window(
        self,
        is_showing: bool
    ):
        super().show_window(is_showing)
        self.orig_rect.topleft = self._worker.orig_rect.bottomleft

    def update(self, *args):
        super().update(*args)
        self.__check_name()
        self.__check_speed()
        self.__check_max_speed()
        self.__check_location()
        self.__check_wheight()
        self.__check_tasks()

    def __check_name(self):
        if self._worker.number != self._previous_name:
            self._previous_name = self._worker.number
            self._name_lbl.set_text(self._worker.number, pos=("west", "center"))

    def __check_speed(self):
        if self._worker.speed != self._previous_speed:
            self._previous_speed = round(self._worker.speed.x), round(self._worker.speed.y)
            self._speed_lbl.set_text(f"{self._previous_speed[0]}, {self._previous_speed[1]}", pos=("west", "center"))

    def __check_max_speed(self):
        if self._worker.max_speed != self._previous_max_speed:
            self._previous_max_speed = self._worker.max_speed
            self._max_speed_lbl.set_text(self._worker.max_speed, pos=("west", "center"))

    def __check_location(self):
        if self._worker.orig_rect.topleft != self._previous_location:
            self._previous_location = self._worker.orig_rect.topleft
            self._location_lbl.set_text(f"{self._worker.orig_rect.left}, {self._worker.orig_rect.right}",
                                        pos=("west", "center"))

    def __check_wheight(self):
        if self._previous_wheight != self._worker.inventory.wheight:
            self._previous_wheight = self._worker.inventory.wheight[0], self._worker.inventory.wheight[1]
            self._wheight_lbl.set_text(str(self._previous_wheight), pos=("west", "center"))

    def __check_tasks(self):
        if len(self._worker.task_queue) != self._previous_number_tasks:
            self._previous_number_tasks = len(self._worker.task_queue)
            [self._task_information_pane.remove_widget(widget) for widget in self._task_information_pane.widgets]
            for task in self._worker.task_queue.tasks:
                task_label = widgets.Label(util.Size(130, 10), text=str(task), text_pos=["west", "center"])
                self._task_information_pane.add_widget(task_label)
