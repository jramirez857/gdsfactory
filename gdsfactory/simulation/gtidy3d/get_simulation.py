"""Returns tidy3d simulation from gdsfactory Component."""
import warnings
from typing import Dict, Optional

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pydantic
import tidy3d as td

import gdsfactory as gf
from gdsfactory.component import Component
from gdsfactory.components.extension import move_polar_rad_copy
from gdsfactory.config import logger
from gdsfactory.routing.sort_ports import sort_ports_x, sort_ports_y
from gdsfactory.simulation.gtidy3d.materials import (
    MATERIAL_NAME_TO_TIDY3D_INDEX,
    MATERIAL_NAME_TO_TIDY3D_NAME,
    get_index,
    get_medium,
)
from gdsfactory.tech import LAYER_STACK, LayerStack
from gdsfactory.types import ComponentSpec, Float2


@pydantic.validate_arguments
def get_simulation(
    component: ComponentSpec,
    port_extension: Optional[float] = 4.0,
    layer_stack: LayerStack = LAYER_STACK,
    thickness_pml: float = 1.0,
    xmargin: float = 0,
    ymargin: float = 0,
    xmargin_left: float = 0,
    xmargin_right: float = 0,
    ymargin_top: float = 0,
    ymargin_bot: float = 0,
    zmargin: float = 1.0,
    clad_material: str = "sio2",
    port_source_name: str = "o1",
    port_margin: float = 0.5,
    port_source_offset: float = 0.1,
    distance_source_to_monitors: float = 0.2,
    resolution: float = 50,
    wavelength_start: float = 1.50,
    wavelength_stop: float = 1.60,
    wavelength_points: int = 50,
    plot_modes: bool = False,
    num_modes: int = 2,
    run_time_ps: float = 10.0,
    dispersive: bool = False,
    material_name_to_tidy3d_index: Dict[str, float] = MATERIAL_NAME_TO_TIDY3D_INDEX,
    material_name_to_tidy3d_name: Dict[str, str] = MATERIAL_NAME_TO_TIDY3D_NAME,
    is_3d: bool = True,
    with_all_monitors: bool = False,
    **kwargs,
) -> td.Simulation:
    r"""Returns Simulation object from gdsfactory.component

    based on GDS example
    https://simulation.cloud/docs/html/examples/ParameterScan.html

    .. code::

         top view
              ________________________________
             |                               |
             | xmargin_left                  | port_extension
             |<------>          port_margin ||<-->
          ___|___________          _________||___
             |           \        /          |
             |            \      /           |
             |             ======            |
             |            /      \           |
          ___|___________/        \__________|___
             |   |                 <-------->|
             |   |ymargin_bot   xmargin_right|
             |   |                           |
             |___|___________________________|

        side view
              ________________________________
             |                     |         |
             |                     |         |
             |                   zmargin_top |
             |xmargin_left         |         |
             |<---> _____         _|___      |
             |     |     |       |     |     |
             |     |     |       |     |     |
             |     |_____|       |_____|     |
             |       |                       |
             |       |                       |
             |       |zmargin_bot            |
             |       |                       |
             |_______|_______________________|


    Args:
        component: gdsfactory Component.
        port_extension: extend ports beyond the PML.
        layer_stack: contains layer numbers (int, int) to thickness, zmin.
        thickness_pml: PML thickness (um).
        xmargin: left/right distance from component to PML.
        xmargin_left: left distance from component to PML.
        xmargin_right: right distance from component to PML.
        ymargin: left/right distance from component to PML.
        ymargin_top: top distance from component to PML.
        ymargin_bot: bottom distance from component to PML.
        zmargin: thickness for cladding above and below core.
        clad_material: material for cladding.
        port_source_name: input port name.
        port_margin: margin on each side of the port.
        distance_source_to_monitors: in (um) source goes before monitors.
        port_source_offset: mode solver workaround.
            positive moves source forward, negative moves source backward.
        resolution: in pixels/um (20: for coarse, 120: for fine)
        wavelength_start: in (um).
        wavelength_stop: in (um).
        wavelength_points: number of wavelengths.
        plot_modes: plot source modes.
        num_modes: number of modes to plot.
        run_time_ps: make sure it's sufficient for the fields to decay.
            defaults to 10ps and counts on automatic shutoff to stop earlier if needed.
        dispersive: False uses constant refractive index materials.
            True adds wavelength depending materials.
            Dispersive materials require more computation.
        material_name_to_tidy3d_index: not dispersive materials have a constant index.
        material_name_to_tidy3d_name: dispersive materials have a wavelength
            dependent index. Maps layer_stack names with tidy3d material database names.
        is_3d: if False, does not consider Z dimension for faster simulations.
        with_all_monitors: if True, includes field monitors which increase results file size.

    keyword Args:
        grid_spec:

    .. code::

        import matplotlib.pyplot as plt
        import gdsfactory as gf
        import gdsfactory.simulation.tidy3d as gt

        c = gf.components.bend_circular()
        sim = gt.get_simulation(c)
        gt.plot_simulation(sim)

    """
    component = gf.get_component(component)
    assert isinstance(component, Component)

    layer_to_thickness = layer_stack.get_layer_to_thickness()
    layer_to_material = layer_stack.get_layer_to_material()
    layer_to_zmin = layer_stack.get_layer_to_zmin()
    # layer_to_sidewall_angle = layer_stack.get_layer_to_sidewall_angle()

    if dispersive:
        material_name_to_tidy3d = material_name_to_tidy3d_name
    else:
        material_name_to_tidy3d = material_name_to_tidy3d_index

    assert isinstance(
        component, Component
    ), f"component needs to be a gf.Component, got Type {type(component)}"
    if port_source_name not in component.ports:
        warnings.warn(
            f"port_source_name={port_source_name} not in {component.ports.keys()}"
        )
        port_source = component.get_ports_list(port_type="optical")[0]
        port_source_name = port_source.name
        warnings.warn(f"Selecting port_source_name={port_source_name} instead.")

    component_padding = gf.add_padding_container(
        component,
        default=0,
        top=ymargin or ymargin_top,
        bottom=ymargin or ymargin_bot,
        left=xmargin or xmargin_left,
        right=xmargin or xmargin_right,
    )
    component_extended = (
        gf.components.extension.extend_ports(
            component=component_padding, length=port_extension, centered=True
        )
        if port_extension
        else component_padding
    )

    gf.show(component_extended)
    component_extended = component_extended.flatten()

    component_ref = component_padding.ref()
    component_ref.x = 0
    component_ref.y = 0

    clad_material_name_or_index = material_name_to_tidy3d[clad_material]
    clad = td.Structure(
        geometry=td.Box(
            size=(td.inf, td.inf, td.inf),
            center=(0, 0, 0),
        ),
        medium=get_medium(name_or_index=clad_material_name_or_index),
    )
    structures = [clad]

    layers_thickness = [
        layer_to_thickness[layer]
        for layer in component.get_layers()
        if layer in layer_to_thickness
    ]

    if len(layer_to_thickness) < 1:
        raise ValueError(f"{component.get_layers()} not in {layer_to_thickness.keys()}")

    t_core = max(layers_thickness)
    cell_thickness = (
        thickness_pml + t_core + thickness_pml + 2 * zmargin
        if is_3d
        else 1 / resolution
    )

    sim_size = [
        component_ref.xsize + 2 * thickness_pml,
        component_ref.ysize + 2 * thickness_pml,
        cell_thickness,
    ]

    for layer in component.layers:
        if layer in layer_to_thickness and layer in layer_to_material:
            thickness = layer_to_thickness[layer]
            zmin = layer_to_zmin[layer] if is_3d else 0
            zmax = zmin + thickness if is_3d else 0

            if (
                layer in layer_to_material
                and layer_to_material[layer] in material_name_to_tidy3d
            ):
                name_or_index = material_name_to_tidy3d[layer_to_material[layer]]
                medium = get_medium(name_or_index=name_or_index)
                index = get_index(name_or_index=name_or_index)
                logger.debug(
                    f"Add {layer}, {name_or_index!r}, index = {index:.3f}, "
                    f"thickness = {thickness}, zmin = {zmin}, zmax = {zmax}"
                )

                polygons = td.PolySlab.from_gds(
                    gds_cell=component_extended,
                    gds_layer=layer[0],
                    gds_dtype=layer[1],
                    axis=2,
                    slab_bounds=(zmin, zmax),
                )

                for polygon in polygons:
                    geometry = td.Structure(
                        geometry=polygon,
                        medium=medium,
                    )
                    structures.append(geometry)
            elif layer not in layer_to_material:
                logger.debug(f"Layer {layer} not in {layer_to_material.keys()}")
            elif layer_to_material[layer] not in material_name_to_tidy3d:
                materials = list(material_name_to_tidy3d.keys())
                logger.debug(f"material {layer_to_material[layer]} not in {materials}")

    # Add source
    port = component_ref.ports[port_source_name]
    angle = port.orientation
    width = port.width + 2 * port_margin
    size_x = width * abs(np.sin(angle * np.pi / 180))
    size_y = width * abs(np.cos(angle * np.pi / 180))
    size_x = 0 if size_x < 0.001 else size_x
    size_y = 0 if size_y < 0.001 else size_y
    size_z = cell_thickness - 2 * zmargin if is_3d else td.inf

    source_size = [size_x, size_y, size_z]
    source_center = port.center.tolist() + [0]  # (x, y, z=0)

    xy_shifted = move_polar_rad_copy(
        np.array(port.center), angle=angle * np.pi / 180, length=port_source_offset
    )
    source_center_offset = xy_shifted.tolist() + [0]  # (x, y, z=0)

    wavelengths = np.linspace(wavelength_start, wavelength_stop, wavelength_points)
    freqs = td.constants.C_0 / wavelengths
    freq0 = td.constants.C_0 / np.mean(wavelengths)
    fwidth = freq0 / 10

    msource = td.ModeSource(
        size=source_size,
        center=source_center,
        source_time=td.GaussianPulse(freq0=freq0, fwidth=fwidth),
        direction="+",
    )

    # Add port monitors
    monitors = {}
    ports = sort_ports_x(sort_ports_y(component_ref.get_ports_list()))
    for port in ports:
        port_name = port.name
        angle = port.orientation
        width = port.width + 2 * port_margin
        size_x = width * abs(np.sin(angle * np.pi / 180))
        size_y = width * abs(np.cos(angle * np.pi / 180))
        size_x = 0 if size_x < 0.001 else size_x
        size_y = 0 if size_y < 0.001 else size_y
        size = (size_x, size_y, size_z)

        # if monitor has a source move monitor inwards
        length = -distance_source_to_monitors if port_name == port_source_name else 0
        xy_shifted = move_polar_rad_copy(
            np.array(port.center), angle=angle * np.pi / 180, length=length
        )
        center = xy_shifted.tolist() + [0]  # (x, y, z=0)

        monitors[port_name] = td.ModeMonitor(
            center=center,
            size=size,
            freqs=freqs,
            mode_spec=td.ModeSpec(num_modes=1),
            name=port.name,
        )

    zcenter = (zmax + zmin) / 2 if is_3d else 0
    domain_monitor = td.FieldMonitor(
        center=[0, 0, zcenter],
        size=[sim_size[0], sim_size[1], 0] if is_3d else [td.inf, td.inf, 0],
        freqs=[freq0],
        name="field",
    )
    monitors = list(monitors.values())
    monitors += [domain_monitor] if with_all_monitors else []

    sim = td.Simulation(
        size=sim_size,
        structures=structures,
        sources=[msource],
        monitors=monitors,
        run_time=20 * run_time_ps / fwidth,
        pml_layers=3 * [td.PML()] if is_3d else [td.PML(), td.PML(), None],
        **kwargs,
    )

    if plot_modes:
        mode_spec = td.ModeSpec(num_modes=num_modes)
        src_plane = td.Box(center=source_center_offset, size=source_size)
        ms = td.plugins.ModeSolver(
            simulation=sim, plane=src_plane, freqs=[freq0], mode_spec=mode_spec
        )
        modes = ms.solve()
        print("Effective index of computed modes: ", np.array(modes.n_eff))

        if is_3d:
            fig, axs = plt.subplots(num_modes, 2, figsize=(12, 12))
            for mode_ind in range(num_modes):
                modes.plot_field(
                    "Ey", "abs", freq=freq0, mode_index=mode_ind, ax=axs[mode_ind, 0]
                )
                modes.plot_field(
                    "Ez", "abs", freq=freq0, mode_index=mode_ind, ax=axs[mode_ind, 1]
                )
        else:
            fig, axs = plt.subplots(num_modes, 3, figsize=(12, 12))
            for mode_ind in range(num_modes):
                ax1 = axs[mode_ind, 0]
                ax2 = axs[mode_ind, 1]
                ax3 = axs[mode_ind, 2]

                abs(modes.fields.Ex.sel(mode_index=mode_ind).abs).plot(ax=ax1)
                abs(modes.fields.Ey.sel(mode_index=mode_ind).abs).plot(ax=ax2)
                abs(modes.fields.Ez.sel(mode_index=mode_ind).abs).plot(ax=ax3)

                ax1.set_title(f"|Ex|: mode_index={mode_ind}")
                ax2.set_title(f"|Ey|: mode_index={mode_ind}")
                ax3.set_title(f"|Ez|: mode_index={mode_ind}")

        plt.show()
    return sim


def plot_simulation_yz(
    sim: td.Simulation,
    z: float = 0.0,
    y: float = 0.0,
    wavelength: Optional[float] = 1.55,
    figsize: Float2 = (11, 4),
):
    """Returns Simulation visual representation.
    returns two views for 3D component and one view for 2D

    Args:
        sim: simulation object
        z: (um)
        y: (um)
        wavelength: (um) for epsilon plot if None plot structures.
        figsize: figure size
    """
    fig = plt.figure(figsize=figsize)
    if sim.size[2] > 0.1 and sim.size[1] > 0.1:
        gs = mpl.gridspec.GridSpec(1, 2, figure=fig, width_ratios=[1, 1.4])
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[0, 1])
        if wavelength:
            freq = td.constants.C_0 / wavelength
            sim.plot_eps(z=z, ax=ax1, freq=freq)
            sim.plot_eps(y=y, ax=ax2, freq=freq)
        else:
            sim.plot(z=z, ax=ax1)
            sim.plot(y=y, ax=ax2)
    elif sim.size[2] > 0.1:  # 2D grating sim_size_y = 0
        gs = mpl.gridspec.GridSpec(1, 1, figure=fig, width_ratios=[1])
        ax1 = fig.add_subplot(gs[0, 0])
        if wavelength:
            freq = td.constants.C_0 / wavelength
            sim.plot_eps(y=y, ax=ax1, freq=freq)
        else:
            sim.plot(y=y, ax=ax1)

    else:  # 2D planar component size_z = 0
        gs = mpl.gridspec.GridSpec(1, 1, figure=fig, width_ratios=[1])
        ax1 = fig.add_subplot(gs[0, 0])
        if wavelength:
            freq = td.constants.C_0 / wavelength
            sim.plot_eps(z=z, ax=ax1, freq=freq)
        else:
            sim.plot(z=z, ax=ax1)

    plt.show()
    return fig


def plot_simulation_xz(
    sim: td.Simulation,
    x: float = 0.0,
    z: float = 0.0,
    wavelength: Optional[float] = 1.55,
    figsize: Float2 = (11, 4),
):
    """Returns figure with two axis of the Simulation.

    Args:
        sim: simulation object
        x: (um)
        z: (um)
        wavelength: (um) for epsilon plot if None plot structures.
        figsize: figure size
    """
    fig = plt.figure(figsize=figsize)
    gs = mpl.gridspec.GridSpec(1, 2, figure=fig, width_ratios=[1, 1.4])
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    if wavelength:
        freq = td.constants.C_0 / wavelength
        sim.plot_eps(z=z, ax=ax1, freq=freq)
        sim.plot_eps(x=x, ax=ax2, freq=freq)
    else:
        sim.plot(z=z, ax=ax1)
        sim.plot(x=x, ax=ax2)
    plt.show()
    return fig


plot_simulation = plot_simulation_yz


if __name__ == "__main__":
    # c = gf.components.mmi1x2()
    # c = gf.components.bend_circular(radius=2)
    # c = gf.components.crossing()
    # c = gf.c.straight_rib()

    c = gf.c.straight(length=3)
    sim = get_simulation(c, plot_modes=True, is_3d=False)
    # plot_simulation(sim)

    # filepath = pathlib.Path(__file__).parent / "extra" / "wg2d.json"
    # filepath.write_text(sim.json())

    # sim.plotly(z=0)
    # plot_simulation_yz(sim, wavelength=1.55)
    # fig = plt.figure(figsize=(11, 4))
    # gs = mpl.gridspec.GridSpec(1, 2, figure=fig, width_ratios=[1, 1.4])
    # ax1 = fig.add_subplot(gs[0, 0])
    # ax2 = fig.add_subplot(gs[0, 1])
    # sim.plot(z=0.0, ax=ax1)
    # sim.plot(x=0.0, ax=ax2)
    # plt.show()
