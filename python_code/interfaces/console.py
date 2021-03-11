#!/usr/bin/env python

import pygame
import re
from typing import Union, Tuple, List, Dict, Any
import os

from interfaces.base_interface import Window
import utility.utilities as util
import utility.constants as con
from utility.constants import DEBUG
import interfaces.widgets as widgets


class ConsoleWindow(Window):

    WINDOW_SIZE: util.Size = util.Size(con.SCREEN_SIZE.width, 0.6 * con.SCREEN_SIZE.height)
    WINDOW_POS: Union[Tuple[int, int], List] = (0, 0)

    __input_line: Union["ConsoleLine", None]
    __text_log_label: Union["TextLogLabel", None]
    __log: "TextLog"
    __console: "Console"

    def __init__(self, sprite_group):
        super().__init__(self.WINDOW_POS, self.WINDOW_SIZE, sprite_group, static=False, title="CONSOLE")
        self.__input_line = None
        self.__text_log_label = None
        self.__log = TextLog()
        self.__console = Console()

        self.__init_widgets()
        self.add_key_event_listener(con.K_TAB, self.__create_tab_information, values=[self.__input_line],
                                    types=["pressed"])

    def __init_widgets(self):
        self.__input_line = ConsoleLine(self.WINDOW_SIZE.width)
        self.add_widget((0, self.WINDOW_SIZE.height - self.__input_line.rect.height), self.__input_line)
        self.__text_log_label = TextLogLabel(self.WINDOW_SIZE - (0, self.__input_line.rect.height), self.__log)
        self.add_widget((0, 0), self.__text_log_label)

    def update(self, *args):
        super().update()
        if self.__input_line.process_line is not None:
            self.add_executed_command_message(self.__input_line.process_line)
            message, is_error = self.__console.process_command_line_text(self.__input_line.process_line)
            if is_error:
                [self.add_error_message(m) for m in message.split("\n")]
            else:
                [self.add_conformation_message(m) for m in message.split("\n")]
            self.__input_line.process_line = None

    def __create_tab_information(self, current_line: widgets.MultilineTextBox):
        current_line_text = current_line.get_text().replace("\n", "")
        commands = self.__get_commands_from_line(current_line_text)
        possible_commands_dict = self.__console.command_tree
        last_command = commands.pop(-1)
        count = 0
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
            current_line.add_text_at_line(0, " ")
            return
        else:
            possible_commands = [key for key in possible_commands_dict.keys() if key.startswith(last_command)]
        if len(possible_commands) == 1:
            if len(last_command) == 0:
                current_line.set_text_at_line(0, current_line_text + possible_commands[0])
            else:
                current_line.set_text_at_line(0, current_line_text[:-len(last_command)] + possible_commands[0])
        elif len(possible_commands) > 0:
            mcl = max(len(command) for command in possible_commands)
            m1 = "{:<" + str(mcl + 2) + "}"
            m2 = m1 * len(possible_commands)
            message = m2.format(*possible_commands)
            self.__log.append_warning(Line(text=message, color=(0, 0, 255)))
            lpc = str(max(possible_commands, key=len))
            letters = ""
            for letter in lpc:
                letters += letter
                if not all(c.startswith(letters) for c in possible_commands):
                    letters = letters[:-1]
                    break
            if not len(last_command) == 0:
                current_line.set_text_at_line(0, current_line_text[:-len(last_command)] + letters)

    def __get_commands_from_line(self, current_line_text: str):
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
        self.__log.append_warning(Line(text=message + text, color=(163, 28, 23)))

    def add_conformation_message(self, text):
        self.__log.append_warning(Line(text=text, color=(25, 118, 168)))

    def add_executed_command_message(self, text):
        self.__log.append(Line(text=text, color=(64, 235, 52)))


class ConsoleLine(widgets.MultilineTextBox):
    def __init__(self, width):
        super().__init__(util.Size(width, con.FONTS[22].get_linesize() + 6), lines=1, font_size=22)
        self.add_key_event_listener(con.K_RETURN, action_function=self.handle_return, types=["pressed"])
        self.remove_key_event_listener(con.K_TAB)
        self.process_line = None

    def handle_return(self):
        self.process_line = self.get_text().replace("\n", "")
        self.delete_text()


class TextLogLabel(widgets.Label):
    def __init__(self, size, text_log, color=(150, 150, 150), **kwargs):
        super().__init__(size, color=color, selectable=False, **kwargs)
        self.__log = text_log

    def wupdate(self):
        super().wupdate()
        if self.__log.changed:
            image = self.__create_log_image()
            self.set_image(image, (0, 0))
            self.__log.changed = False

    def __create_log_image(self):
        image = pygame.Surface(self.rect.size)
        image.fill((150, 150, 150))
        prev_line_heigth = 0
        for i, line in enumerate(iter(self.__log)):
            if self.rect.height - prev_line_heigth < 0:
                break
            text = line.render_str()
            prev_line_heigth += text.get_size()[1]
            image.blit(text, (5, self.rect.height - prev_line_heigth))
        return image.convert()


class TextLog:
    def __init__(self):
        self.user_log = {}
        self.warning_log = {}
        self.user_log_location = 0
        self.changed = False

    def __getitem__(self, key):
        return self.user_log[len(self.user_log) - key]

    def __len__(self):
        return len(self.user_log)

    def __iter__(self):
        # return all the user and warning messages in one itter sorted based on the insertion line
        combined_keys = list(self.user_log.keys()) + list(self.warning_log.keys())
        combined_keys.sort()
        combined = {**self.user_log, **self.warning_log}
        sorted_lines = reversed(list(combined[key] for key in combined_keys))
        return iter(sorted_lines)

    def append(self, line):
        self.user_log[len(self.user_log) + len(self.warning_log)] = line
        self.changed = True

    def append_warning(self, line):
        self.warning_log[len(self.user_log) + len(self.warning_log)] = line
        self.changed = True

    def line_up(self):
        if len(self.user_log) == 0:
            return Line()
        if self.user_log_location < len(self.user_log):
            self.user_log_location += 1
        return list(self.user_log.values())[-self.user_log_location].copy()

    def line_down(self):
        if self.user_log_location > 0:
            self.user_log_location -= 1
        if self.user_log_location == 0:
            return Line()
        return list(self.user_log.values())[-self.user_log_location].copy()


class Line:
    MAX_LINE_SIZE = 155
    BACKGROUND_COLOR = (150, 150, 150)

    def __init__(self, text="", color=(0, 255, 0), font=22):
        self.color = color
        self.text = text
        self.line_location = len(self.text)
        self.rendered_str = None
        self.font = con.FONTS[font]

    def __str__(self):
        return self.text

    def render_str(self):
        if self.rendered_str:
            return self.rendered_str
        else:
            return self.__render_string()

    def __render_string(self):
        # if line is bigger then max of screen seperate the words and put them on separate lines
        size = util.Size(con.SCREEN_SIZE.width, 0)
        line_heigth = self.font.size("k")[1]
        if len(self.text) > self.MAX_LINE_SIZE:
            words = self.text.split(" ")
            text = [""]
            line_length = 0
            for word in words:
                if line_length + len(word) < self.MAX_LINE_SIZE:
                    text[len(text) - 1] += word + " "
                    line_length += len(word) + 1
                else:
                    s = self.font.size(text[len(text) - 1])
                    size.height += line_heigth
                    line_length = 0
                    text.append("")
            size.height += line_heigth
        else:
            text = [self.text]
            size = util.Size(*self.font.size(self.text))
        surf = pygame.Surface((size.width + 2, size.height + 2))

        surf.fill(self.BACKGROUND_COLOR)
        for index, line in enumerate(text):
            rt = self.font.render(line, True, self.color)
            surf.blit(rt, (0, rt.get_size()[1] * index))
        return surf

    def __len__(self):
        return len(self.text)

    def copy(self):
        return Line(text=self.text, color=self.color)


class Console:
    def __init__(self):
        self.command_tree = {}
        self.__innitialise_command_tree()

    def __innitialise_command_tree(self):
        self.command_tree["print"] = self.__create_print_tree()
        self.command_tree["scripts"] = self.__create_script_tree()

    def __create_print_tree(self) -> Dict[str, Any]:
        tree = dict()
        tree["DEBUG"] = self.__create_attribute_tree(DEBUG, "printables")
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
    ):
        try:
            commands_list = self.__text_to_commands(text)
        except ValueError as e:
            return str(e), True
        for arguments in commands_list:
            arguments = arguments.strip().split(" ")
            if arguments[0] == "print":
                return self.__process_print(arguments), False
            elif arguments[0] == "scripts":

                return self.__process_script_call(arguments)


            #     return self.__process(commands)
            # elif commands[0] == "create":
            #     return self.__process_create(commands)
            # elif commands[0] == "delete":
            #     return self.__process_delete(commands)
            # elif commands[0] == "print":
            #     # make sure that the last part of the command is executed.
            #     return self.__process(commands + [" "])
            # elif commands[0] == "scripts":
            #     if commands[1] in self.command_tree["scripts"]:
            #         self.__process_commands(self.command_tree["scripts"][commands[1]])
            #     else:
            #         return "No script known by name {}".format(commands[1]), True
            else:
                return "{} is not a valid command. Choose one of the following: {}."\
                    .format(arguments[0], ", ".join(self.command_tree.keys())), True

    def __process_print(self, arguments):
        target = globals()[arguments[1]]
        index = 2
        while index < len(arguments):
            target = getattr(target, arguments[index])
            index += 1
        return "Value of {} is {}".format(".".join(arguments[1:]), str(target))

    def __process_script_call(
        self,
        arguments: List[str]
    ) -> Tuple[str, bool]:
        """Process a script call by taking the called script and calling all script lines that are provided by ;
        separation"""
        command_line = self.command_tree["scripts"][arguments[1]]
        total_message = ""
        all_return_code = True
        for line in command_line.split(";"):
            message, return_code = self.process_command_line_text(line)
            all_return_code = return_code and all_return_code
            total_message += message + "\n"
        return total_message[:-1], all_return_code

    def __text_to_commands(self, text):
        text = text.strip()
        lists = {}
        if text.count("]") != text.count("["):
            raise ValueError("Uneven amount of open and closing brackets.")
        # first get all lists within lists
        count = 0
        while True:
            matches = re.findall("\[[^\[]+?\]", text)
            if matches:
                for match in matches:
                    text = text.replace(match, ",list" + str(count))
                    lists["list" + str(count)] = match
                    count += 1
            else:
                break
        # then get all commands conveyed by those lists
        return self.__get_command_list(text, lists)

    def __get_command_list(self, text, lists):
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

    # def __process(self, commands):
    # #     if len(commands) < 3:
    #         return "Expected al least 3 arguments to SET command [FROM, NAME, VALUE].", True
    #     if commands[1] == "game_rule":
    #         self.__execute(game_rules, commands)
    #     elif commands[1] == "player":
    #         self.__execute(self.screen.player, commands)
    #     elif commands[1] == "room_entities":
    #         enemie = None
    #         for e in self.stage.room_group.sprites():
    #             if str(e) == commands[2]:
    #                 enemie = e
    #                 break
    #         if enemie:
    #             self.__execute(enemie, commands, 2)
    #         else:
    #             self.main_sprite.add_error_message("Unknown enemy {}.".format(commands[2]))
    #     elif commands[1] == "entities":
    #         correct_class = None
    #         for c in inspect.getmembers(entities, inspect.isclass):
    #             if c[0] == commands[2]:
    #                 correct_class = c[1]
    #                 break
    #         if correct_class:
    #             self.__execute(correct_class, commands, 2)
    #         else:
    #             self.main_sprite.add_error_message("Unknown entity class {}.".format(commands[2]))
    #     elif commands[1] == "stage":
    #         self.__execute(self.stage, commands)
    #     elif commands[1] == "weapon":
    #         self.__execute(self.weapon_parts[commands[2]][commands[3]], commands, 3)
    #     else:
    #         self.main_sprite.add_error_message("{} is not a valid FROM location. Choose one of the following: game_rule, player, room_entities, entities".format(commands[1]))
    #
    # def __execute(self, target, commands, from_l=1):
    #     for i, name in enumerate(commands[1 + from_l:-1]):
    #         if hasattr(target, name):
    #             if i < len(commands[1 + from_l:-1]) - 1:
    #                 target = getattr(target, name)
    #             else:
    #                 if commands[0] == "set":
    #                     try:
    #                         value = self.__convert_to_type(type(getattr(target, name)), commands[-1],
    #                                                        getattr(target, name), target)
    #                     except ValueError as e:
    #                         return str(e), True
    #                     if type(getattr(target, name)) is property:
    #                         getattr(target, name).fset(target, value)
    #                     else:
    #                         setattr(target, name, value)
    #                     return "{} is set to {}".format(".".join(commands[1:-1]), value), False
    #                 elif commands[0] == "print":
    #                     val = getattr(target, name)
    #                     if type(val) is property:
    #                         val = getattr(target, name).fget(target)
    #                     return "The value of {} is: {}".format(".".join(commands[1:-1]), val), False
    #         else:
    #             return "{} has no attribute {}.".format(target, name), True

    def __convert_to_type(self, type_s, s, orig_value=None, target=None):
        try:
            if type_s is str:
                return s
            elif type_s is bool:
                return self.__string_to_bool(s)
            elif type_s is int:
                return int(s)
            elif type_s is float:
                return float(s)
            elif type_s is list:
                return self.__string_to_list(s, [type(val) for val in orig_value])
            elif type_s is tuple:
                return self.__string_to_list(s, [type(val) for val in orig_value])
            elif type_s is property:
                return self.__convert_to_type(type(orig_value.fget(target)), s)
            elif con.DEBUG.WARNINGS:
                print("No case for value of type_s {}".format(type_s))
        except ValueError as e:
            raise e
        raise ValueError("cannot convert to type_s {}. No known method.".format(type_s))

    def __string_to_bool(self, value):
        value = value.lower()
        if value == "true" or value == "t":
            return True
        elif value == "false" or value == "f":
            return False
        else:
            raise ValueError("expected a boolean to be either: true, t, false or f (case insensitive)".format(value))

    def __string_to_list(self, value, types):
        """
        only a one dimensional list is expected
        """
        if "(" not in value:
            raise ValueError("expected a list to be of form (val1;val2;..)")
        value = value.replace("(", "").replace(")", "")
        the_list = [val.strip() for val in value.split(";")]
        if len(types) != len(the_list):
            raise ValueError("list is of wrong length. Expected a list of lenght {}.".format(len(types)))
        for i, val_type in enumerate(types):
            try:
                user_value = the_list[i]
                if val_type != str:
                    user_value = user_value.strip()
                correct_typed_value = self.__convert_to_type(val_type, user_value)
                the_list[i] = correct_typed_value
            except ValueError:
                raise ValueError("expected value of type {} at index {}. Cannot convert {} to {}."
                                 .format(val_type, i, the_list[i], val_type))
        return the_list
