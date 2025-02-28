# from pprint import pprint

import jsondiff
from pytest_regressions.data_regression import DataRegressionFixture

import gdsfactory as gf

gdspath = gf.CONFIG["gdsdir"] / "mzi2x2.gds"


def test_read_gds_hash2() -> gf.Component:
    c = gf.import_gds(gdspath)
    assert (
        c.hash_geometry() == "021d5b67cc60a49ff09fe5f1a91e116cccb75284"
    ), c.hash_geometry()
    return c


def test_read_gds_with_settings2(data_regression: DataRegressionFixture) -> None:
    c = gf.import_gds(gdspath)
    data_regression.check(c.to_dict())


def test_read_gds_equivalent2() -> None:
    """Ensures we can load it from GDS + YAML and get the same component settings"""
    c1 = gf.components.mzi()
    c2 = gf.import_gds(gdspath)

    d1 = c1.to_dict()
    d2 = c2.to_dict()

    # we change the name, so there is no cache conflicts
    # d1.pop("name")
    # d2.pop("name")
    # d1.pop("ports")
    # d2.pop("ports")
    # c1.pprint()
    # c2.pprint()

    d = jsondiff.diff(d1, d2)

    # from pprint import pprint
    # pprint(d1)
    # pprint(d2)
    # pprint(d)
    assert len(d) == 0, d


def test_mix_cells_from_gds_and_from_function2() -> None:
    """Ensures not duplicated cell names.
    when cells loaded from GDS and have the same name as a function
    with @cell decorator
    """
    c = gf.Component("test_mix_cells_from_gds_and_from_function")
    c << gf.components.mzi()
    c << gf.import_gds(gdspath)
    c.write_gds()
    c.show()


def _write() -> None:
    c1 = gf.components.mzi()
    c1.write_gds_with_metadata(gdspath=gdspath)
    c1.show()


if __name__ == "__main__":
    _write()
    test_read_gds_equivalent2()

    # c = test_read_gds_hash2()
    # c.show()
    # test_mix_cells_from_gds_and_from_function2()

    # test_read_gds_with_settings2()
    c1 = gf.components.mzi()
    c2 = gf.import_gds(gdspath)
    d1 = c1.to_dict()
    d2 = c2.to_dict()

    d = jsondiff.diff(d1, d2)
    print(d)
