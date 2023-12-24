# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from cachetools import TTLCache, cached

from ..base.config import set_observatory
from ..base.tle import TLEBase
from ..fermi.config import FERMI


@cached(cache=TTLCache(maxsize=128, ttl=3600))
@set_observatory(FERMI)
class FermiTLE(TLEBase):
    ...


TLE = FermiTLE
