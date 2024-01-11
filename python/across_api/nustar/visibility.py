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
from .config import NUSTAR
from .ephem import NuSTAREphem
from .saa import NuSTARSAA


@cached(cache=TTLCache(maxsize=128, ttl=86400))
@set_observatory(NUSTAR)
class NuSTARVisibility(VisibilityBase, ACROSSAPIBase):
    """Class to calculate NuSTAR visibility.

    Parameters
    ----------
    ra : float
        Right Ascension in decimal degrees
    dec : float
        Declination in decimal degrees
    begin : datetime
        Start time of visibility search
    end : datetime
        End time of visibility search
    stepsize : int
        Step size in seconds for visibility calculations
    """

    # Schema for API class
    _schema = VisibilitySchema
    _get_schema = VisibilityGetSchema

    # Type hints
    username: str
    begin: datetime
    stepsize: int
    length: float
    end: datetime
    isat: bool

    # Attributes
    entries: List[VisWindow]

    # Internal parameters
    _ephem: Ephem
    saa: SAA

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
            # Calculate Ephemeris and SAA information.
            daybegin = datetime.combine(self.begin.date(), time())
            dayend = datetime.combine(self.end.date(), time()) + timedelta(days=1)
            self.ephem = Ephem(begin=daybegin, end=dayend, stepsize=self.stepsize)
            self.saa = SAA(begin=daybegin, end=dayend, ephem=self.ephem)
            self.get()
