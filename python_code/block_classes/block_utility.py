#!/usr/bin/python3

# library imports
import inspect
from typing import Set, Union, Type, Dict, Any

# own imports
import block_classes.materials.materials as base_materials
import block_classes.materials.ground_materials as ground_m
import block_classes.materials.environment_materials as env_m
import block_classes.materials.building_materials as build_m
from utility import utilities as util, loading_saving

# Collections used for getting all type of a certain material for conventience
fuel_materials: Set = set()
environment_materials: Set = set()


class MCD(loading_saving.Savable):
    """Allows to define a MaterialClassDefinition where you can save a material class linked to arguments needed for
    instantiation.

    This allows for the definition of a material without instantiation to be done on a later moment. The instantiation
    is flexible and can be done with a string a material type or an MCD"""
    __slots__ = "material", "needs_board_update", "kwargs", "block_kwargs", "__is_string"

    material: Union[Type[base_materials.BaseMaterial], str]
    kwargs: Dict[str, Any]
    needs_board_update: bool
    block_kwargs: Dict[str, Any]
    __is_string: bool

    def __init__(
        self,
        material: Union[Type[base_materials.BaseMaterial], str, "MCD"],
        needs_board_update: bool = False,
        block_kwargs: Dict[str, Any] = None,
        **arguments
    ):
        if isinstance(material, MCD):
            self.material = material.material
            self.kwargs = material.kwargs
            self.block_kwargs = material.block_kwargs
            self.needs_board_update = material.needs_board_update
        else:
            self.material = material
            self.kwargs = arguments
            self.block_kwargs = {} if block_kwargs is None else block_kwargs
            self.needs_board_update = needs_board_update
        self.__is_string = isinstance(self.material, str)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "material": self.material if self.__is_string else self.material.name(),
            "needs_board_update": self.needs_board_update,
            "arguments": {name: value.to_dict() if isinstance(value, loading_saving.Savable) else value
                          for name, value in self.kwargs.items()},
            "block_kwargs": {name: value.to_dict() if isinstance(value, loading_saving.Savable) else value
                             for name, value in self.block_kwargs.items()}
        }

    def to_instance(
        self,
        **additional_kwargs
    ) -> base_materials.BaseMaterial:
        if self.__is_string:
            return material_instance_from_string(self.material, **self.kwargs, **additional_kwargs)
        return self.material(**self.kwargs, **additional_kwargs)

    def name(self) -> str:
        if self.__is_string:
            return self.material
        return self.material.name()


def material_instance_from_string(string: str, **kwargs) -> base_materials.BaseMaterial:
    """Get the instance of the material named by string

    Args:
        string (str): name of the material you want the instance from
        **kwargs: optional arguments

    Returns:
        material instance
    """
    if string in dir(ground_m):
        material = getattr(ground_m, string)
    elif string in dir(env_m):
        material = getattr(env_m, string)
    elif string in dir(build_m):
        material = getattr(build_m, string)
    # elif string in dir(block_classes.machine_materials):
    #     material = getattr(block_classes.machine_materials, string)
    else:
        material = getattr(base_materials, string)
    return material(**kwargs)


def configure_material_collections() -> None:
    """Configure the sets of materials names at the beginning of the module"""
    global fuel_materials, environment_materials
    for module in (env_m, ground_m):
        for name, cls in inspect.getmembers(module, inspect.isclass):
            selected_sets = []
            if issubclass(cls, ground_m.Burnable) and not util.is_abstract(cls):
                selected_sets.append(fuel_materials)
            if (issubclass(cls, env_m.EnvironmentMaterial) or issubclass(cls, env_m.MultiFloraMaterial))\
                    and not util.is_abstract(cls):
                selected_sets.append(environment_materials)
            if len(selected_sets) > 0:
                [set_.add(cls) for set_ in selected_sets]
