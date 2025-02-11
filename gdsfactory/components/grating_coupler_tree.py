from typing import Tuple

import gdsfactory as gf
from gdsfactory.component import Component
from gdsfactory.components.bend_euler import bend_euler
from gdsfactory.components.grating_coupler_elliptical import (
    grating_coupler_elliptical_te,
)
from gdsfactory.components.straight_array import straight_array
from gdsfactory.types import ComponentSpec


@gf.cell
def grating_coupler_tree(
    n: int = 4,
    straight_spacing: float = 4.0,
    grating_coupler_function: ComponentSpec = grating_coupler_elliptical_te,
    with_loopback: bool = False,
    bend: ComponentSpec = bend_euler,
    fanout_length: float = 0.0,
    layer_label: Tuple[int, int] = (66, 0),
    **kwargs
) -> Component:
    """Array of straights connected with grating couplers
    useful to align the 4 corners of the chip

    Args:
        n: number of gratings.
        straight_spacing:
        grating_coupler_function:
        with_loopback:
        bend:
        fanout_length:
        layer_label:
        kwargs: cross_section settings

    """
    c = straight_array(
        n=n,
        spacing=straight_spacing,
        **kwargs,
    )

    return gf.routing.add_fiber_array(
        component=c,
        with_loopback=with_loopback,
        optical_routing_type=0,
        grating_coupler=grating_coupler_function,
        fanout_length=fanout_length,
        component_name=c.name,
        bend=bend,
        layer_label=layer_label,
        taper=None,
        **kwargs,
    )


if __name__ == "__main__":
    c = grating_coupler_tree(layer=(2, 0))
    # print(c.settings)
    c.show()
