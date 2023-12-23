# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from datetime import datetime
from typing import Optional

from cachetools import TTLCache, cached

from ..base.common import ACROSSAPIBase
from ..base.config import set_observatory
from ..base.ephem import EphemBase
from ..base.tle import TLEEntry
from .config import BURSTCUBE
from .tle import TLE


@cached(cache=TTLCache(maxsize=1024, ttl=86400))
@set_observatory(BURSTCUBE)
class Ephem(EphemBase, ACROSSAPIBase):
    """
    Class to generate BurstCube ephemeris. Generate on the fly an ephemeris for Satellite from TLE.

    Parameters
    ----------
    begin : datetime
        Start time of ephemeris search
    end : datetime
        End time of ephemeris search
    stepsize : int
        Step size in seconds for ephemeris calculations
    """

    def __init__(self, begin: datetime, end: datetime, stepsize: int = 60):
        EphemBase.__init__(self)
        # Default values
        self.tle: Optional[TLEEntry] = TLE(begin).tle

        # Parse argument keywords
        self.begin = begin
        self.end = end
        self.stepsize = stepsize

        # Validate and process API call
        if self.validate_get():
            # Perform GET
            self.get()


BurstCubeEphem = Ephem
