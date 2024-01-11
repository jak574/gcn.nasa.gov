# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

import astropy.units as u  # type: ignore
import numpy as np
from astropy.time import Time  # type: ignore
from cachetools import TTLCache, cached

from ..base.common import ACROSSAPIBase
from ..base.config import set_observatory
from ..base.visibility import VisibilityBase
from .config import BURSTCUBE
from .ephem import BurstCubeEphem
from .saa import BurstCubeSAA


@cached(cache=TTLCache(maxsize=128, ttl=86400))
@set_observatory(BURSTCUBE)
class BurstCubeVisibility(VisibilityBase, ACROSSAPIBase):
    """Class to calculate BurstCube visibility."""

    def __init__(
        self,
        ra: float,
        dec: float,
        begin: Time,
        end: Time,
        stepsize: u.Quantity = 60 * u.s,
    ):
        # Parameters
        self.ra = ra
        self.dec = dec
        self.begin = begin
        self.stepsize = stepsize
        self.end = end
        self.isat = False
        # Attributes
        self.entries = []

        # Run GET automatically if parameters are valid, this is a GET only API
        if self.validate_get():
            # Calculate Ephemeris and SAA information. Note calculate this for
            # whole days to avoid having to calculate it multiple times (with caching).
            daybegin = Time(np.floor(self.begin.mjd), format="mjd")
            dayend = Time(np.ceil(self.end.mjd), format="mjd")
            self.ephem = BurstCubeEphem(
                begin=daybegin, end=dayend, stepsize=self.stepsize
            )
            self.saa = BurstCubeSAA(begin=daybegin, end=dayend, ephem=self.ephem)
            self.get()
