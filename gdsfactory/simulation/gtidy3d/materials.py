from functools import partial
from typing import Dict, Union

import tidy3d as td
from tidy3d.components.medium import PoleResidue
from tidy3d.components.types import ComplexNumber
from tidy3d.material_library import material_library

MATERIAL_NAME_TO_MEDIUM = {
    "si": material_library["cSi"]["Li1993_293K"],
    "csi": material_library["cSi"]["Li1993_293K"],
    "sio2": material_library["SiO2"]["Horiba"],
    "sin": material_library["Si3N4"]["Luke2015"],
    "si3n4": material_library["Si3N4"]["Luke2015"],
}

# not dispersive materials have a constant index
MATERIAL_NAME_TO_TIDY3D_INDEX = {
    "si": 3.47,
    "sio2": 1.44,
    "sin": 2.0,
}

# dispersive materials
MATERIAL_NAME_TO_TIDY3D_NAME = {
    "si": "cSi",
    "sio2": "SiO2",
    "sin": "Si3N4",
}


def get_epsilon(
    name_or_index: Union[str, float],
    wavelength: float = 1.55,
    material_name_to_medium: Dict[str, PoleResidue] = MATERIAL_NAME_TO_MEDIUM,
) -> ComplexNumber:
    """Return permittivity from material database.

    Args:
        name_or_index: material name or refractive index.
        wavelength: wavelength (um)
        material_name_to_medium:
    """
    medium = get_medium(
        name_or_index=name_or_index, material_name_to_medium=material_name_to_medium
    )
    frequency = td.C_0 / wavelength
    return medium.eps_model(frequency)


def get_index(
    name_or_index: Union[str, float],
    wavelength: float = 1.55,
    material_name_to_medium: Dict[str, PoleResidue] = MATERIAL_NAME_TO_MEDIUM,
) -> float:
    """Return refractive index from material database.

    Args:
        wavelength: wavelength (um)
        name_or_index: material name or refractive index.
        material_name_to_medium:
    """

    eps_complex = get_epsilon(
        wavelength=wavelength,
        name_or_index=name_or_index,
        material_name_to_medium=material_name_to_medium,
    )
    n, _ = td.Medium.eps_complex_to_nk(eps_complex)
    return n


def get_medium(
    name_or_index: Union[str, float],
    material_name_to_medium: Dict[str, PoleResidue] = MATERIAL_NAME_TO_MEDIUM,
) -> td.Medium:
    """Return Medium from materials database

    Args:
        name_or_index: material name or refractive index.
        material_name_to_medium:
    """

    name_or_index = (
        name_or_index.lower() if isinstance(name_or_index, str) else name_or_index
    )

    if isinstance(name_or_index, (int, float)):
        m = td.Medium(permittivity=name_or_index**2)
    elif name_or_index in material_name_to_medium:
        m = material_name_to_medium[name_or_index]
    else:
        materials = list(material_name_to_medium.keys())

        raise ValueError(f"Material {name_or_index!r} not in {materials}")

    return m


si = partial(get_index, "si")
sio2 = partial(get_index, "sio2")

if __name__ == "__main__":
    print(si(1.55))
    # print(get_index(name_or_index="cSi"))
    # print(get_index(name_or_index=3.4))
    # m = get_medium(name_or_index="SiO2")
    # m = td.Medium(permittivity=1.45 ** 2)
