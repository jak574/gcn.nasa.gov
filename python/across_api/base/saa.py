from functools import cached_property
from typing import Optional

import astropy.units as u  # type: ignore
from astropy.time import Time  # type: ignore
from shapely import Point, Polygon  # type: ignore

from .common import ACROSSAPIBase
from .ephem import EphemBase
from .schema import SAAEntry, SAAGetSchema, SAASchema
from .window import MakeWindowBase


class SAAPolygonBase:
    """
    Simple class to define the Mission SAA Polygon.

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
    Base class for SAA calculations.

    Attributes
    ----------
    begin
        Start time of SAA search
    end
        End time of SAA search
    ephem
        Ephem object to use for SAA calculations
    saa
        SAA Polygon object to use for SAA calculations
    status
        Status of SAA query
    """

    _schema = SAASchema
    _get_schema = SAAGetSchema

    begin: Time
    end: Time

    # Internal things
    saa: SAAPolygonBase
    ephem: EphemBase

    stepsize: u.Quantity
    _insaacons: Optional[list]
    entries: Optional[list]  # type: ignore

    def get(self) -> bool:
        """Calculate list of SAA entries for a given date range.

        Returns
        -------
        bool
            Did the query succeed?
        """
        # Validate Query
        if not self.validate_get():
            return False

        # Calculate SAA windows
        self.entries = self.make_windows(
            [not s for s in self.insaacons], wintype=SAAEntry
        )

        return True

    def insaawindow(self, dttime):
        """
        Check if the given Time falls within any of the SAA windows in list.

        Arguments
        ---------
        dttime : Time
            The Time to check.

        Returns
        -------
        bool
            True if the Time falls within any SAA window, False otherwise.
        """
        return True in [
            True for win in self.entries if dttime >= win.begin and dttime <= win.end
        ]

    @cached_property
    def insaacons(self) -> list:
        """
        Calculate SAA constraint using SAA Polygon

        Returns
        -------
        list
            List of booleans indicating if the spacecraft is in the SAA

        """
        return [
            self.saa.insaa(self.ephem.longitude[i].deg, self.ephem.latitude[i].deg)
            for i in range(len(self.ephem))
        ]
