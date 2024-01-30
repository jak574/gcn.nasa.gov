# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from typing import Type

from ..base.constraints import SAAPolygonConstraint  # type: ignore
from ..base.saa import SAABase
from .ephem import SwiftEphem


class SwiftSAA(SAABase):
    """
    Class to calculate Swift SAA passages.
    """

    # Swift Spacecraft SAA polygon as supplied by Swift team.
    insaacons = SAAPolygonConstraint(
        polygon=[
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
    )

    def __init__(self, ephemclass: Type[SwiftEphem] = SwiftEphem, **kwargs):
        """
        Initialize the SAA class, passing the appropriate ephem class for this mission.
        """
        # Set up the ephemeris class to use
        self.ephemclass = ephemclass

        # Calculate the SAA entries
        super().__init__(**kwargs)
