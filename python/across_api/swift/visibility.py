# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

import astropy.units as u  # type: ignore
from astropy.time import Time  # type: ignore
from cachetools import TTLCache, cached

from ..base.common import ACROSSAPIBase
from ..base.config import set_observatory
from ..base.visibility import VisibilityBase
from .config import SWIFT
from .ephem import Ephem
from .saa import SAA
from datetime import datetime, time, timedelta

@cached(cache=TTLCache(maxsize=128, ttl=86400))
@set_observatory(SWIFT)
class SwiftVisibility(VisibilityBase, ACROSSAPIBase):
    """Class to calculate Swift visibility.

    Parameters
    ----------
    ra
        Right Ascension in decimal degrees
    dec
        Declination in decimal degrees
    begin
        Start time of visibility search
    end
        End time of visibility search
    stepsize
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
