# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

import re
from typing import Union

import astropy.units as u  # type: ignore
import numpy as np
import requests
from astropy.io import fits  # type: ignore
from astropy.time import Time  # type: ignore
from fastapi import HTTPException

from ..base.config import set_observatory
from ..base.pointing import PointingBase
from ..base.schema import PointSchema
from .config import FERMI


def time_from_year_and_day(year: int, day_of_year: int) -> Time:
    start_date = Time(f"{year}-01-01")  # Start with the first day of the given year
    result_date = start_date + (day_of_year - 1) * u.day
    # Subtract 1 since day_of_year is 1-indexed
    return result_date


def fermi_met_to_time(met: float) -> Time:
    return Time("2001-01-01") + met * u.s


def time_to_fermi_met(dt: Time) -> float:
    return dt.unix - Time("2001-01-01").unix


def latestfermi(starttime: Time) -> Union[str, bool]:
    """Fetch the most relevant Fermi FT2 file from their website"""

    tcedir = "http://fermi.gsfc.nasa.gov/ssc/resources/timeline/ft2/files/"
    sort = "?C=M;O=A"

    req = requests.get(tcedir + sort)
    if req.status_code == 200:
        tcehtml = req.text.splitlines()
        filename = ""
        for line in tcehtml:
            x = re.sub("<.*?>", " ", line).strip().split()
            if len(x) > 0:
                if x[0][0:5] == "FERMI":
                    vals = x[0].split("_")
                    startyear = int(vals[4][0:4])
                    startday = int(vals[4][4:7])
                    endyear = int(vals[5][0:4])
                    endday = int(vals[5][4:7])
                    afststart = time_from_year_and_day(startyear, startday)
                    afstend = time_from_year_and_day(endyear, endday)
                    backupafst = x[0]
                    if afststart <= starttime <= afstend:
                        filename = x[0]
        if filename == "":
            return tcedir + backupafst
        else:
            return tcedir + filename
    return False


@set_observatory(FERMI)
class FermiPointing(PointingBase):
    def __init__(self, begin: Time, end: Time, stepsize: u.Quantity = 60 * u.s):
        self.begin = begin
        self.end = end
        self.stepsize = stepsize
        self.entries = []
        self._times: list = []

        if self._get_schema.model_validate(self):
            self.get()

    @property
    def times(self) -> list:
        return self._times

    def get(self) -> bool:
        """Calculate list of spacecraft pointings for a given date range.

        Returns
        -------
        bool
            True
        """

        # Load Fermi FT2 file
        ft2file = latestfermi(self.begin)
        if ft2file is None:
            raise HTTPException(status_code=404, detail="No Fermi FT2 file found")

        self.hdu = fits.open(ft2file)

        # Calculate where in the FT2 file the period of interest lies
        startmet = time_to_fermi_met(self.begin)
        stopmet = time_to_fermi_met(self.end)
        startindex = np.where(self.hdu[1].data["START"] >= startmet)[0][0]
        stopindex = np.where(self.hdu[1].data["STOP"] <= stopmet)[0][-1]

        # Create the list of FermiPoints
        for i in range(startindex, stopindex):
            t = fermi_met_to_time(self.hdu[1].data["START"][i])
            self.times.append(t)
            ra = self.hdu[1].data["RA_SCZ"][i]
            dec = self.hdu[1].data["DEC_SCZ"][i]
            self.entries.append(
                PointSchema(timestamp=t, ra=ra, dec=dec, observing=True)
            )

        # Set the stepsize, should be 60s for Fermi FT2 files
        self.stepsize = self.entries[1].timestamp - self.entries[0].timestamp

        return True
