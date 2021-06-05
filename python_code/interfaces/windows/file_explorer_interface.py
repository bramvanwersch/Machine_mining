import os
from os.path import isfile, join
from typing import Tuple, Union, List
from abc import ABC

from interfaces.windows import base_interface
from interfaces import widgets
from utility import constants as con, utilities as util
import scenes


class OpenFile(base_interface.TopWindow):
    SIZE: util.Size = util.Size(400, 400)
    COLOR: Union[Tuple[int, int, int, int], Tuple[int, int, int], List[int]] = (173, 94, 29)

    def __init__(self, pos, sprite_group):
        super().__init__(pos, self.SIZE, sprite_group, title="CHOOSE A FILE", static=False, color=self.COLOR)
        self.file_list = None
        self.__init_widgets()
        self.__create_name_popup = None

    def update(self, *args):
        super().update(*args)
        self.check_popups()

    def check_popups(self):
        if self.__create_name_popup is not None and not self.__create_name_popup.is_showing():
            response = self.__create_name_popup.response
            print(response)
            self.__create_name_popup = None
            if response is not False:
                scenes.scenes["Game"].save(response)

    def __init_widgets(self):
        save_label = widgets.Label(util.Size(200, 30), text="Choose a save file:", font_size=25, color=(0, 0, 0, 0),
                                   selectable=False)
        self.add_widget((int(self.rect.width / 2 - save_label.rect.width / 2), 5), save_label)

        self.file_list = widgets.ListBox(util.Size(self.rect.width - 50, self.rect.height - 100),  color=self.COLOR)
        self.add_widget(("center", 45), self.file_list)
        self.add_border(self.file_list)

        new_button = widgets.Button(util.Size(self.file_list.rect.width, 25), text="New...", font_size=25,
                                    color=self.COLOR)
        new_button.add_key_event_listener(1, self.create_new_file_window, types=["unpressed"])

        self.file_list.add_widget(new_button)

        for file in os.listdir(con.SAVE_DIR):
            if isfile(join(con.SAVE_DIR, file)):
                file_button = widgets.Button(util.Size(self.file_list.rect.width, 25), text=file, font_size=25,
                                             color=self.COLOR)
                self.file_list.add_widget(file_button)

    def create_new_file_window(self):
        from interfaces.managers import game_window_manager
        self.__create_name_popup = GiveNamePopup(self.rect.center, self.groups()[0])
        game_window_manager.add(self.__create_name_popup)


class Popup(base_interface.Window, ABC):
    SIZE: util.Size = util.Size(200, 100)
    COLOR: Union[Tuple[int, int, int, int], Tuple[int, int, int], List[int]] = (150, 150, 150)

    def __init__(self, pos, sprite_group, **kwargs):
        super().__init__(pos, self.SIZE, sprite_group, static=False, color=self.COLOR, movable=False, **kwargs)
        self.response = False


class GiveNamePopup(Popup):
    COLOR: Union[Tuple[int, int, int, int], Tuple[int, int, int], List[int]] = (150, 150, 150)

    def __init__(self, pos, sprite_group):
        super().__init__(pos, sprite_group, title="FILE NAME")
        self._incorect_lbl = None
        self._input_line = None
        self.__init_widgets()

    def __init_widgets(self):
        self.input_line = widgets.MultilineTextBox(util.Size(150, 25), lines=1, font_size=25)
        self.add_widget((25, 5), self.input_line)

        self._incorect_lbl = widgets.Label(util.Size(self.rect.width - 50, 25), color=self.COLOR)
        self.add_widget((25, 35), self._incorect_lbl)

        oke_button = widgets.Button(util.Size(self.rect.width / 2 - 25, 25), text="OK", font_size=25)
        oke_button.add_key_event_listener(1, self._set_name_response, types=["unpressed"])
        self.add_widget((20, 60), oke_button)

        cancel_button = widgets.Button(util.Size(self.rect.width / 2 - 25, 25), text="CANCEL", font_size=25)
        cancel_button.add_key_event_listener(1, self._close_window, types=["unpressed"])
        self.add_widget((self.rect.width - cancel_button.rect.width - 20, 60), cancel_button)

    def _set_name_response(self):
        if self.__check_valid_name() is True:
            name = self.input_line.active_line.get_text()
            self.response = name
            self._close_window()

    def __check_valid_name(self):
        name = self.input_line.active_line.get_text()
        for character in name:
            if character not in con.ALLOWED_FILE_CHARACTERS:
                self._incorect_lbl.set_text(f"Invalid character: '{character}'", font_size=20, color=(255, 0, 0))
                return False
        return True
