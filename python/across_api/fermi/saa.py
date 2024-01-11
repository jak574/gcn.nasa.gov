# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

import astropy.units as u  # type: ignore
from shapely.geometry import Polygon  # type: ignore

from ..base.config import set_observatory
from ..base.saa import SAABase, SAAPolygonBase
from .config import FERMI
from .ephem import FermiEphem


class FermiSAAPolygon(SAAPolygonBase):
    """Class to define the Fermi SAA polygon.

    Attributes
    ----------
    points : list
        List of points defining the SAA polygon.
    saapoly : Polygon
        Shapely Polygon object defining the SAA polygon.
    """

    # SAA polygon for Fermi from here:
    # https://fermi.gsfc.nasa.gov/ssc/data/analysis/software/aux/L_SAA_2008198.03
    points: list = [
        (33.900000, -30.000000),
        (24.500000, -22.600000),
        (-18.600000, -2.500000),
        (-25.700000, -5.200000),
        (-36.000000, -5.200000),
        (-42.000000, -4.600000),
        (-58.800000, -0.700000),
        (-93.100000, -8.600000),
        (-97.500000, -9.900000),
        (-98.500000, -12.500000),
        (-92.100000, -21.700000),
        (-86.100000, -30.000000),
    ]

    saapoly: Polygon = Polygon(points)


@set_observatory(FERMI)
class FermiSAA(SAABase):
    """
    Class to calculate Fermi SAA passages.
    """

    saa = FermiSAAPolygon()
    ephemclass = FermiEphem

    def __init__(self, begin, end, ephem=None, stepsize=60 * u.s):
        """
        Initialize the SAA class. Set up the Ephemeris if it's not given.
        """
        # Need to instantiate the ephem class here or else th
        if ephem is None:
            ephem = FermiEphem(begin, end, stepsize)
        super().__init__(begin, end, ephem, stepsize)
