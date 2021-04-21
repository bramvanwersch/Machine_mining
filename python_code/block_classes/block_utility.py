#!/usr/bin/python3

# library imports
import inspect
from typing import Set, Union, Type

# own imports
import block_classes.materials as base_materials
import block_classes.ground_materials as ground_m
import block_classes.environment_materials as env_m
import block_classes.building_materials as build_m
import utility.utilities as util

# Collections used for getting all type of a certain material for conventience
fuel_materials: Set = set()
environment_materials: Set = set()


class MCD:
    """Allows to define a MaterialClassDefinition where you can save a material class linked to arguments needed for
    instantiation.

    This allows for the definition of a material without instantiation to be done on a later moment. The instantiation
    is flexible and can be done with a string a material type or an MCD"""
    def __init__(self, material: Union[Type[base_materials.BaseMaterial], str, "MCD"], **arguments):
        if isinstance(material, MCD):
            self.material = material.material
            self.kwargs = material.kwargs
        else:
            self.material = material
            self.kwargs = arguments
        self.__is_string = isinstance(self.material, str)

    def to_instance(self, **additional_kwargs):
        if self.__is_string:
            return material_instance_from_string(self.material, **self.kwargs, **additional_kwargs)
        return self.material(**self.kwargs)

    def name(self):
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
