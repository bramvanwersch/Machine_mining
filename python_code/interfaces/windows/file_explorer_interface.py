import os
from os.path import isfile, join

from interfaces.windows import base_interface
from interfaces import widgets
from utility import constants as con, utilities as util


class OpenFile(base_interface.Window):
    SIZE: util.Size = util.Size(400, 400)

    def __init__(self, pos, sprite_group):
        super().__init__(pos, self.SIZE, sprite_group, title="CHOOSE A FILE", static=False)
        self.file_list = None
        self.__init_widgets()

    def __init_widgets(self):
        files = [f for f in os.listdir(con.SAVE_DIR) if isfile(join(con.SAVE_DIR, f))]
        self.file_list = widgets.ListBox(util.Size(self.rect.width - 50, self.rect.height - 100),
                                         files, color=(173, 94, 29, 150))
        self.add_widget((25, 25), self.file_list)

        new_button = widgets.Button((self.rect.width / 2 - 75, 30), text="New")
        self.add_widget((25, self.rect.height - 100 + 25), new_button)
