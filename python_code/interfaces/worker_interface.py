from typing import Union, Tuple, TYPE_CHECKING

from interfaces import other_interfaces, widgets
import utility.utilities as util
if TYPE_CHECKING:
    from entities import Worker
    from board import sprite_groups
    import pygame


class WorkerWindow(other_interfaces.InventoryWindow):
    """The building window where a building material can be selected"""

    _worker: "Worker"
    _general_information_pane: Union[widgets.Pane, None]
    _previous_name: str
    _name_lbl: Union[widgets.MultilineTextBox, None]
    _previous_speed: Tuple[int, int]
    _speed_lbl: Union[widgets.Label, None]
    _previous_max_speed: int
    _max_speed_lbl: Union[widgets.Label, None]
    _previous_location: Tuple[int, int]
    _location_lbl: Union[widgets.Label, None]
    _previous_wheight: Tuple[int, int]
    _wheight_lbl: Union[widgets.Label, None]
    _previous_number_tasks: int
    _task_information_pane: Union[widgets.ScrollPane, None]

    def __init__(
        self,
        rect: "pygame.Rect",
        worker: "Worker",
        *sprite_group: "sprite_groups.CameraAwareLayeredUpdates"
    ):
        self._worker = worker
        self._general_information_pane = None

        self._previous_name = worker.name
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
        # general information
        self._general_information_pane = widgets.Pane(util.Size(150, self.orig_rect.height / 2) - (30, 30),
                                                      selectable=False, color=(150, 150, 150))
        self.add_widget((15, 15), self._general_information_pane, adjust=True)
        self.add_border(self._general_information_pane)

        y = 0
        info_name_lbl = widgets.Label(util.Size(150, 15), text="INFO", text_pos=(43, "center"), font_size=20,
                                      selectable=False)
        self._general_information_pane.add_widget((0, 0), info_name_lbl)
        self._general_information_pane.add_border(info_name_lbl)

        y += 25
        name_name_lbl = widgets.Label(util.Size(60, 10), text="Name: ", text_pos=("west", "center"), selectable=False,
                                      color=(150, 150, 150))
        self._general_information_pane.add_widget((5, y), name_name_lbl)

        self._name_lbl = widgets.MultilineTextBox(util.Size(80, 13))
        self._name_lbl.active_line.set_line_text(self._worker.name)
        self._general_information_pane.add_widget((38, y-2), self._name_lbl)

        y += 15
        speed_name_lbl = widgets.Label(util.Size(60, 10), text="Speed: ", text_pos=("west", "center"), selectable=False,
                                       color=(150, 150, 150))
        self._general_information_pane.add_widget((5, y), speed_name_lbl)

        self._speed_lbl = widgets.Label(util.Size(75, 10),
                                        text=f"{self._previous_speed[0]}, {self._previous_speed[1]}",
                                        text_pos=("west", "center"), selectable=False, color=(150, 150, 150))
        self._general_information_pane.add_widget((45, y), self._speed_lbl)

        y += 15
        max_speed_name_lbl = widgets.Label(util.Size(60, 10), text="Max speed: ", text_pos=("west", "center"),
                                           selectable=False, color=(150, 150, 150))
        self._general_information_pane.add_widget((5, y), max_speed_name_lbl)

        self._max_speed_lbl = widgets.Label(util.Size(75, 10), text=str(self._worker.max_speed),
                                            text_pos=("west", "center"), selectable=False, color=(150, 150, 150))
        self._general_information_pane.add_widget((65, y), self._max_speed_lbl)

        y += 15
        location_name_lbl = widgets.Label(util.Size(60, 10), text="Location: ", text_pos=("west", "center"),
                                          selectable=False, color=(150, 150, 150))
        self._general_information_pane.add_widget((5, y), location_name_lbl)

        self._location_lbl = widgets.Label(util.Size(75, 10),
                                           text=f"{self._worker.orig_rect.left}, {self._worker.orig_rect.right}",
                                           text_pos=("west", "center"), selectable=False, color=(150, 150, 150))
        self._general_information_pane.add_widget((52, y), self._location_lbl)

        y += 15
        wheight_name_lbl = widgets.Label(util.Size(60, 10), text="Wheight: ", text_pos=("west", "center"),
                                         selectable=False, color=(150, 150, 150))
        self._general_information_pane.add_widget((5, y), wheight_name_lbl)

        self._wheight_lbl = widgets.Label(util.Size(75, 10), text=str(self._previous_wheight),
                                          text_pos=("west", "center"), selectable=False, color=(150, 150, 150))
        self._general_information_pane.add_widget((50, y), self._wheight_lbl)

        task_name_lbl = widgets.Label(util.Size(120, 15), text="TASK QUEUE", text_pos=(20, "center"), font_size=20,
                                      selectable=False, color=(150, 150, 150))
        self.add_widget((165, 15), task_name_lbl, adjust=True)
        self.add_border(task_name_lbl)

        # task information
        self._task_information_pane = widgets.ScrollPane(util.Size(150, self.orig_rect.height / 2) - (30, 48),
                                                         selectable=False)
        self.add_widget((165, 33), self._task_information_pane, adjust=True)
        self.add_border(self._task_information_pane)

        # inventory pane
        self._inventory_pane = widgets.ScrollPane(util.Size(300, self.orig_rect.height / 2) - (30, 50),
                                                  color=self.COLOR, selectable=False)
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
        if self._name_lbl.active_line.text != self._worker.name:
            self._worker.name = self._name_lbl.active_line.text
        if self._worker.name != self._previous_name:
            self._previous_name = self._worker.name
            self._name_lbl.active_line.set_line_text(self._previous_name)

    def __check_speed(self):
        if self._worker.speed != self._previous_speed:
            self._previous_speed = round(self._worker.speed.x), round(self._worker.speed.y)
            self._speed_lbl.set_text(f"{self._previous_speed[0]}, {self._previous_speed[1]}", pos=("west", "center"))

    def __check_max_speed(self):
        if self._worker.max_speed != self._previous_max_speed:
            self._previous_max_speed = self._worker.max_speed
            self._max_speed_lbl.set_text(str(self._worker.max_speed), pos=("west", "center"))

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
                task_label = widgets.Label(util.Size(130, 10), text=str(task), text_pos=["west", "center"],
                                           selectable=False)
                self._task_information_pane.add_widget(task_label)
