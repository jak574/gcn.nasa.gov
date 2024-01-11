# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

import astropy.units as u  # type: ignore
from shapely.geometry import Polygon  # type: ignore

from ..base.config import set_observatory
from ..base.saa import SAABase, SAAPolygonBase
from .config import BURSTCUBE
from .ephem import BurstCubeEphem


class BurstCubeSAAPolygon(SAAPolygonBase):
    """
    Class to define the BurstCube SAA polygon.
    """

    points: list = [
        (33.900000, -30.0),
        (12.398, -19.876),
        (-9.103, -9.733),
        (-30.605, 0.4),
        (-38.4, 2.0),
        (-45.0, 2.0),
        (-65.0, -1.0),
        (-84.0, -6.155),
        (-89.2, -8.880),
        (-94.3, -14.220),
        (-94.3, -18.404),
        (-84.48631, -31.84889),
        (-86.100000, -30.0),
        (-72.34921, -43.98599),
        (-54.5587, -52.5815),
        (-28.1917, -53.6258),
        (-0.2095279, -46.88834),
        (28.8026, -34.0359),
        (33.900000, -30.0),
    ]

    saapoly: Polygon = Polygon(points)


@set_observatory(BURSTCUBE)
class BurstCubeSAA(SAABase):
    """
    Class to calculate BurstCube SAA passages.
    """

    saa = BurstCubeSAAPolygon()
    ephemclass = BurstCubeEphem

    def __init__(self, begin, end, ephem=None, stepsize=60 * u.s):
        """
        Initialize the SAA class. Set up the Ephemeris if it's not given.
        """
        # Need to instantiate the ephem class here or else th
        if ephem is None:
            ephem = BurstCubeEphem(begin, end, stepsize)
        super().__init__(begin, end, ephem, stepsize)
