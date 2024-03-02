# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from typing import Optional
import astropy.units as u  # type: ignore
from astropy.time import Time  # type: ignore
from cachetools import TTLCache, cached

from ..base.schema import TLEEntry
from ..base.common import ACROSSAPIBase
from ..base.ephem import EphemBase
from ..burstcube.tle import BurstCubeTLE


@cached(cache=TTLCache(maxsize=128, ttl=86400))
class BurstCubeEphem(EphemBase, ACROSSAPIBase):
    """
    Class to generate BurstCube ephemeris. Generate on the fly an ephemeris for
    Satellite from TLE.
    """

    # Configuration options
    earth_radius = 70 * u.deg  # Fix 70 degree Earth radius

    async def get(self):
        tle = BurstCubeTLE(self.begin)
        await tle.get()
        self.tle = tle.tle

        return await super().get()
