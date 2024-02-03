# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from functools import cached_property
from typing import List, Optional

import astropy.units as u  # type: ignore
import numpy as np
from .constraints import (
    EarthLimbConstraint,
    MoonConstraint,
    PoleConstraint,
    RamConstraint,
    SAAPolygonConstraint,
    SunConstraint,
)
from astropy.coordinates import SkyCoord  # type: ignore
from astropy.time import Time  # type: ignore

from .common import ACROSSAPIBase
from .ephem import EphemBase
from .schema import VisibilityGetSchema, VisibilitySchema, VisWindow


class VisibilityBase(ACROSSAPIBase):
    """
    Calculate visibility of a given object.


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

    Attributes
    ----------
    ephem
        Ephem object to use for visibility calculations
    saa
        SAA object to use for visibility calculations
    entries
        List of visibility windows
    """

    _schema = VisibilitySchema
    _get_schema = VisibilityGetSchema

    ram_cons: bool
    pole_cons: bool
    sun_cons: bool
    moon_cons: bool
    earth_cons: bool
    saa_cons: bool
    earthoccult: float
    moonoccult: float
    sunoccult: float
    ramsize: float
    sunextra: float
    ramextra: float
    earthextra: float
    moonextra: float
    isat: bool
    saapoly: Optional[list]

    # Constraint definitions
    ram_constraint: Optional[RamConstraint] = None
    pole_constraint: Optional[PoleConstraint] = None
    sun_constraint: Optional[SunConstraint] = None
    moon_constraint: Optional[MoonConstraint] = None
    earth_constraint: Optional[EarthLimbConstraint] = None
    saa_constraint: Optional[SAAPolygonConstraint] = None

    inramcon: np.ndarray
    inpolecon: np.ndarray
    insuncon: np.ndarray
    inmooncon: np.ndarray
    inearthcon: np.ndarray
    insaacon: np.ndarray
    inconstraint: np.ndarray

    entries: List[VisWindow]
    ra: float
    dec: float

    begin: Time
    end: Time
    ephem: EphemBase
    stepsize: u.Quantity

    def __init__(self, begin: Time, end: Time, ra: float, dec: float):
        self.ra = ra
        self.dec = dec
        self.begin = begin
        self.end = end
        self.entries = list()
        self.stepsize = 60 * u.s

        # Set up constraints
        if self.ram_cons:
            self.ram_constraint = RamConstraint(self.ramsize)
        if self.pole_cons:
            self.pole_constraint = PoleConstraint(self.earthoccult + self.earthextra)
        if self.sun_cons:
            self.sun_constraint = SunConstraint(self.sunoccult + self.sunextra)
        if self.moon_cons:
            self.moon_constraint = MoonConstraint(self.moonoccult + self.moonextra)
        if self.earth_cons:
            self.earth_constraint = EarthLimbConstraint(
                self.earthoccult + self.earthextra
            )
        if self.pole_cons:
            self.pole_constraint = PoleConstraint(self.earthoccult + self.earthextra)
        if self.saa_cons and self.saapoly is not None:
            self.saa_constraint = SAAPolygonConstraint(self.saapoly)

        # Parse argument keywords
        if self.validate_get():
            # Perform Query
            self.get()

    def __getitem__(self, i):
        return self.entries[i]

    def __len__(self):
        return len(self.timestamp)

    @cached_property
    def skycoord(self):
        """
        Create array of RA/Dec and vector of these.

        Returns
        -------
        numpy.ndarray
            Array of RA/Dec coordinates.
        """
        return SkyCoord(self.ra * u.deg, self.dec * u.deg)

    def visible(self, t: Time) -> bool:
        """
        For a given time, is the target visible?

        Parameters
        ----------
        t
            Time to check

        Returns
        -------
            True if visible, False if not
        """
        for win in self.entries:
            if t >= win.begin and t <= win.end:
                return True
        return False

    @cached_property
    def ephstart(self) -> Optional[int]:
        """
        Returns the ephemeris index of the beginning time.
        """
        return self.ephem.ephindex(self.begin)

    @cached_property
    def ephstop(self) -> Optional[int]:
        i = self.ephem.ephindex(self.end)
        if i is None:
            return None
        return i + 1

    def get(self) -> bool:
        """
        Query visibility for given parameters.

        Returns
        -------
            True if successful, False otherwise.
        """
        # Reset windows
        self.entries = list()

        # Check everything is kosher, if just run calculation
        if not self.validate_get():
            return False

        # Calculate the times to calculate the visibility
        self.timestamp = self.ephem.timestamp[self.ephstart : self.ephstop]

        # Calculate SAA constraint
        if self.saa_constraint is not None:
            self.insaacon = self.saa_constraint(time=self.timestamp, ephem=self.ephem)  # type: ignore
        else:
            self.insaacon = np.full(len(self.timestamp), False)

        # Calculate Earth constraint
        if self.earth_constraint is not None:
            self.inearthcon = self.earth_constraint(
                coord=self.skycoord, time=self.timestamp, ephem=self.ephem  # type: ignore
            )
        else:
            self.inearthcon = np.full(len(self.timestamp), False)

        # Calculate Moon constraint
        if self.moon_constraint is not None:
            self.inmooncon = self.moon_constraint(
                coord=self.skycoord, time=self.timestamp, ephem=self.ephem  # type: ignore
            )
        else:
            self.inmooncon = np.full(len(self.timestamp), False)

        # Calculate Sun constraint
        if self.sun_constraint is not None:
            self.insuncon = self.sun_constraint(
                coord=self.skycoord, time=self.timestamp, ephem=self.ephem  # type: ignore
            )
        else:
            self.insuncon = np.full(len(self.timestamp), False)

        # Calculate Pole constraint
        if self.pole_constraint is not None:
            self.inpolecon = self.pole_constraint(
                coord=self.skycoord, time=self.timestamp, ephem=self.ephem  # type: ignore
            )
        else:
            self.inpolecon = np.full(len(self.timestamp), False)

        # Calculate Ram constraint
        if self.ram_constraint is not None:
            self.inramcon = self.ram_constraint(
                coord=self.skycoord,
                time=self.timestamp,
                ephem=self.ephem,  #   type: ignore
            )
        else:
            self.inramcon = np.full(len(self.timestamp), False)

        # Calculate combined constraints
        self.inconstraint = (
            self.insuncon
            | self.inmooncon
            | self.inpolecon
            | self.inearthcon
            | self.insaacon
            | self.inramcon
        )

        # Calculate good windows from combined constraints
        self.entries = self.make_windows(self.inconstraint.tolist())

        return True

    def constraint(self, index: int) -> str:
        """
        What kind of constraints are in place at a given time index.

        Parameters
        ----------
        index
            Index of timestamp to check

        Returns
        -------
            String indicating what constraint is in place at given time index
        """
        # Sanity check
        assert self.ephstart is not None
        assert self.ephstop is not None

        # Check if index is out of bounds
        if index == self.ephstart - 1 or index == self.ephstop - 1:
            return "Window"

        # Return what constraint is causing the window to open/close
        if self.inconstraint[index]:
            if self.sun_constraint is not None and self.insuncon[index]:
                return "Sun"
            elif self.moon_constraint is not None and self.inmooncon[index]:
                return "Moon"
            elif self.pole_constraint is not None and self.inpolecon[index]:
                return "Pole"
            elif self.earth_constraint is not None and self.inearthcon[index]:
                return "Earth"
            elif self.saa_constraint is not None and self.insaacon[index]:
                return "SAA"
            else:
                return "Unknown"
        else:
            return "None"

    def make_windows(self, inconstraint: np.ndarray) -> list:
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
        buff: np.ndarray = np.concatenate(
            ([False], np.logical_not(inconstraint), [False])
        )
        begin = np.flatnonzero(~buff[:-1] & buff[1:])
        end = np.flatnonzero(buff[:-1] & ~buff[1:])
        indices = np.column_stack((begin, end - 1))

        # Return as list of VisWindows
        return [
            VisWindow(
                begin=self.ephem.timestamp[i[0]],
                end=self.ephem.timestamp[i[1]],
                initial=self.constraint(i[0] - 1),
                final=self.constraint(i[1] + 1),
            )
            for i in indices
        ]
