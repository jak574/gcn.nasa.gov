# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from datetime import datetime
from typing import Optional

import astropy.units as u  # type: ignore
from shapely.geometry import Polygon  # type: ignore

from ..base.config import set_observatory
from ..base.saa import SAABase, SAAGetSchema, SAAPolygonBase, SAASchema
from .config import FERMI
from .ephem import FermiEphem


class FermiSAAPolygon(SAAPolygonBase):
    """Class to define the Fermi SAA polygon.

    Attributes
    ----------
    points : list
        List of points defining the SAA polygon.
    saapoly : Polygon
        Shapely Polygon object defining the SAA polygon.
    """

    # SAA polygon for Fermi from here:
    # https://fermi.gsfc.nasa.gov/ssc/data/analysis/software/aux/L_SAA_2008198.03
    points: list = [
        (33.900000, -30.000000),
        (24.500000, -22.600000),
        (-18.600000, -2.500000),
        (-25.700000, -5.200000),
        (-36.000000, -5.200000),
        (-42.000000, -4.600000),
        (-58.800000, -0.700000),
        (-93.100000, -8.600000),
        (-97.500000, -9.900000),
        (-98.500000, -12.500000),
        (-92.100000, -21.700000),
        (-86.100000, -30.000000),
    ]

    saapoly: Polygon = Polygon(points)


@set_observatory(FERMI)
class FermiSAA(SAABase):
    """Class to calculate Fermi SAA entries.

    Parameters
    ----------
    begin : datetime
        Start time of SAA search
    end : datetime
        End time of SAA search
    ephem : Optional[Ephem]
        Ephem object to use for SAA calculations
    stepsize : int
        Step size in seconds for SAA calculations

    Attributes
    ----------
    entries : list
        List of SAA entries
    status : JobInfo
        Status of SAA query
    """

    _schema = SAASchema
    _get_schema = SAAGetSchema

    # Internal things
    saa = FermiSAAPolygon()
    ephem: FermiEphem
    begin: datetime
    end: datetime
    stepsize: u.Quantity

    def __init__(
        self,
        begin: datetime,
        end: datetime,
        ephem: Optional[FermiEphem] = None,
        stepsize: u.Quantity = 60 * u.s,
    ):
        # Attributes

        self._insaacons: Optional[list] = None
        self.entries = None

        # Parameters
        self.begin = begin
        self.end = end
        if ephem is None:
            self.ephem = FermiEphem(begin=begin, end=end, stepsize=stepsize)
            self.stepsize = stepsize
        else:
            self.ephem = ephem
            # Make sure stepsize matches supplied ephemeris
            self.stepsize = ephem.stepsize

        # If request validates, query
        if self.validate_get():
            self.get()

    @classmethod
    def insaa(cls, dttime: datetime) -> bool:
        """
        For a given datetime, are we in the SAA?

        Parameters
        ----------
        dttime : datetime
            Time at which to calculate if we're in SAA

        Returns
        -------
        bool
            True if we're in the SAA, False otherwise
        """
        # Calculate an ephemeris for the exact time requested
        ephem = FermiEphem(begin=dttime, end=dttime)  # type: ignore
        return cls.saa.insaa(ephem.longitude[0].deg, ephem.latitude[0].deg)


# Class alias
SAA = FermiSAA
