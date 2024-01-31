# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from typing import Type

from .constraints import swift_saa_constraint
from ..base.saa import SAABase
from .ephem import SwiftEphem


class SwiftSAA(SAABase):
    """
    Class to calculate Swift SAA passages.
    """

    # Swift Spacecraft SAA polygon as supplied by Swift team.
    insaacons = swift_saa_constraint

    def __init__(self, ephemclass: Type[SwiftEphem] = SwiftEphem, **kwargs):
        """
        Initialize the SAA class, passing the appropriate ephem class for this mission.
        """
        # Set up the ephemeris class to use
        self.ephemclass = ephemclass

        # Calculate the SAA entries
        super().__init__(**kwargs)
