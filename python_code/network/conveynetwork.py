
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
        return iter(self.__belts)

    def __len__(self):
        return len(self.__belts)
