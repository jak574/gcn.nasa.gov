# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from functools import cached_property
from typing import List, Optional

import astropy.units as u  # type: ignore
from astropy.time import Time  # type: ignore
from shapely import Point, Polygon  # type: ignore

from .common import ACROSSAPIBase
from .ephem import EphemBase
from .schema import SAAEntry, SAAGetSchema, SAASchema
from .window import MakeWindowBase


class SAAPolygonBase:
    """
    Class to define the Mission SAA Polygon.

    Attributes
    ----------
    points
        List of points defining the SAA polygon.
    saapoly
        Shapely Polygon object defining the SAA polygon.

    """

    points: list = [
        (39.0, -30.0),
        (36.0, -26.0),
        (28.0, -21.0),
        (6.0, -12.0),
        (-5.0, -6.0),
        (-21.0, 2.0),
        (-30.0, 3.0),
        (-45.0, 2.0),
        (-60.0, -2.0),
        (-75.0, -7.0),
        (-83.0, -10.0),
        (-87.0, -16.0),
        (-86.0, -23.0),
        (-83.0, -30.0),
    ]

    saapoly: Polygon = Polygon(points)

    def insaa(self, lat: float, lon: float) -> bool:
        return self.saapoly.contains(Point(lat, lon))


class SAABase(ACROSSAPIBase, MakeWindowBase):
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
    """

    _schema = SAASchema
    _get_schema = SAAGetSchema

    begin: Time
    end: Time

    # Internal things
    saa: SAAPolygonBase

    stepsize: u.Quantity
    entries: List[SAAEntry]  # type: ignore

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
        # Parse parameters
        self.begin = begin
        self.end = end
        self.stepsize = stepsize
        if ephem is not None:
            self.ephem = ephem
            # Make sure stepsize matches supplied ephemeris
            self.stepsize = ephem.stepsize

        # If request validates, do a get
        if self.validate_get():
            self.get()

    def get(self) -> bool:
        """
        Calculate list of SAA entries for a given date range.

        Returns
        -------
            Did the query succeed?
        """
        # Calculate SAA windows
        self.entries = self.make_windows(
            [not s for s in self.insaacons], wintype=SAAEntry
        )

        return True

    def insaawindow(self, t):
        """
        Check if the given Time falls within any of the SAA windows in list.

        Arguments
        ---------
        t
            The Time to check.

        Returns
        -------
            True if the Time falls within any SAA window, False otherwise.
        """
        return True in [True for win in self.entries if t >= win.begin and t <= win.end]

    @cached_property
    def insaacons(self) -> list:
        """
        Calculate SAA constraint for each point in the ephemeris using SAA
        Polygon.

        Returns
        -------
        list
            List of booleans indicating if the spacecraft is in the SAA

        """
        return [
            self.saa.insaa(self.ephem.longitude[i].deg, self.ephem.latitude[i].deg)
            for i in range(len(self.ephem))
        ]

    @classmethod
    def insaa(cls, t: Time) -> bool:
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
        return cls.saa.insaa(ephem.longitude[0].deg, ephem.latitude[0].deg)
