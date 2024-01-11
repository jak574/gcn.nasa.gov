# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

import astropy.units as u  # type: ignore
from shapely.geometry import Polygon  # type: ignore

from ..base.config import set_observatory
from ..base.saa import SAABase, SAAPolygonBase
from .config import NICER
from .ephem import NICEREphem


class NICERSAAPolygon(SAAPolygonBase):
    """Class to define the NICER SAA polygon.

    Attributes
    ----------
    points : list
        List of points defining the SAA polygon.
    saapoly : Polygon
        Shapely Polygon object defining the SAA polygon.
    """

    points: list = [
        (39.0, -30.0),
        (36.0, -26.0),
        (28.0, -21.0),
        (6.0, -12.0),
        (-5.0, -6.0),
        (-21.0, 2.0),
        (-30.0, 3.0),
        (-45.0, 2.0),
        (-60.0, -2.0),
        (-75.0, -7.0),
        (-83.0, -10.0),
        (-87.0, -16.0),
        (-86.0, -23.0),
        (-83.0, -30.0),
    ]

    saapoly: Polygon = Polygon(points)


@set_observatory(NICER)
class NICERSAA(SAABase):
    """
    Class to calculate NICER SAA passages.
    """

    saa = NICERSAAPolygon()
    ephemclass = NICEREphem

    def __init__(self, begin, end, ephem=None, stepsize=60 * u.s):
        """
        Initialize the SAA class. Set up the Ephemeris if it's not given.
        """
        # Need to instantiate the ephem class here or else th
        if ephem is None:
            ephem = NICEREphem(begin, end, stepsize)
        super().__init__(begin, end, ephem, stepsize)
