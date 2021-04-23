
from typing import Set, TYPE_CHECKING

if TYPE_CHECKING:
    from block_classes.blocks import ConveyorNetworkBlock


class ConveyorNetwork:

    __belts: Set["ConveyorNetworkBlock"]

    def __init__(self):
        self.__belts = set()

    def add(self, belt: "ConveyorNetworkBlock"):
        self.__belts.add(belt)

    def remove(self, belt: "ConveyorNetworkBlock"):
        self.__belts.remove(belt)

    def __iter__(self):
        # the copy is neccesairy because loading chunks are able to add belts and that would crash the game
        return iter(self.__belts.copy())

    def __len__(self):
        return len(self.__belts)
