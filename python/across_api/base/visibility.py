# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from functools import cached_property
from typing import List

import astropy.units as u  # type: ignore
import numpy as np
from astropy.coordinates import SkyCoord  # type: ignore
from astropy.time import Time  # type: ignore

from .common import ACROSSAPIBase, round_time
from .ephem import EphemBase
from .saa import SAABase
from .schema import VisibilityGetSchema, VisibilitySchema, VisWindow
from .window import MakeWindowBase


class VisibilityBase(ACROSSAPIBase, MakeWindowBase):
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

    # Constraint definitions
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
    entries: List[VisWindow]
    ra: float
    dec: float

    begin: Time
    end: Time
    saa: SAABase
    ephem: EphemBase
    stepsize: u.Quantity

    def __init__(self, begin: Time, end: Time, ra: float, dec: float):
        self.ra = ra
        self.dec = dec
        self.begin = begin
        self.end = end
        self.entries = list()
        self.stepsize = 60 * u.s

        # Parse argument keywords
        if self.validate_get():
            # Perform Query
            self.get()

    def __getitem__(self, i):
        return self.entries[i]

    def __len__(self):
        return len(self.timestamp)

    @cached_property
    def timestamp(self):
        """
        Create array of timestamps for the visibility period being calculated.

        Returns
        -------
            Array of timestamps.
        """
        return self.ephem.timestamp[self.ephstart : self.ephstop]

    @cached_property
    def inearthcons(self) -> List[bool]:
        """
        Determines if the celestial object is within the satellite Earth
        constraint.

        Returns
        -------
            A list of booleans indicating whether the celestial object is
            within the Earth's constraints.
        """

        self.earthang = self.ephem.earth[self.ephstart : self.ephstop].separation(
            self.skycoord
        )

        earth_cons = self.earthoccult  # type: ignore
        if not self.isat:
            earth_cons = self.earthoccult + self.earthextra  # type: ignore

        return (
            self.earthang
            < earth_cons + self.ephem.earthsize[self.ephstart : self.ephstop]
        )

    @cached_property
    def inramcons(self) -> np.ndarray:
        """
        Calculate Ram constraint (avoidance of direction of motion)

        Returns
        -------
            A boolean array indicating whether each point in the trajectory
            satisfies the ram constraint.
        """
        # calculate the angle between the velocity vector and the RA/Dec vector
        self.ramang = SkyCoord(
            self.ephem.velvec[self.ephstart : self.ephstop]
        ).separation(self.skycoord)

        # calculate the size of the ram constraint
        ram_cons = self.ramsize  # type: ignore
        if not self.isat:
            ram_cons = self.ramsize + self.ramextra  # type: ignore
        # return the constraint
        return self.ramang < ram_cons

    @cached_property
    def inpolecons(self) -> np.ndarray:
        """
        Determine if a source is in pole constraint. Note this is only
        important for spacecraft that have earth limb avoidance constraints
        large enough so that a region around the orbit poles is not visible.

        Returns
        -------
            An array of boolean values indicating whether each source is in
            pole constraint.
        """
        # Determine the size of the pole constraint
        pole_cons = self.ephem.earthsize[self.ephstart : self.ephstop] + (
            self.earthoccult - 90 * u.deg
        )  # type: ignore
        if not self.isat:
            pole_cons += self.earthextra

        # Calculate the angular distance of the source from the North and South poles
        pole_dist = self.ephem.pole[self.ephstart : self.ephstop].separation(
            self.skycoord
        )

        # Create an array of pole constraints
        return np.logical_or(pole_dist < pole_cons, pole_dist > 360 * u.deg - pole_cons)

    @cached_property
    def insuncons(self):
        """
        Calculate Sun constraint

        Returns
        -------
            True if the separation between the sun and the sky coordinates is
            less than the sun constraint, False otherwise.
        """
        self.sunang = self.ephem.sun[self.ephstart : self.ephstop].separation(
            self.skycoord
        )

        sun_cons = self.sunoccult  # type: ignore
        if not self.isat:
            sun_cons = self.sunoccult + self.sunextra  # type: ignore
        return self.sunang < sun_cons

    @cached_property
    def inmooncons(self):
        """
        Calculate Moon constraint.

        Returns
        -------
            True if the separation between the moon and the sky coordinates is
            less than the moon constraint, False otherwise.
        """
        self.moonang = self.ephem.moon[self.ephstart : self.ephstop].separation(
            self.skycoord
        )

        moon_cons = self.moonoccult  # type: ignore
        if not self.isat:
            moon_cons = self.moonoccult + self.moonextra  # type: ignore
        return self.moonang < moon_cons

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

    @cached_property
    def saa_windows(self):
        """
        Calculate SAA windows.

        Returns
        -------
            An array representing the SAA windows.
        """
        return np.array([not s for s in self.insaacons])

    def insaa(self, t: Time) -> bool:
        """
        For a given time, checks if we are in the SAA (South Atlantic Anomaly) as calculated by saa_windows.

        Parameters
        ----------
        t
            The time to check.

        Returns
        -------
            True if the given time is within any of the SAA windows, False otherwise.
        """
        for win in self.saa_windows:
            if t >= win.begin and t <= win.end:
                return True
        return False

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
    def ephstart(self) -> int:
        """
        Returns the ephemeris index of the beginning time.
        """
        return self.ephem.ephindex(self.begin)

    @cached_property
    def ephstop(self) -> int:
        return self.ephem.ephindex(self.end) + 1

    def get(self) -> bool:
        """
        Query visibility for given parameters.

        Returns
        -------
            True if successful, False otherwise.
        """
        # Round begin to the nearest minute
        self.begin = round_time(self.begin, self.stepsize)

        # Reset windows
        self.entries = list()

        # Check everything is kosher, if just run calculation
        if not self.validate_get():
            return False

        # Set up the constraint array
        self.inconstraint = np.zeros(len(self.timestamp), dtype=bool)

        # Calculate SAA constraint
        if self.saa_cons is True:
            self.inconstraint += self.insaacons

        # Calculate Earth constraint
        if self.earth_cons is True:
            self.inconstraint += self.inearthcons

        # Calculate Moon constraint
        if self.moon_cons is True:
            self.inconstraint += self.inmooncons

        # Calculate Sun constraint
        if self.sun_cons is True:
            self.inconstraint += self.insuncons

        # Calculate Pole constraint
        if self.pole_cons is True:
            self.inconstraint += self.inpolecons

        # Calculate Ram constraint
        if self.ram_cons is True:
            self.inconstraint += self.inramcons

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
        # Check if index is out of bounds
        if index == self.ephstart - 1 or index == self.ephstop - 1:
            return "Window"

        # Return what constraint is causing the window to open/close
        if self.inconstraint[index]:
            if self.insuncons[index]:
                return "Sun"
            elif self.inmooncons[index]:
                return "Moon"
            elif self.pole_cons and self.inpolecons[index]:
                return "Pole"
            elif self.inearthcons[index]:
                return "Earth"
            elif self.insaacons[index]:
                return "SAA"
            else:
                return "Unknown"
        else:
            return "None"

    @cached_property
    def insaacons(self) -> np.ndarray:
        """
        Calculate SAA constraint using SAA Polygon

        Returns
        -------
            A list of booleans indicating whether the spacecraft is
            within the SAA polygon.

        """
        return np.array(self.saa.insaacons[self.ephstart : self.ephstop])
