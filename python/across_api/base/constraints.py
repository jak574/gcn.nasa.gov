# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from typing import Union
from astropy.time import Time  # type: ignore
from astropy.coordinates import SkyCoord  # type: ignore
import astropy.units as u  # type: ignore
import numpy as np
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

    polygon: Polygon

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


class EarthLimbConstraint:
    """
    For a given Earth limb avoidance angle, is a given coordinate inside this
    constraint?

    Parameters
    ----------
    earthoccult
        The Earth limb avoidance angle.

    Methods
    -------
    __call__(coord, ephem, earthsize=None)
        Checks if a given coordinate is inside the constraint.

    """

    earthoccult: u.Quantity

    def __init__(self, earthoccult: u.Quantity):
        self.earthoccult = earthoccult

    def __call__(
        self,
        coord: SkyCoord,
        time: Time,
        ephem: EphemBase,
    ) -> Union[bool, np.ndarray]:
        """
        Check if a given coordinate is inside the constraint.

        Parameters
        ----------
        coord
            The coordinate to check.
        time
            The time to check.
        ephem
            The ephemeris object.

        Returns
        -------
        bool
            `True` if the coordinate is inside the constraint, `False` otherwise.

        """

        # Find a slice what the part of the ephemeris that we're using
        i = getslice(time, ephem)

        # NOTE: This following gives a correct answer, but it's computationally
        # inefficient.
        #
        # >>> inconstraint = (
        # >>>    ephem.earth[i].separation(coord) < ephem.earthsize[i] + self.earthoccult
        # >>> )
        #
        # The method below is quicker*, but gives a value that's off by a few
        # arcseconds. However for a typical LEO spacecraft the Earth moves by
        # ~4 degrees/minute, and we're calculating ephemerides at 1 minute
        # intervals, so being a few arcseconds off is not making a real
        # difference.
        #
        # *3x faster than above. If we're calculating earth occultation for
        # every pixel in an NSIDE=1024 HEALPix map, this means 1s vs 3s on a M1
        # Mac.
        inconstraint = (
            SkyCoord(ephem.earth[i].ra, ephem.earth[i].dec).separation(coord)
            < ephem.earthsize[i] + self.earthoccult
        )

        # Return the result as True or False, or an array of True/False
        return inconstraint[0] if time.isscalar and coord.isscalar else inconstraint
