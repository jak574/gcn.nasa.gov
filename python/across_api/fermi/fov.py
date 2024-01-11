# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from typing import Literal, Optional

import astropy.units as u  # type: ignore
import numpy as np
from astropy.time import Time  # type: ignore

from ..base.config import set_observatory
from ..base.fov import FOVCheckBase
from ..fermi.config import FERMI
from .ephem import FermiEphem
from .pointing import FermiPointing
from .schema import FermiFOVCheckGetSchema, FermiFOVCheckSchema


@set_observatory(FERMI)
class FermiFOVCheck(FOVCheckBase):
    """Class to calculate if a given source is in the Fermi FOV at a given time.

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
    earthoccult : bool
        Calculate Earth occultation (default: True)
    instrument : Literal["LAT", "GBM"]
        Instrument to check (default: "GBM")

    Attributes
    ----------
    entries : List[FermiPointing]
        List of FermiPointing entries
    status : JobInfo
        Info about FermiFOVCheck query
    """

    _schema = FermiFOVCheckSchema
    _get_schema = FermiFOVCheckGetSchema

    def __init__(
        self,
        begin: Time,
        end: Time,
        ra: Optional[float] = None,
        dec: Optional[float] = None,
        healpix_loc: Optional[np.ndarray] = None,
        healpix_order: str = "nested",
        stepsize: u.Quantity = 60 * u.s,
        earthoccult: bool = True,
        instrument: Literal["LAT", "GBM"] = "GBM",
    ):
        self.ra = ra
        self.dec = dec
        self.healpix_loc = healpix_loc
        self.healpix_order = healpix_order
        self.begin = begin
        self.end = end
        self.stepsize = stepsize
        self.earthoccult = earthoccult

        self.instrument = instrument
        self.entries = []

        # Validate the input
        if self.validate_get():
            self.get()

    def get(self):
        """Calculate list of FermiPointing entries for a given date range.

        Returns
        -------
        bool
            True
        """
        # Load Pointings into the entries
        self.entries = FermiPointing(
            begin=self.begin, end=self.end, stepsize=self.stepsize
        ).entries

        # Load Ephemeris
        if self.stepsize == 60 * u.s:
            # If this is a 60s ephemeris, then do this as there's probably a cached one
            begin = Time(np.floor(self.begin.mjd), format="mjd")
            end = Time(np.ceil(self.end.mjd), format="mjd")
        else:
            begin = self.begin
            end = self.end
        self.ephem = FermiEphem(begin=begin, end=end, stepsize=self.stepsize)
        return super().get()


# Short hand aliases
FOVCheck = FermiFOVCheck
