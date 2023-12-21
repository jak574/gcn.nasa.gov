from datetime import datetime
from typing import Optional

from ..base.common import ACROSSAPIBase
from ..base.config import set_observatory
from ..base.ephem import EphemBase, EphemSchema
from ..base.schema import JobInfo
from ..base.tle import TLEEntry
from .config import SWIFT
from .tle import TLE


@set_observatory(SWIFT)
class Ephem(EphemBase, ACROSSAPIBase):
    """
    Class to generate Swift ephemeris. Generate on the fly an ephemeris for Satellite from TLE.

    Parameters
    ----------
    begin
        Start time of ephemeris search
    end
        End time of ephemeris search
    stepsize
        Step size in seconds for ephemeris calculations

    Attributes
    ----------
    datetimes
        List of datetimes for ephemeris points
    posvec
        List of S/C position vectors in km
    lat
        List of S/C latitude (degrees)
    long
        List of S/C longitude (degrees)
    velra
        List of Ra of the direction of motion (degrees)
    veldec:
        List of Dec of the direction of motion (degrees)
    beta
        List of Beta Angle of orbit
    sunpos
        List of RA/Dec of the Sun
    moonpos
        List of RA/Dec of the Moon
    sunvec
        List of vectors to the Sun from the center of the Earth
    moonvec
        List of vectors to the Moon from the center of the Earth
    ineclipse
        List of booleans indicating if the spacecraft is in eclipse
    status
        Info about the ephemeris query
    """

    _schema = EphemSchema
    # _arg_schema: EphemArgSchema = EphemArgSchema

    def __init__(self, begin: datetime, end: datetime, stepsize: int = 60):
        EphemBase.__init__(self)
        # Default values
        self.status = JobInfo()
        self.tle: Optional[TLEEntry] = TLE(begin).get()

        # Parse argument keywords
        self.begin = begin
        self.end = end
        self.stepsize = stepsize

        # If arguments are valid, run the GET automatically as this is a GET only API
        if self.validate_get():
            self.get()


SwiftEphem = Ephem
