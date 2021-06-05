import os
from os.path import isfile, join
from typing import Tuple, Union, List
from abc import ABC

from interfaces.windows import base_interface
from interfaces import widgets
from utility import constants as con, utilities as util
import scenes


class OpenFile(base_interface.Window):
    SIZE: util.Size = util.Size(350, 400)
    COLOR: Union[Tuple[int, int, int, int], Tuple[int, int, int], List[int]] = (173, 94, 29)

    def __init__(self, pos, sprite_group):
        super().__init__(pos, self.SIZE, sprite_group, title="CHOOSE A FILE", static=False, color=self.COLOR,
                         movable=False, top_window=True)
        self.file_list = None
        self.__init_widgets()
        self.__create_name_popup = None
        self.__overwrite_file_popup = None

    def update(self, *args):
        super().update(*args)
        self.check_popups()

    def check_popups(self):
        if self.__create_name_popup is not None and not self.__create_name_popup.is_showing():
            response = self.__create_name_popup.response
            self.__create_name_popup = None
            if response is not False:
                self.save_game(response)
        if self.__overwrite_file_popup is not None and not self.__overwrite_file_popup.is_showing():
            response = self.__overwrite_file_popup.response
            self.__overwrite_file_popup = None
            if response is not False:
                self.save_game(response)

    def save_game(self, file_name):
        # since dots are not allowed to be in file names this should be save
        file_name = file_name.replace(".save", "")
        scenes.scenes["Game"].save(file_name)
        self._close_window()

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
            if isfile(join(con.SAVE_DIR, file) and file.endswith(".save")):
                file_button = widgets.Button(util.Size(self.file_list.rect.width, 25), text=file, font_size=25,
                                             color=self.COLOR)
                file_button.add_key_event_listener(1, self.confirm_overwrite_window, values=[file], types=["unpressed"])
                self.file_list.add_widget(file_button)

    def create_new_file_window(self):
        from interfaces.managers import game_window_manager
        self.__create_name_popup = GiveNamePopup(self.rect.center, self.groups()[0])
        game_window_manager.add(self.__create_name_popup)

    def confirm_overwrite_window(self, file_name):
        from interfaces.managers import game_window_manager
        self.__overwrite_file_popup = ConfirmPopup(self.rect.center, f"WARNING: '{file_name}'\n will be overwritten",
                                                   file_name, self.groups()[0])
        game_window_manager.add(self.__overwrite_file_popup)


class Popup(base_interface.Window, ABC):
    SIZE: util.Size = util.Size(200, 100)
    COLOR: Union[Tuple[int, int, int, int], Tuple[int, int, int], List[int]] = (150, 150, 150)

    def __init__(self, pos, sprite_group, **kwargs):
        super().__init__(pos, self.SIZE, sprite_group, static=False, color=self.COLOR, movable=False, top_window=True,
                         **kwargs)
        self.response = False


class ConfirmPopup(Popup):
    def __init__(self, pos, message, true_response, sprite_group, **kwargs):
        super().__init__(pos, sprite_group, **kwargs)
        self.__true_response = true_response
        self.__init_widgets(message)

    def __init_widgets(self, message):
        for index, line in enumerate(message.split("\n")):
            message_lbl = widgets.Label(util.Size(self.rect.width - 20, 25), color=self.COLOR, text=line, font_size=18)
            self.add_widget((10, index * 18 + 5), message_lbl)

        oke_button = widgets.Button(util.Size(self.rect.width / 2 - 25, 25), text="OK", font_size=25)
        oke_button.add_key_event_listener(1, self.__set_response_true, types=["unpressed"])
        self.add_widget((20, 60), oke_button)

        cancel_button = widgets.Button(util.Size(self.rect.width / 2 - 25, 25), text="CANCEL", font_size=25)
        cancel_button.add_key_event_listener(1, self._close_window, types=["unpressed"])
        self.add_widget((self.rect.width - cancel_button.rect.width - 20, 60), cancel_button)

    def __set_response_true(self):
        self.response = self.__true_response
        self._close_window()


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
        if os.path.exists(f"{con.SAVE_DIR}{os.sep}{name}.save"):
            self._incorect_lbl.set_text(f"File '{name}' already exists", font_size=20, color=(255, 0, 0))
            return False
        return True
