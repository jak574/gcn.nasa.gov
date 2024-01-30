# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from typing import Type

from ..base.constraints import SAAPolygonConstraint  # type: ignore
from ..base.saa import SAABase
from .ephem import BurstCubeEphem


class BurstCubeSAA(SAABase):
    """
    Class to calculate BurstCube SAA passages.
    """

    # BurstCube Spacecraft SAA polygon as supplied by BurstCube team.
    insaacons = SAAPolygonConstraint(
        polygon=[
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
    )

    def __init__(self, ephemclass: Type[BurstCubeEphem] = BurstCubeEphem, **kwargs):
        """
        Initialize the SAA class, passing the appropriate ephem class for this mission.
        """
        # Set up the ephemeris class to use
        self.ephemclass = ephemclass

        # Calculate the SAA entries
        super().__init__(**kwargs)
