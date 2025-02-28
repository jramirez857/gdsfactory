from gdsfactory.component import Component, ComponentReference

try:
    import dphox as dp

    DPHOX_IMPORTED = True
except ImportError:
    DPHOX_IMPORTED = False


def from_dphox(device: "dp.Device", foundry: "dp.foundry.Foundry") -> Component:
    """Converts a Dphox Device into a gdsfactory Component.

    Note that you need to install dphox `pip install dphox`

    https://dphox.readthedocs.io/en/latest/index.html

    Args:
        device: Dphox device
        foundry: Dphox foundry object
    """
    c = Component(device.name)

    for layer_name, shapely_multipolygon in device.layer_to_polys.items():
        for poly in shapely_multipolygon:
            layer = foundry.layer_to_gds_label[layer_name]
            c.add_polygon(points=poly, layer=layer)

    for ref in device.child_to_device:
        child = from_dphox(device.child_to_device[ref], foundry)
        for gds_transform in device.child_to_transform[ref][-1]:
            new_ref = ComponentReference(
                component=child,
                origin=(gds_transform.x, gds_transform.y),
                rotation=gds_transform.angle,
                magnification=gds_transform.mag,
                x_reflection=gds_transform.flip_y,
            )
            new_ref.owner = c
            c.add(new_ref)

    for port_name, port in device.port.items():
        c.add_port(
            name=port_name,
            midpoint=(port.x, port.y),
            orientation=port.a,
            width=port.w,
            layer=foundry.layer_to_gds_label.get(port.layer, (1, 0)),
        )
    return c


if __name__ == "__main__":
    from dphox.demo import mzi

    c = from_dphox(mzi, foundry=dp.foundry.FABLESS)
    c.show()
