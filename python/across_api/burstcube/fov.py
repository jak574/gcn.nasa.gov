# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.


from typing import Optional

import astropy.units as u  # type: ignore
import numpy as np
from astropy.time import Time  # type: ignore

from ..base.config import set_observatory
from ..base.fov import FOVCheckBase
from ..burstcube.config import BURSTCUBE
from .ephem import BurstCubeEphem
from .pointing import BurstCubePointing
from .schema import BurstCubeFOVCheckGetSchema, BurstCubeFOVCheckSchema


@set_observatory(BURSTCUBE)
class BurstCubeFOVCheck(FOVCheckBase):
    """Class to calculate if a given source is in the BurstCube FOV at a given time.

    Parameters
    ----------
    ra : float
        Right Ascension in decimal degrees
    dec : float
        Declination in decimal degrees
    begin : Time
        Start time of visibility search
    end : Time
        End time of visibility search
    stepsize : int
        Step size in seconds for visibility calculations
    earthoccult : bool
        Calculate Earth occultation (default: True)

    Attributes
    ----------
    entries : List[BurstCubePointing]
        List of BurstCubePointing entries
    status : JobInfo
        Info about BurstCubeFOVCheck query
    """

    _schema = BurstCubeFOVCheckSchema
    _get_schema = BurstCubeFOVCheckGetSchema

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
    ):
        self.ra = ra
        self.dec = dec
        self.healpix_loc = healpix_loc
        self.healpix_order = healpix_order
        self.begin = begin
        self.end = end
        self.stepsize = stepsize
        self.earthoccult = earthoccult

        self.instrument = "BurstCube"
        self.entries = []

        # Validate the input
        if self.validate_get():
            self.get()

    def get(self):
        """Calculate list of BurstCubePointing entries for a given date range.

        Returns
        -------
        bool
            True
        """
        # Load Pointings into the entries
        self.entries = BurstCubePointing(
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
        self.ephem = BurstCubeEphem(begin=begin, end=end, stepsize=self.stepsize)
        return super().get()


# Short hand aliases
FOVCheck = BurstCubeFOVCheck
