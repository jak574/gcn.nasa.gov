# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from typing import Union
from astropy.time import Time  # type: ignore
import numpy as np  # type: ignore
from shapely import Polygon, points  # type: ignore

from .ephem import EphemBase


def getslice(time: Time, ephem: EphemBase) -> slice:
    """
    Return a slice for what the part of the ephemeris that we're using.

    Arguments
    ---------
    time
        The time to calculate the slice for
    ephem
        The spacecraft ephemeris

    Returns
    -------
        The slice for the ephemeris
    """
    # If we're just passing a single time, we can just find the index for that
    if time.isscalar:
        # Check that the time is within the ephemeris range, this should never
        # happen as the ephemeris is generated based on this range.
        assert (
            time >= ephem.begin and time <= ephem.end
        ), "Time outside of ephemeris of range"
        # Find the index for the time and return a slice for that index
        index = ephem.ephindex(time)
        return slice(index, index + 1)
    else:
        # Check that the time range is within the ephemeris range, as above.
        assert (
            time[0] >= ephem.begin and time[-1] <= ephem.end
        ), "Time outside of ephemeris of range"

        # Find the indices for the start and end of the time range and return a
        # slice for that range
        return slice(ephem.ephindex(time[0]), ephem.ephindex(time[-1]) + 1)


class SAAPolygonConstraint:
    """
    Polygon based SAA constraint. The SAA is defined by a Shapely Polygon, and
    this constraint will calculate for a given set of times and a given
    ephemeris whether the spacecraft is in that SAA polygon.

    Attributes
    ----------
    polygon
        Shapely Polygon object defining the SAA polygon.

    """

    def __init__(self, polygon: list):
        self.polygon = Polygon(polygon)

    def __call__(self, time: Time, ephem: EphemBase) -> Union[bool, np.ndarray]:
        """
        Return a bool array indicating whether the spacecraft is in constraint
        for a given ephemeris.

        Arguments
        ---------
        time
            The time to calculate the constraint for.
        ephem
            The spacecraft ephemeris, must be precalculated. Note: The
            ephemeris can be calculated for a longer time range than the `time`
            argument, but it must contain the time(s) in the `time` argument.

        Returns
        -------
            Array of booleans for every value in `time` returning True if the
            spacecraft is in the SAA polygon at that time. If `time` is a
            scalar then a single boolean is returned.
        """

        # Find a slice what the part of the ephemeris that we're using
        i = getslice(time, ephem)

        inconstraint = self.polygon.contains(
            points(ephem.longitude[i], ephem.latitude[i])
        )
        # Return the result as True or False, or an array of True/False
        return inconstraint[0] if time.isscalar else inconstraint
