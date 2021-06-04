import os
from os.path import isfile, join
from typing import Tuple, Union, List

from interfaces.windows import base_interface
from interfaces import widgets
from utility import constants as con, utilities as util


class OpenFile(base_interface.Window):
    SIZE: util.Size = util.Size(400, 400)
    COLOR: Union[Tuple[int, int, int, int], Tuple[int, int, int], List[int]] = (173, 94, 29)

    def __init__(self, pos, sprite_group):
        super().__init__(pos, self.SIZE, sprite_group, title="CHOOSE A FILE", static=False, color=self.COLOR)
        self.file_list = None
        self.__init_widgets()

    def __init_widgets(self):
        save_label = widgets.Label(util.Size(200, 30), text="Choose a save file:", font_size=25, color=(0, 0, 0, 0),
                                   selectable=False)
        self.add_widget((int(self.rect.width / 2 - save_label.rect.width / 2), 5), save_label)

        self.file_list = widgets.ListBox(util.Size(self.rect.width - 50, self.rect.height - 100),  color=self.COLOR)
        self.add_widget((25, 45), self.file_list)
        self.add_border(self.file_list)

        new_button = widgets.Button(util.Size(self.file_list.rect.width, 25), text="New...", font_size=25,
                                    color=self.COLOR)
        new_button.add_key_event_listener(con.MOUSEBUTTONUP, self.create_new_file_window)

        self.file_list.add_widget(new_button)

        for file in os.listdir(con.SAVE_DIR):
            if isfile(join(con.SAVE_DIR, file)):
                file_button = widgets.Button(util.Size(self.file_list.rect.width, 25), text=file, font_size=25,
                                             color=self.COLOR)
                self.file_list.add_widget(file_button)

    def create_new_file_window(self):
        from interfaces.managers import game_window_manager
        popup = CreateNewFile(self.rect.center, self.groups()[0])
        game_window_manager.add(popup)


class CreateNewFile(base_interface.Window):
    SIZE: util.Size = util.Size(200, 200)
    COLOR: Union[Tuple[int, int, int, int], Tuple[int, int, int], List[int]] = (173, 94, 29)

    def __init__(self, pos, sprite_group):
        super().__init__(pos, self.SIZE, sprite_group, title="FILE NAME", static=False, color=self.COLOR)
        self.__init_widgets()

    def __init_widgets(self):
        input_line = widgets.MultilineTextBox(util.Size(150, 25), lines=1)
        self.add_widget((25, 5), input_line)