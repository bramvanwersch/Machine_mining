#!/usr/bin/python3

# library imports
import inspect
from typing import Set

# own imports
import block_classes.materials as base_materials
import block_classes.ground_materials as ground_m
import block_classes.environment_materials as env_m
import block_classes.building_materials as build_m
import utility.utilities as util


# Collections used for getting all type of a certain material for conventience
fuel_materials: Set = set()
environment_materials: Set = set()


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
