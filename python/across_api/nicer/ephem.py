# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

import astropy.units as u  # type: ignore
from astropy.time import Time  # type: ignore
from cachetools import TTLCache, cached

from ..base.common import ACROSSAPIBase
from ..base.config import set_observatory
from ..base.ephem import EphemBase
from .config import NICER
from .tle import NICERTLE


@cached(cache=TTLCache(maxsize=128, ttl=86400))
@set_observatory(NICER)
class NICEREphem(EphemBase, ACROSSAPIBase):
    """
    Class to generate NICER ephemeris. Generate on the fly an ephemeris for
    Satellite from TLE.
    """

    def __init__(self, begin: Time, end: Time, stepsize: u.Quantity = 60 * u.s):
        self.tle = NICERTLE(begin).tle
        super().__init__(begin=begin, end=end, stepsize=stepsize)
