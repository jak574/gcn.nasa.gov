# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.


from typing import List, Optional, Type, Union

import astropy.units as u  # type: ignore
from astropy.time import Time  # type: ignore

from .common import ACROSSAPIBase, ceil_time, floor_time, round_time
from .constraints import SAAPolygonConstraint
from .ephem import EphemBase
from .schema import SAAEntry, SAAGetSchema, SAASchema
import numpy as np


class SAABase(ACROSSAPIBase):
    """
    Class for SAA calculations.

    Parameters
    ----------
    begin
        Start time of SAA search
    end
        End time of SAA search
    ephem
        Ephem object to use for SAA calculations (optional, calculated if not
        provided)
    stepsize
        Step size for SAA calculations

    Attributes
    ----------
    saa
        SAA Polygon object to use for SAA calculations
    ephem
        Ephem object to use for SAA calculations
    entries
        List of SAA entries
    status
        Status of SAA query
    insaacons
        SAA constraint class to use for SAA calculations
    """

    _schema = SAASchema
    _get_schema = SAAGetSchema

    begin: Time
    end: Time

    # Constraint class to use for SAA calculations
    insaacons: SAAPolygonConstraint

    stepsize: u.Quantity
    entries: List[SAAEntry]  # type: ignore
    ephemclass: Type[EphemBase]

    def __init__(
        self,
        begin: Time,
        end: Time,
        ephem: Optional[EphemBase] = None,
        stepsize: u.Quantity = 60 * u.s,
    ):
        """
        Initialize the SAA class.
        """
        # Round start and end times to stepsize resolution
        self.begin = round_time(begin, stepsize)
        self.end = round_time(end, stepsize)
        self.stepsize = stepsize

        # Instantiate the ephem class here if not passed as an argument. By
        # default we'll calculate ephem for a whole day, to aide with caching.
        if ephem is None:
            ephem = self.ephemclass(
                begin=floor_time(self.begin, 1 * u.day),
                end=ceil_time(self.end, 1 * u.day),
                stepsize=self.stepsize,
            )
        else:
            # Make sure stepsize matches supplied ephemeris
            self.stepsize = ephem.stepsize
        self.ephem = ephem

        # If request validates, do a get
        if self.validate_get():
            self.get()

    def get(self) -> Union[bool, np.ndarray]:
        """
        Calculate list of SAA entries for a given date range.

        Returns
        -------
            Did the query succeed?
        """
        # Determine the times to calculate the SAA
        steps = int((self.end - self.begin).to(u.s) / (self.stepsize.to(u.s)) + 1)
        self.timestamp = Time(np.linspace(self.begin, self.end, steps))

        # Calculate SAA windows
        self.entries = self.saa_windows(
            self.insaacons(time=self.timestamp, ephem=self.ephem),  # type: ignore
        )

        return True

    @classmethod
    def insaa(cls, t: Time) -> Union[bool, np.ndarray]:
        """
        For a given time, are we in the SAA?

        Parameters
        ----------
        dttime
            Time at which to calculate if we're in SAA

        Returns
        -------
            True if we're in the SAA, False otherwise
        """
        # Calculate an ephemeris for the exact time requested
        ephem = cls.ephemclass(begin=t, end=t, stepsize=1e-6 * u.s)  # type: ignore
        return cls.insaacons(time=t, ephem=ephem)

    def saa_windows(self, insaa: np.ndarray) -> list:
        """
        Record SAAEntry from array of booleans and timestamps

        Parameters
        ----------
        inconstraint : list
            List of booleans indicating if the spacecraft is in the SAA
        wintype : VisWindow
            Type of window to create (default: VisWindow)

        Returns
        -------
        list
            List of SAAEntry objects
        """
        # Find the start and end of the SAA windows
        buff = np.concatenate(([False], insaa.tolist(), [False]))
        begin = np.flatnonzero(~buff[:-1] & buff[1:])
        end = np.flatnonzero(buff[:-1] & ~buff[1:])
        indices = np.column_stack((begin, end - 1))
        windows = self.timestamp[indices]

        # Return as array of SAAEntry objects
        return [SAAEntry(begin=win[0], end=win[1]) for win in windows]
