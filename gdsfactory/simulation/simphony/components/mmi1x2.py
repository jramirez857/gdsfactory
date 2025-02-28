import gdsfactory as gf
from gdsfactory.simulation.simphony.model_from_gdsfactory import model_from_gdsfactory


def mmi1x2(**kwargs):
    r"""Return 1x2 MultiModeInterferometer Sparameter model.

    Keyword Args:
        width: input and output straight width
        width_taper: interface between input straights and mmi region
        length_taper: into the mmi region
        length_mmi: in x direction
        width_mmi: in y direction
        gap_mmi:  gap between tapered wg
        taper: taper function
        layer:
        layers_cladding:
        cladding_offset

    .. code::

               length_mmi
                <------>
                ________
               |        |
               |         \__
               |          __  o2
            __/          /_ _ _ _
        o1  __          | _ _ _ _| gap_mmi
              \          \__
               |          __  o3
               |         /
               |________|

             <->
        length_taper

    .. plot::
      :include-source:

      import gdsfactory as gf
      c = gf.components.mmi1x2(width_mmi=2, length_mmi=2.8)
      c.plot()

    .. plot::
        :include-source:

        import gdsfactory.simulation.simphony as gs
        import gdsfactory.simulation.simphony.components as gc

        c = gc.mmi1x2()
        gs.plot_model(c)
    """
    return model_from_gdsfactory(gf.components.mmi1x2)


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import numpy as np

    from gdsfactory.simulation.simphony.plot_model import plot_model

    wav = np.linspace(1520, 1570, 1024) * 1e-9
    f = 3e8 / wav
    c = mmi1x2()

    # s = c.s_parameters(freq=f)
    # plt.plot(wav, np.abs(s[:, 1] ** 2))
    # print(c.pins)
    # print(c.settings)

    plot_model(c)
    plt.show()
