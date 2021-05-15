# !/usr/bin/python3

# library imports
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING, Tuple, Union, Set, Type, Hashable
import pygame

# own imports
import block_classes.materials.building_materials as build_materials
import block_classes.materials.materials as base_materials
import block_classes.blocks as block_classes
from utility import inventories, loading_saving
import utility.utilities as util
import interfaces.base_interface as base_interface
import interfaces.other_interfaces as small_interfaces
import interfaces.crafting_interfaces as craft_interfaces
import recipes.recipe_utility as r_constants
if TYPE_CHECKING:
    import board.sprite_groups as sprite_groups
    from interfaces.managers import game_window_manager


# TODO check the use of this
def building_type_from_material(material):
    return material_mapping[material.name()]


class Building(block_classes.MultiBlock, util.ConsoleReadable, loading_saving.Loadable, ABC):
    """
    Abstract class for buildings. Buildings are multiblock (can be 1) structures
    that contain an image
    """
    MATERIAL: base_materials.BaseMaterial

    def __init__(
        self,
        pos: List[int],
        **kwargs
    ):
        super().__init__(pos, self.MATERIAL(), **kwargs)

    def to_dict(self):
        d = super().to_dict()
        d["block_kwargs"]["pos"] = self.rect.topleft
        d["block_kwargs"]["instance_name"] = type(self).__name__
        return d

    @classmethod
    def from_dict(cls, dct, sprite_group=None, first=True):
        if first:
            cls_type = globals()[dct["block_kwargs"].pop("instance_name")]
            return cls_type.from_dict(dct, sprite_group=sprite_group, first=False)
        else:
            mcd = super().from_dict(dct)
            material = mcd.to_instance()
            posses = [[d["pos"] for d in row] for row in dct["blocks"]]
            mcds = [[block_classes.Block.from_dict(d) for d in row] for row in dct["blocks"]]
            blocks = [[mcd.to_instance().to_block(pos=posses[index][index2], **mcd.block_kwargs)
                       for index2, mcd in enumerate(row)] for index, row in enumerate(mcds)]
            return cls.load(**mcd.block_kwargs, blocks=blocks, material=material, sprite_group=sprite_group)

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def MATERIAL(self) -> Type[base_materials.BaseMaterial]:
        """
        Specify a material class. The material class should be called
        NameOfBuildingMaterial and the name of the building cannot contain the
        word Material

        :return: material class
        """
        pass

    def has_inventory(self) -> bool:
        """
        Check on the fly if any of the bocks of the building are a container block
        """
        for row in self.blocks:
            for block in row:
                if isinstance(block, block_classes.ContainerBlock):
                    return True
        return False


class InterfaceBuilding(Building, ABC):
    """abstraction level of buidlings with interfaces and inventory"""
    INTERFACE_TYPE: base_interface.Window

    inventory: inventories.Inventory
    window_manager: "game_window_manager"
    interface: base_interface.Window

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        size: int = -1,
        in_filter: inventories.Filter = None,
        out_filter: inventories.Filter = None,
        starting_items: inventories.Inventory = None,
        **kwargs
    ):
        self.inventory = inventories.Inventory(size, in_filter=in_filter, out_filter=out_filter)
        Building.__init__(self, pos, action=self.__select_buidling_action, **kwargs)
        from interfaces.managers import game_window_manager
        self.window_manager = game_window_manager

        self.interface = self.create_interface(sprite_group)
        self._add_starting_items(starting_items)

    def __init_load__(self, pos=None, sprite_group=None, inventory=None, **kwargs):
        self.inventory = inventory
        del kwargs["material"]
        Building.__init__(self, pos, action=self.__select_buidling_action, **kwargs)
        from interfaces.managers import game_window_manager
        self.window_manager = game_window_manager

        self.interface = self.create_interface(sprite_group)

    def to_dict(self):
        d = super().to_dict()
        d["block_kwargs"]["inventory"] = self.inventory.to_dict()
        return d

    @classmethod
    def from_dict(cls, dct, sprite_group=None, first=True):
        mcd = block_classes.Block.from_dict(dct)
        material = mcd.to_instance()
        inventory = inventories.Inventory.from_dict(mcd.block_kwargs.pop("inventory"))
        posses = [[d["pos"] for d in row] for row in dct["blocks"]]
        mcds = [[block_classes.Block.from_dict(d) for d in row] for row in dct["blocks"]]
        blocks = [[mcd.to_instance().to_block(pos=posses[index][index2], **mcd.block_kwargs)
                   for index2, mcd in enumerate(row)] for index, row in enumerate(mcds)]
        return cls.load(**mcd.block_kwargs, blocks=blocks, material=material, inventory=inventory,
                        sprite_group=sprite_group)

    # noinspection PyPep8Naming
    @property
    @abstractmethod
    def INTERFACE_TYPE(self) -> type:
        pass

    def _add_starting_items(
        self,
        starting_items: Union[None, inventories.Inventory]
    ):
        if starting_items is None:
            return
        for item in starting_items.get_all_items(ignore_filter=True):
            self.inventory.add_items(item)

    def create_interface(
        self,
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
    ) -> base_interface.Window:
        """Innitiate the interface window"""
        return self.INTERFACE_TYPE(self, sprite_group)

    def printables(self) -> Set[str]:
        attributes = super().printables()
        attributes.remove("window_manager")
        attributes.remove("interface")
        return attributes

    def __select_buidling_action(self) -> None:
        # make sure to update the window manager when needed
        if self.window_manager is None:
            from interfaces.managers import game_window_manager
            self.window_manager = game_window_manager
        self.window_manager.add(self.interface)

    def _get_blocks(self) -> List[List[block_classes.Block]]:
        blocks_ = super()._get_blocks()
        for row in blocks_:
            for block in row:
                block.inventory = self.inventory
        return blocks_


class Terminal(InterfaceBuilding):
    """
    Terminal building. The main interaction centrum for the workers
    """
    MATERIAL: Type[base_materials.BaseMaterial] = build_materials.TerminalMaterial
    MULTIBLOCK_LAYOUT: List[List[Hashable]] = [[1, 2], [3, 4]]
    INTERFACE_TYPE: base_interface.Window = small_interfaces.InventoryWindow

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        spite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        InterfaceBuilding.__init__(self, pos, spite_group, size=-1, **kwargs)

    def create_interface(
        self,
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
    ) -> base_interface.Window:
        """Innitiate the interface window"""
        return self.INTERFACE_TYPE(pygame.Rect(self.rect.left, self.rect.bottom, 300, 200),
                                   self.blocks[0][0].inventory, sprite_group, title="TERMINAL")


class StoneChest(InterfaceBuilding):
    """
    Terminal building. The main interaction centrum for the workers
    """
    MATERIAL: Type[base_materials.BaseMaterial] = build_materials.StoneChestMaterial
    MULTIBLOCK_LAYOUT: List[List[Hashable]] = [[1]]
    INTERFACE_TYPE: base_interface.Window = small_interfaces.InventoryWindow

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        spite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        InterfaceBuilding.__init__(self, pos, spite_group, size=100, **kwargs)

    def create_interface(
        self,
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
    ) -> base_interface.Window:
        """Innitiate the interface window"""
        return self.INTERFACE_TYPE(pygame.Rect(self.rect.left, self.rect.bottom, 300, 200),
                                   self.blocks[0][0].inventory, sprite_group, title="STONE CHEST")


class CraftingInterfaceBuilding(InterfaceBuilding, block_classes.VariableSurfaceBlock, ABC):
    __recipes: r_constants.RecipeBook

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        size: int = -1,
        in_filter: inventories.Filter = None,
        out_filter: inventories.Filter = None,
        **kwargs
    ):
        self.__recipes = type(self).get_recipe_book()
        super().__init__(pos, sprite_group, size, in_filter, out_filter, **kwargs)
        block_classes.VariableSurfaceBlock.__init__(self)

    def __init_load__(self, pos=None, sprite_group=None, inventory=None, **kwargs):
        self.__recipes = type(self).get_recipe_book()
        block_classes.VariableSurfaceBlock.__init__(self, changed=kwargs.pop("changed"))
        super().__init_load__(pos=pos, sprite_group=sprite_group, inventory=inventory, **kwargs)

    @classmethod
    def from_dict(cls, dct, sprite_group=None, first=True):
        mcd = block_classes.Block.from_dict(dct)
        material = mcd.to_instance()
        inventory = inventories.Inventory.from_dict(mcd.block_kwargs.pop("inventory"))
        posses = [[d["pos"] for d in row] for row in dct["blocks"]]
        mcds = [[block_classes.Block.from_dict(d) for d in row] for row in dct["blocks"]]
        blocks = [[mcd.to_instance().to_block(pos=posses[index][index2], **mcd.block_kwargs)
                   for index2, mcd in enumerate(row)] for index, row in enumerate(mcds)]
        return cls.load(**mcd.block_kwargs, blocks=blocks, material=material, inventory=inventory,
                        sprite_group=sprite_group)

    @staticmethod
    @abstractmethod
    def get_recipe_book() -> r_constants.RecipeBook:
        # this method is here instead of a class value because it is loaded on startup of the game
        pass

    def create_interface(
        self,
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
    ) -> base_interface.Window:
        return self.INTERFACE_TYPE(self, self.__recipes, sprite_group)


class Furnace(CraftingInterfaceBuilding):
    """
    Terminal building. The main interaction centrum for the workers
    """
    MATERIAL: Type[base_materials.BaseMaterial] = build_materials.FurnaceMaterial
    MULTIBLOCK_LAYOUT: List[List[Hashable]] = [[1, 2], [3, 4]]
    INTERFACE_TYPE: base_interface.Window = craft_interfaces.FurnaceWindow

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        CraftingInterfaceBuilding.__init__(self, pos, sprite_group,
                                           in_filter=inventories.Filter(whitelist=[]), size=200, **kwargs)

    def to_dict(self):
        d1 = super().to_dict()
        d2 = block_classes.VariableSurfaceBlock.to_dict(self)
        d1["block_kwargs"]["changed"] = d2["changed"]
        return d1

    @staticmethod
    def get_recipe_book():
        return r_constants.recipe_books["furnace"]


class Factory(CraftingInterfaceBuilding):
    MATERIAL: Type[base_materials.BaseMaterial] = build_materials.FactoryMaterial
    MULTIBLOCK_LAYOUT: List[List[Hashable]] = [[1, 2], [3, 4]]
    INTERFACE_TYPE: base_interface.Window = craft_interfaces.FactoryWindow

    def __init__(
        self,
        pos: Union[Tuple[int, int], List[int]],
        sprite_group: "sprite_groups.CameraAwareLayeredUpdates",
        **kwargs
    ):
        CraftingInterfaceBuilding.__init__(self, pos, sprite_group, size=300,
                                           in_filter=inventories.Filter(whitelist=[]), **kwargs)

    def to_dict(self):
        d1 = super().to_dict()
        d2 = block_classes.VariableSurfaceBlock.to_dict(self)
        d1["block_kwargs"]["changed"] = d2["changed"]
        return d1

    @staticmethod
    def get_recipe_book():
        return r_constants.recipe_books["factory"]


material_mapping = {"TerminalMaterial": Terminal,
                    "FurnaceMaterial": Furnace,
                    "FactoryMaterial": Factory,
                    "StoneChestMaterial": StoneChest}
