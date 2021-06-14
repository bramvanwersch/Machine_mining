#!/usr/bin/env python

import pygame
import re
from typing import Union, Tuple, List, Dict, Any, TYPE_CHECKING
import os
import inspect

from interfaces.windows.base_window import Window

import utility.inventories
import utility.utilities as util
import utility.constants as con
from utility.constants import DEBUG
from utility import game_timing
import interfaces.widgets as widgets
from block_classes.materials import building_materials, environment_materials, ground_materials,\
    machine_materials, materials

if TYPE_CHECKING:
    from board.sprite_groups import CameraAwareLayeredUpdates
    from board.board import Board
    import user


class ConsoleWindow(Window):

    WINDOW_SIZE: util.Size = util.Size(con.SCREEN_SIZE.width, 0.6 * con.SCREEN_SIZE.height)
    WINDOW_POS: Union[Tuple[int, int], List] = (0, 0)

    __input_line: Union["ConsoleLine", None]
    __text_log_label: Union["TextLogLabel", None]
    __log: "TextLog"
    __console: "Console"

    def __init__(
        self,
        sprite_group: "CameraAwareLayeredUpdates",
        board: "Board",
        user_: "user.User"
    ):
        super().__init__(self.WINDOW_POS, self.WINDOW_SIZE, sprite_group, static=False, title="CONSOLE",
                         color=(150, 150, 150))
        self.__input_line = None
        self.__text_log_label = None
        self.__log = TextLog()
        self.__console = Console(board, user_)

        self.__init_widgets()
        self.add_key_event_listener(con.K_TAB, self.__create_tab_information, types=["pressed"])
        self.add_key_event_listener(con.K_UP, self.__set_log_line, values=[-1], types=["unpressed"])
        self.add_key_event_listener(con.K_DOWN, self.__set_log_line, values=[1], types=["unpressed"])

    def __set_log_line(
        self,
        direction: int
    ):
        if direction == 1:
            line = self.__log.line_down()
        elif direction == -1:
            line = self.__log.line_up()
        else:
            raise util.GameException(f"Invalid direction for retrieving Console line {direction}")
        self.__input_line.active_line.set_line_text(line.text)

    def run_starting_script(self):
        self.__console.process_command_line_text("scripts start")

    def __init_widgets(self):
        self.__input_line = ConsoleLine(self.WINDOW_SIZE.width - 10)
        self.add_widget((5, self.WINDOW_SIZE.height - self.__input_line.rect.height - 5), self.__input_line)
        self.add_border(self.__input_line, color=(50, 50, 50))

        self.__text_log_label = TextLogLabel(self.WINDOW_SIZE - (0, self.__input_line.rect.height + 10), self.__log)
        self.add_widget((0, 0), self.__text_log_label)

    def show_window(
        self,
        is_showing: bool
    ):
        super().show_window(is_showing)
        if is_showing is True:
            self.selected_widget = self.__input_line
            self.__input_line.set_selected(True)

    def update(
        self,
        *args: Any
    ):
        """Make sure to process the input line when one is presented when enter is pressed"""
        super().update()
        if self.__input_line.process_line is not None:
            self.add_executed_command_message(self.__input_line.process_line)
            results = self.__console.process_command_line_text(self.__input_line.process_line)
            for message, is_error in results:
                if is_error:
                    [self.add_error_message(m) for m in message.split("\n")]
                else:
                    [self.add_result_message(m) for m in message.split("\n")]
            self.__input_line.process_line = None

    def __create_tab_information(self):
        """Determine tab information that is relevant and append either a list of options or add the information that 
        is shared between all options e.g """
        # get all the text between the start and the cursor
        full_line = self.__input_line.active_line.text
        until_cursor_text = full_line[:self.__input_line.active_line.line_location]
        after_cursor_text = full_line[self.__input_line.active_line.line_location:]
        commands = self.__get_commands_from_line(until_cursor_text)
        possible_commands_dict = self.__console.command_tree
        last_command = commands.pop(-1)
        count = 0
        # moving down the tree for all found commands
        while count < len(commands):
            command = commands[count]
            try:
                if type(possible_commands_dict[command]) == dict:
                    possible_commands_dict = possible_commands_dict[command]
                elif type(possible_commands_dict[command]) == str:
                    loop_loc = possible_commands_dict[command].split(" ")
                    possible_commands_dict = self.__console.command_tree
                    for loc in loop_loc:
                        possible_commands_dict = possible_commands_dict[loc]
                else:
                    return
            except KeyError:
                return
            count += 1
        if last_command == "":
            possible_commands = list(possible_commands_dict.keys())
        # if it ends on a perfect command simply add a space to the line
        elif last_command in possible_commands_dict.keys():
            self.__input_line.active_line.append(" ")
            return
        else:
            possible_commands = [key for key in possible_commands_dict.keys() if key.startswith(last_command)]
        if len(possible_commands) == 1:
            # if line ended on a space
            if len(last_command) == 0:
                self.__input_line.active_line.append(possible_commands[0])
            else:
                self.__input_line.active_line.set_line_text(until_cursor_text[:-len(last_command)]
                                                            + possible_commands[0] + after_cursor_text)
                self.__input_line.active_line.set_line_location(len(until_cursor_text) - len(last_command) +
                                                                len(possible_commands[0]))
        elif len(possible_commands) > 0:
            message = " ".join(possible_commands)
            self.add_tab_possibilities_message(message)
            lpc = str(max(possible_commands, key=len))
            letters = ""
            for letter in lpc:
                letters += letter
                if not all(c.startswith(letters) for c in possible_commands):
                    letters = letters[:-1]
                    break
            if not len(last_command) == 0:
                self.__input_line.active_line.set_line_text(until_cursor_text[:-len(last_command)] + letters +
                                                            after_cursor_text)
                self.__input_line.active_line.set_line_location(len(until_cursor_text) - len(last_command) +
                                                                len(letters))

    def __get_commands_from_line(
        self,
        current_line_text: str
    ) -> List[str]:
        word = ""
        commands = []
        list_multiplier = None
        for letter in current_line_text:
            if letter == " ":
                if word != "":
                    commands.append(word)
                word = ""
            elif letter == "[":
                if word != "":
                    commands.append(word)
                    list_multiplier = word
                elif len(commands) >= 1:
                    list_multiplier = commands[-1]
                word = ""
            elif letter == "]":
                word = ""
                if list_multiplier:
                    list_multiplier = commands[commands.index(list_multiplier) - 1]
                    commands = commands[:commands.index(list_multiplier) + 1]
            elif letter == ",":
                word = ""
                if list_multiplier:
                    commands = commands[:commands.index(list_multiplier) + 1]
                else:
                    commands = []
            else:
                word += letter
        commands.append(word)
        return commands

    def add_error_message(self, text):
        message = "ERROR: "
        self.__log.append_other(Line(text=message + text, color=(163, 28, 23)))

    def add_result_message(self, text):
        self.__log.append_other(Line(text=text, color=(25, 118, 168)))

    def add_tab_possibilities_message(self, text):
        self.__log.append_other(Line(text=text, color=(0, 0, 255), line_type="list"))

    def add_executed_command_message(self, text):
        """Print a command that was just executed in greenn"""
        self.__log.append(Line(text=text, color=(64, 235, 52)))


class ConsoleLine(widgets.MultilineTextBox):
    """The command line where the commands are typed"""

    process_line: Union[str, None]

    def __init__(
        self,
        width: int
    ):
        super().__init__(util.Size(width, con.FONTS[22].get_linesize() + 6), lines=1, font_size=22)
        self.add_key_event_listener(con.K_RETURN, action_function=self.handle_return, types=["pressed"])
        self.remove_key_event_listener(con.K_TAB)
        self.process_line = None

    def handle_return(self):
        self.process_line = self.active_line.text
        self.active_line.set_line_text("")


class TextLogLabel(widgets.Label):
    """The area above the command line containing the replies of the console"""
    # TODO use a scrollpane in order to better see the full history

    __log: "TextLog"

    def __init__(
        self,
        size: Union[util.Size, Tuple[int, int], List[int]],
        text_log: "TextLog",
        color: Union[Tuple[int, int, int], List[int]] = (150, 150, 150),
        **kwargs
    ):
        super().__init__(size, color=color, selectable=False, **kwargs)
        self.__log = text_log

    def wupdate(self):
        super().wupdate()
        if self.__log.changed:
            image = self.__create_log_image()
            self.set_image(image, (0, 0))
            self.__log.changed = False

    def __create_log_image(self):
        """Create the label image to be displayed only called when the log is changed"""
        image = pygame.Surface(self.rect.size)
        image.fill((150, 150, 150))
        prev_line_heigth = 0
        for i, line in enumerate(iter(self.__log)):
            if self.rect.height - prev_line_heigth < 0:
                break
            text = line.render()
            prev_line_heigth += text.get_size()[1]
            image.blit(text, (5, self.rect.height - prev_line_heigth))
        return image.convert()


class TextLog:
    """Log for tracking the commands typed by the user, warnings and confirmation messages. Commands typed by the user
    are tracked separatelly from the others in order to allow the for finding back these commands

    The user log and warning/confirmation log are dictionaries with indexes as keys, together one full log is formed
    """

    __user_log: Dict
    __warning_and_confirmation_log: Dict
    __user_log_location: int
    changed: bool

    def __init__(self):
        self.__user_log = {}  # the log with user issued commands
        self.__warning_and_confirmation_log = {}  # all other text that is commited to the log
        self.__user_log_location = 0
        self.changed = False

    def __getitem__(self, key):
        return self.__user_log[len(self.__user_log) - key]

    def __len__(self):
        return len(self.__user_log)

    def __iter__(self):
        """return all the user and warning messages in one itter sorted based on the insertion line"""
        combined_keys = list(self.__user_log.keys()) + list(self.__warning_and_confirmation_log.keys())
        combined_keys.sort()
        combined = {**self.__user_log, **self.__warning_and_confirmation_log}
        sorted_lines = reversed(list(combined[key] for key in combined_keys))
        return iter(sorted_lines)

    def append(
        self,
        line: "Line"
    ):
        """Add a line to the user log"""
        self.__user_log[len(self.__user_log) + len(self.__warning_and_confirmation_log)] = line
        self.changed = True
        # always place the cursor at the last line to act like linux instead of windows command line
        self.__user_log_location = 0

    def append_other(
        self,
        line: "Line"
    ):
        """Add a line to the warning/confirmation log"""
        self.__warning_and_confirmation_log[len(self.__user_log) + len(self.__warning_and_confirmation_log)] = line
        self.changed = True

    def line_up(self) -> "Line":
        """Move the line location one line up if possible and return a copy of the the line moved to"""
        if len(self.__user_log) == 0:
            return Line()
        if self.__user_log_location < len(self.__user_log):
            self.__user_log_location += 1
        return list(self.__user_log.values())[-self.__user_log_location].copy()

    def line_down(self) -> "Line":
        """Move the line location one line down if possible and return a copy of the the line moved to"""
        if self.__user_log_location > 0:
            self.__user_log_location -= 1
        if self.__user_log_location == 0:
            return Line()
        return list(self.__user_log.values())[-self.__user_log_location].copy()


class Line:
    """TextLog lines that are easier to keep track of and have methods for console accurate rendering"""

    MAX_LINE_LENGTH = con.SCREEN_SIZE.width
    BACKGROUND_COLOR = (150, 150, 150)

    text: str
    __color: Union[Tuple[int, int, int], List[int]]
    __line_location: int
    __rendered_str: Union[None, pygame.Surface]
    __font: pygame.font.Font
    __line_type: str

    def __init__(
        self,
        text: str = "",
        color: Union[Tuple[int, int, int], List[int]] = (0, 255, 0),
        font: int = 22,
        line_type: str = "normal"
    ):
        self.text = text
        self.__color = color
        self.__line_location = len(self.text)
        self.__rendered_str = None
        self.__font = con.FONTS[font]
        self.__line_type = line_type

    def __str__(self):
        return self.text

    def render(self) -> pygame.Surface:
        """Render the string of this line, either return the rendered version of it was rendered before or actually
        render the string"""
        if self.__rendered_str:
            return self.__rendered_str
        else:
            return self.__render_string()

    def __render_string(self) -> pygame.Surface:
        """Render the string based on the __line_type, the line type determines if a list like format is rendered or
        the normal line with enters if neccesairy"""
        if self.__line_type == "normal":
            text = self.__render_normal_line()
        elif self.__line_type == "list":
            text = self.__render_list_line()
        else:
            raise util.GameException(f"Unsupported line_type {self.__line_type}")
        surf = pygame.Surface((con.SCREEN_SIZE.width + 2, len(text) * self.__font.size("k")[1] + 2))

        surf.fill(self.BACKGROUND_COLOR)
        for index, line in enumerate(text):
            rt = self.__font.render(line, True, self.__color)
            surf.blit(rt, (0, rt.get_size()[1] * index))
        return surf

    def __render_normal_line(self) -> List[str]:
        """Render a 'normal' text line that can be longer then the given MAX_LINE_LENGTH. In that the case the line
        is split up in multiple lines using the words to break."""
        if self.__font.size(self.text)[0] > self.MAX_LINE_LENGTH:
            words = self.text.split(" ")
            lines = [""]
            line_length = 0
            for word in words:
                word_size = self.__font.size(word + " ")[0]
                if line_length + word_size < self.MAX_LINE_LENGTH:
                    lines[len(lines) - 1] += word + " "
                    line_length += word_size
                else:
                    line_length = self.__font.size(word)
                    lines.append(word)
            return lines
        else:
            return [self.text]

    def __render_list_line(self) -> List[str]:
        """Render a line that represents a list of values that are seperated on spaces. In this case the line should
        be shown in sutch a way that the list elements allign under one another if there are multiple lines needed"""
        words = self.text.split(" ")
        longest_word = max(self.__font.size(word + "   ")[0] for word in words)
        lines = [""]
        line_length = 0
        for word in words:
            word_size = self.__font.size(word)[0]
            while word_size < longest_word:
                word += " "
                word_size = self.__font.size(word)[0]
            if line_length + word_size < self.MAX_LINE_LENGTH:
                lines[len(lines) - 1] += word
                line_length += word_size
            else:
                line_length = word_size
                lines.append(word)
        return lines

    def __len__(self):
        return len(self.text)

    def copy(self) -> "Line":
        """Return a copy of this line"""
        return Line(text=self.text, color=self.__color, line_type=self.__line_type)


class Console:
    """Class that allows for using commands in order to manipulate values while the game is running
    Quick guide:
        - Every command is build up in a simple way. Name of main command, a series of names indicating where to find
         the value. A potential value to set the located value too.
        - tab can be pressed to see the allowed commands given a certain type point.
        - square brackets ([]) can be used in order to save typing by allowing some sort of multiplication e.g print
         debug [FPS, NO_LIGHTING] -means-> print debug FPS and print debug NO_LIGTHING, this works in a nested fashion 
         as well
        - brackets and ; are used in order to set lists in order to not interfer with the square bracket syntax
    """
    command_tree: Dict[str, Any]
    __board: "Board"
    __user: "user.User"

    def __init__(
        self,
        board: "Board",
        user_: "user.User"
    ):
        self.command_tree = {}
        self.__board = board
        self.__user = user_
        self.__innitialise_command_tree()

    def __innitialise_command_tree(self):
        self.command_tree["print"] = self.__create_print_tree()
        self.command_tree["scripts"] = self.__create_script_tree()
        self.command_tree["set"] = self.__create_set_tree()
        self.command_tree["add_item"] = self.__create_add_item_tree()

    def __create_print_tree(self) -> Dict[str, Any]:
        tree = dict()
        tree["debug"] = self.__create_attribute_tree(DEBUG, "printables")
        tree["workers"] = {f"worker_{index + 1}": self.__create_attribute_tree(worker, "printables")
                           for index, worker in enumerate(self.__user.workers)}
        tree["buildings"] = \
            {f"buildling_{index + 1}({buidling.name()[:3]})": self.__create_attribute_tree(buidling, "printables")
             for index, buidling in enumerate(self.__user.board.buildings.values())}
        tree["timings"] = False
        return tree

    def __create_set_tree(self) -> Dict[str, Any]:
        tree = dict()
        tree["debug"] = self.__create_attribute_tree(DEBUG, "setables")
        tree["workers"] = {f"worker_{index + 1}": self.__create_attribute_tree(worker, "setables")
                           for index, worker in enumerate(self.__user.workers)}
        tree["buildings"] = \
            {f"buildling_{index + 1}({buidling.name()[:3]})": self.__create_attribute_tree(buidling, "setables")
             for index, buidling in enumerate(self.__user.board.buildings.values())}
        return tree

    def __create_script_tree(self) -> Dict[str, Any]:
        """Scrips are read from a file that contain a name, ':' and then a oneliner to be executed"""
        partsfile = os.path.join(con.DATA_DIR, "scripts.txt")
        f = open(partsfile, "r")
        lines = f.readlines()
        f.close()
        tree = {}
        for line in lines:
            name, command_line = line.split(":")
            tree[name] = command_line
        return tree

    def __create_add_item_tree(self) -> Dict[str, Any]:
        tree = dict()
        for module, module_name in [(building_materials, "building_materials"),
                                    (environment_materials, "environment_materials"),
                                    (ground_materials, "ground_materials"),
                                    (machine_materials, "machine_materials")]:
            tree[module_name] = {}
            for cls_name, cls in inspect.getmembers(module, inspect.isclass):
                if inspect.isclass(cls) and issubclass(cls, materials.BaseMaterial) and not util.is_abstract(cls):
                    tree[module_name][cls_name] = cls
        return tree

    def __create_attribute_tree(
        self,
        target: util.ConsoleReadable,
        function: str
    ) -> Dict[str, Any]:
        """Starting from a ConsoleReadable collect all relevant values at a certain provided function and check if
        those are console readable. If that os the case recursively continue"""
        tree = {}
        target_function = getattr(target, function)
        attributes = target_function()
        for str_atr in attributes:
            new_target = getattr(target, str_atr)
            if isinstance(new_target, util.ConsoleReadable):
                tree[str_atr] = self.__create_attribute_tree(new_target, function)
            else:
                tree[str_atr] = False
        return tree

    def process_command_line_text(
        self,
        text: str
    ) -> List[Tuple[str, bool]]:
        """Process a string that presumably represents a valid command"""
        results = []
        try:
            commands_list = self.__text_to_commands(text)
        except ValueError as e:
            return [(str(e), True)]
        for arguments in commands_list:
            arguments = arguments.strip().split(" ")
            try:
                if arguments[0] == "print":
                    results.append(self.__process_arguments(arguments))
                elif arguments[0] == "scripts":
                    # special case
                    results.extend(self._process_script_call(arguments))
                elif arguments[0] == "set":
                    results.append(self.__process_arguments(arguments))
                elif arguments[0] == "add_item":
                    results.append(self.__process_add_item(arguments))
                else:
                    results.append(("{} is not a valid command. Choose one of the following: {}."
                                    .format(arguments[0], ", ".join(self.command_tree.keys())), True))
            except (IndexError, KeyError):
                results.append((f"Not enough arguments supplied for the {arguments[0]} command.", True))
        return results

    def __text_to_commands(self, text):
        """Extract all commands in a given text by writing out all the lists into lines of commands conveyed by those
        lists"""
        text = text.strip()
        lists = {}
        if text.count("]") != text.count("["):
            raise ValueError("Uneven amount of open and closing brackets.")
        # first get all lists within lists
        count = 0
        while True:
            matches = re.findall("\[[^\[]+?\]", text)  # noqa --> because fuck off
            if matches:
                for match in matches:
                    text = text.replace(match, ",list" + str(count))
                    lists["list" + str(count)] = match
                    count += 1
            else:
                break
        # then get all commands conveyed by those lists
        return self.__get_command_list(text, lists)

    def __get_command_list(
        self,
        text: str,
        lists: Dict
    ):
        text = text.split(",")
        fl = []
        for i in range(len(text)):
            if text[i] in lists:
                text[i] = self.__get_command_list(lists[text[i]][1:-1], lists)
                for val in text[i]:
                    combined = text[i - 1].strip() + " " + val.strip()
                    fl.append(combined)
                    # remove the shorter version from the final_list
                    if text[i-1] in fl:
                        fl.remove(text[i-1])
            else:
                fl.append(text[i])
        return fl

    def __process_arguments(
        self,
        arguments: List[str]
    ) -> Tuple[str, bool]:
        start_argument_index = 1
        check_dictionary = self.command_tree[arguments[0]][arguments[1]]
        if arguments[1] == "debug":
            target = DEBUG
        elif arguments[1] == "workers":
            target = self.__user.workers[int(arguments[2].split("_")[1]) - 1]
            start_argument_index = 2
            check_dictionary = check_dictionary[arguments[2]]
        elif arguments[1] == "buildings":
            target = list(self.__user.board.buildings.values())[int(arguments[2].split("_")[1].split("(")[0]) - 1]
            start_argument_index = 2
            check_dictionary = check_dictionary[arguments[2]]
        elif arguments[1] == "timings":
            return game_timing.TIMINGS.get_time_summary()[:-1], False
        else:
            raise util.GameException(f"Unexpected value to print from; {arguments[1]}")

        return getattr(self, f"_process_{arguments[0]}")(arguments, start_argument_index, check_dictionary, target)

    def __process_add_item(self, arguments):
        if len(arguments) < 4:
            return f"Expected 3 arguments to add item only got {len(arguments)}", True
        material = getattr(globals()[arguments[1]], arguments[2])()
        try:
            amount = int(arguments[3])
        except ValueError:
            return "Expected the amount argument to be a valid integer", True
        if amount <= 0:
            return "The amount must be bigger then 0", True
        item = utility.inventories.Item(material, amount)
        self.__board.add_to_terminal_inventory(item)
        return f"Added {str(item)} to the terminal", False

    def _process_print(
        self,
        arguments: List[str],
        start_argument_index: int,
        check_dictionary: Dict,
        target: Any
    ) -> Tuple[str, bool]:
        """Process a print call by the user"""
        index = start_argument_index + 1
        # walk down the tree for all the arguments
        while index < len(arguments):
            if not isinstance(check_dictionary, dict) or arguments[index] not in check_dictionary:
                return "Value {} cannot be accessed or is not allowed to be accessed".\
                           format(".".join(arguments[start_argument_index:])), True
            else:
                check_dictionary = check_dictionary[arguments[index]]
            target = getattr(target, arguments[index])
            index += 1
        return "Value of {} is {}".format(".".join(arguments[start_argument_index:]), str(target)), False

    def _process_script_call(
        self,
        arguments: List[str]
    ) -> List[Tuple[str, bool]]:
        """Process a script call by taking the name and taking the provided line"""
        command_line = self.command_tree["scripts"][arguments[1]]
        results = self.process_command_line_text(command_line)
        return results

    def _process_set(
        self,
        arguments: List[str],
        start_argument_index: int,
        check_dictionary: Dict,
        target: Any
    ) -> Tuple[str, bool]:
        index = start_argument_index + 1
        # walk down the tree for all the arguments
        if len(arguments) < 3:
            return "Expected at least 3 arguments for a set call.", True
        while index < len(arguments) - 2:
            if not isinstance(check_dictionary, dict) or arguments[index] not in check_dictionary:
                return "Value {} cannot be accessed or is not allowed to be accessed". \
                           format(".".join(arguments[start_argument_index:])), True
            else:
                check_dictionary = check_dictionary[arguments[index]]
            target = getattr(target, arguments[index])
            index += 1
        new_value = arguments[-1]
        target_attribute = arguments[-2]
        if not hasattr(target, target_attribute):
            return "Value {} cannot be accessed or is not allowed to be accessed". \
                       format(".".join(arguments[start_argument_index:])), True
        current_value = getattr(target, target_attribute)
        try:
            proper_type_new_value = self.__convert_to_type(new_value, current_value)
        except ValueError as e:
            return str(e), True
        setattr(target, target_attribute, proper_type_new_value)
        return "The value {} = {} is set to {}".format('.'.join(arguments[start_argument_index:-1]), current_value,
                                                       str(proper_type_new_value)), False

    def __convert_to_type(
        self,
        string_to_convert: str,
        orig_value: Any
    ) -> Any:
        try:
            if isinstance(orig_value, str):
                return string_to_convert
            elif isinstance(orig_value, bool):
                return self.__string_to_bool(string_to_convert)
            elif isinstance(orig_value, int):
                return int(string_to_convert)
            elif isinstance(orig_value, float):
                return float(string_to_convert)
            elif isinstance(orig_value, list) or isinstance(orig_value, tuple):
                return self.__string_to_list(string_to_convert, orig_value)
            elif isinstance(orig_value, pygame.math.Vector2):
                values = self.__string_to_list(string_to_convert, [orig_value[0], orig_value[1]])
                return pygame.math.Vector2(*values)
            elif isinstance(orig_value, pygame.Rect):
                values = self.__string_to_list(string_to_convert, [orig_value[0], orig_value[1], orig_value[2],
                                                                   orig_value[3]])
                return pygame.Rect(*values)
            elif con.DEBUG.WARNINGS:
                print("No case for value of type {}".format(type(orig_value)))
        except ValueError as e:
            raise e
        raise ValueError("cannot convert to type_s {}. No known method.".format(type(orig_value)))

    def __string_to_bool(
        self,
        value: str
    ) -> bool:
        value = value.lower()
        if value == "true" or value == "t":
            return True
        elif value == "false" or value == "f":
            return False
        else:
            raise ValueError("expected a boolean to be either: true, t, false or f (case insensitive)".format(value))

    def __string_to_list(
        self,
        value: str,
        orig_list: Union[List, Tuple]
    ) -> List[Any]:
        """
        only a one dimensional list is expected
        """
        if "(" not in value:
            raise ValueError("expected a list to be of form (val1;val2;..)")
        value = value.replace("(", "").replace(")", "")
        the_list = [val.strip() for val in value.split(";")]
        if len(orig_list) != len(the_list):
            raise ValueError("list is of wrong length. Expected a list of lenght {}.".format(len(orig_list)))
        for index, value in enumerate(orig_list):
            val_type = type(value)
            try:
                user_value = the_list[index]
                if val_type != str:
                    user_value = user_value.strip()
                correct_typed_value = self.__convert_to_type(user_value, value)
                the_list[index] = correct_typed_value
            except ValueError:
                raise ValueError("expected value of type {} at index {}. Cannot convert {} to {}."
                                 .format(val_type, index, the_list[index], val_type))
        return the_list
