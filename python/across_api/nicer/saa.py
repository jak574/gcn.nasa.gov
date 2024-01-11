# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from datetime import datetime
from typing import Optional

from shapely.geometry import Polygon  # type: ignore

from ..base.config import set_observatory
from ..base.saa import SAABase, SAAGetSchema, SAAPolygonBase, SAASchema
from .config import NICER
from .ephem import NICEREphem


class NICERSAAPolygon(SAAPolygonBase):
    """Class to define the NICER SAA polygon.

    Attributes
    ----------
    points : list
        List of points defining the SAA polygon.
    saapoly : Polygon
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


@set_observatory(NICER)
class NICERSAA(SAABase):
    """Class to calculate NICER SAA entries.

    Parameters
    ----------
    begin : datetime
        Start time of SAA search
    end : datetime
        End time of SAA search
    ephem : Optional[NICEREphem]
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
    saa = NICERSAAPolygon()
    ephem: NICEREphem
    begin: datetime
    end: datetime
    stepsize: int

    def __init__(
        self,
        begin: datetime,
        end: datetime,
        ephem: Optional[NICEREphem] = None,
        stepsize: int = 60,
    ):
        # Attributes

        self._insaacons: Optional[list] = None
        self.entries = None

        # Parameters
        self.begin = begin
        self.end = end
        if ephem is None:
            self.ephem = NICEREphem(begin=begin, end=end, stepsize=stepsize)
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
        ephem = NICEREphem(begin=dttime, end=dttime)  # type: ignore
        return cls.saa.insaa(ephem.longitude[0], ephem.latitude[0])


# Class alias
SAA = NICERSAA
