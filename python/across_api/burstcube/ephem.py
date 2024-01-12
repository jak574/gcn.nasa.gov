# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

import astropy.units as u  # type: ignore
from astropy.time import Time  # type: ignore
from cachetools import TTLCache, cached

from ..base.common import ACROSSAPIBase
from ..base.config import set_observatory
from ..base.ephem import EphemBase
from .config import BURSTCUBE
from .tle import BurstCubeTLE
from ..scheduling.orbit import TLE


@cached(cache=TTLCache(maxsize=128, ttl=86400))
@set_observatory(BURSTCUBE)
class BurstCubeEphem(EphemBase, ACROSSAPIBase):
    """
    Class to generate BurstCube ephemeris. Generate on the fly an ephemeris for
    Satellite from TLE.
    """

    def __init__(self, begin: Time, end: Time, stepsize: u.Quantity = 60 * u.s):
        self.tle = BurstCubeTLE(begin).tle
        if self.tle is not None:
            self.satellite = TLE(self.tle.io)
            super().__init__(begin=begin, end=end, stepsize=stepsize)
