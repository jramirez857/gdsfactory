from typing import Optional, Tuple

from gdsfactory.cell import cell
from gdsfactory.component import Component
from gdsfactory.components.compass import compass
from gdsfactory.types import Ints, Layer


@cell
def rectangle(
    size: Tuple[float, float] = (4.0, 2.0),
    layer: Layer = (1, 0),
    centered: bool = False,
    port_type: Optional[str] = "electrical",
    port_orientations: Optional[Ints] = (180, 90, 0, -90),
) -> Component:
    """Returns a rectangle.

    Args:
        size: (tuple) Width and height of rectangle.
        layer: Specific layer to put polygon geometry on.
        centered: True sets center to (0, 0), False sets south-west to (0, 0).
        port_type: optical, electrical.
        port_orientations: list of port_orientations to add.

    """
    c = Component()
    ref = c << compass(
        size=size, layer=layer, port_type=port_type, port_orientations=port_orientations
    )
    if not centered:
        ref.move((size[0] / 2, size[1] / 2))
    if port_type:
        c.add_ports(ref.ports)
    return c


if __name__ == "__main__":
    c = rectangle(size=(3, 2), centered=False, layer=(2, 3))
    # c = rectangle(size=(3, 2), centered=True, layer=(2, 3))
    print(c.ports)
    print(c.name)
    c.show()
