import re
from datetime import datetime, timedelta
from typing import Union

import numpy as np
import requests
from astropy.io import fits  # type: ignore
from fastapi import HTTPException

from ..base.config import set_observatory
from ..base.pointing import PointingBase
from .config import FERMI
from .schema import FermiPoint, FermiPointingGetSchema, FermiPointingSchema


def datetime_from_year_and_day(year: int, day_of_year: int) -> datetime:
    start_date = datetime(year, 1, 1)  # Start with the first day of the given year
    result_date = start_date + timedelta(
        days=day_of_year - 1
    )  # Subtract 1 since day_of_year is 1-indexed
    return result_date


def fermi_met_to_datetime(met: float) -> datetime:
    return datetime(2001, 1, 1) + timedelta(seconds=met)


def datetime_to_fermi_met(dt: datetime) -> float:
    return dt.timestamp() - datetime(2001, 1, 1).timestamp()


def latestfermi(starttime: datetime) -> Union[str, bool]:
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
                    afststart = datetime_from_year_and_day(startyear, startday)
                    afstend = datetime_from_year_and_day(endyear, endday)
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
    _schema = FermiPointingSchema
    _get_schema = FermiPointingGetSchema

    def __init__(self, begin: datetime, end: datetime, stepsize: int = 60):
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
        startmet = datetime_to_fermi_met(self.begin)
        stopmet = datetime_to_fermi_met(self.end)
        startindex = np.where(self.hdu[1].data["START"] >= startmet)[0][0]
        stopindex = np.where(self.hdu[1].data["STOP"] <= stopmet)[0][-1]

        # Create the list of FermiPoints
        for i in range(startindex, stopindex):
            t = fermi_met_to_datetime(self.hdu[1].data["START"][i])
            self.times.append(t)
            ra = self.hdu[1].data["RA_SCZ"][i]
            dec = self.hdu[1].data["DEC_SCZ"][i]
            self.entries.append(FermiPoint(timestamp=t, ra=ra, dec=dec, observing=True))

        # Set the stepsize, should be 60s for Fermi FT2 files
        self.stepsize = int(
            (self.entries[1].timestamp - self.entries[0].timestamp).total_seconds()
        )

        return True


# Short hand aliases
Pointing = FermiPointing
