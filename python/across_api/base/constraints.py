# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
import astropy.units as u  # type: ignore
from astropy.coordinates import SkyCoord, angular_separation  # type: ignore
from typing import Union, Optional
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
    this constraint will calculate for a given ephemeris whether the spacecraft
    is in that SAA polygon.

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
        ephem
            The spacecraft ephemeris

        Returns
        -------
            Array of booleans for every timetamp in the calculated ephemeris
            returning True if the spacecraft is in the SAA polygon at that time.
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

    def __init__(self, earthoccult):
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

        # Calculate constraint Note: Using the `angular_separation` function
        # here instead of the `SkyCoord` `separation` method is much faster and
        # gives the same result.
        inconstraint = (
            angular_separation(
                ephem.earth[i].ra, ephem.earth[i].dec, coord.ra, coord.dec
            )
            < ephem.earthsize[i] + self.earthoccult
        )
        # Return the result as True or False, or an array of True/False
        return inconstraint[0] if time.isscalar and coord.isscalar else inconstraint



class SunConstraint:
    """
    For a given Sun avoidance angle, is a given coordinate inside this
    constraint?

    Parameters
    ----------
    sunoccult
        The Sun avoidance angle.

    Methods
    -------
    __call__(coord, ephem, earthsize=None)
        Checks if a given coordinate is inside the constraint.

    """

    def __init__(self, sunoccult):
        self.sunoccult = sunoccult

    def __call__(
        self, coord: SkyCoord, time: Time, ephem: EphemBase
    ) -> Union[bool, np.ndarray]:
        """
        Check if a given coordinate is inside the constraint.

        Parameters
        ----------
        coord
            The coordinate to check.
        ephem
            The ephemeris object.

        Returns
        -------
        bool
            `True` if the coordinate is inside the constraint, `False` otherwise.

        """
        # Find a slice what the part of the ephemeris that we're using
        i = getslice(time, ephem)

        #        return ephem.sun[i].separation(coord) < self.sunoccult
        inconstraint = (
            angular_separation(ephem.sun[i].ra, ephem.sun[i].dec, coord.ra, coord.dec)
            < self.sunoccult
        )
        # Return the result as True or False, or an array of True/False
        return inconstraint[0] if time.isscalar else inconstraint


class MoonConstraint:
    """
    For a given Moon avoidance angle, is a given coordinate inside this
    constraint?

    Parameters
    ----------
    moonoccult
        The Moon avoidance angle.

    Methods
    -------
    __call__(coord, ephem, earthsize=None)
        Checks if a given coordinate is inside the constraint.

    """

    def __init__(self, earthoccult):
        self.moonoccult = earthoccult

    def __call__(
        self, coord: SkyCoord, time: Time, ephem: EphemBase
    ) -> Union[bool, np.ndarray]:
        """
        Check if a given coordinate is inside the constraint.

        Parameters
        ----------
        coord
            The coordinate to check.
        ephem
            The ephemeris object.

        Returns
        -------
        bool
            `True` if the coordinate is inside the constraint, `False` otherwise.

        """

        # Find a slice what the part of the ephemeris that we're using
        i = getslice(time, ephem)

        inconstraint = (
            angular_separation(ephem.moon[i].ra, ephem.moon[i].dec, coord.ra, coord.dec)
            < self.moonoccult
        )
        # Return the result as True or False, or an array of True/False
        return inconstraint[0] if time.isscalar else inconstraint


class RamConstraint:
    """
    For a given RAM angle, is a given coordinate inside this constraint?

    Parameters
    ----------
    ram
        The RAM angle.

    Methods
    -------
    __call__(coord, ephem)
        Checks if a given coordinate is inside the constraint.

    """

    def __init__(self, ramsize: u.Quantity):
        self.ramsize = ramsize

    def __call__(
        self, coord: SkyCoord, time: Time, ephem: EphemBase
    ) -> Union[bool, np.ndarray]:
        """
        Check if a given coordinate is inside the constraint.

        Parameters
        ----------
        coord
            The coordinate to check.
        ephem
            The ephemeris object.

        Returns
        -------
        bool
            `True` if the coordinate is inside the constraint, `False` otherwise.

        """

        # Find a slice what the part of the ephemeris that we're using
        i = getslice(time, ephem)

        inconstraint = SkyCoord(ephem.velvec[i]).separation(coord) < self.ramsize

        # Return the result as True or False, or an array of True/False
        return inconstraint[0] if time.isscalar else inconstraint


class InNightConstraint:
    """
    For a given ephemeris, calculate if the spacecraft is in orbit nighttime.
    """

    def __init__(self, earthsize: Optional[u.Quantity] = None):
        self.earthsize = earthsize

    def __call__(self, time: Time, ephem: EphemBase) -> Union[bool, np.ndarray]:
        """
        Is the spacecraft in an Earth eclipse? Defined as when the Sun > 50%
        behind the Earth.

        Returns
        -------
            A boolean array indicating if the spacecraft is in eclipse.
        """
        # Find a slice what the part of the ephemeris that we're using
        i = getslice(time, ephem)

        # return ephem.earth.separation(ephem.sun[i]) < self.earthsize
        inconstraint = (
            angular_separation(
                ephem.sun[i].ra, ephem.sun[i].dec, ephem.earth[i].ra, ephem.earth[i].dec
            )
            < self.earthsize
        )
        # Return the result as True or False, or an array of True/False
        return inconstraint[0] if time.isscalar else inconstraint


class PoleConstraint:
    """
    For a given ephemeris an, calculate if a given coordinate is inside the
    pole constraint. Note that a pole constraint is simply a emergant property
    of the Earth limb constraint. However, given that for some spacecraft (e.g.
    Swift) pole constraints can last for ~7 days, it's useful to be able to
    calculate this for long term visibility.
    """

    def __init__(self, earthoccult: u.Quantity):
        self.earthoccult = earthoccult

    def __call__(
        self, coord: SkyCoord, time: Time, ephem: EphemBase
    ) -> Union[bool, np.ndarray]:
        """
        Is the spacecraft in an Earth eclipse? Defined as when the Sun > 50%
        behind the Earth.

        Returns
        -------
            A boolean array indicating if the spacecraft is in eclipse.
        """
        # Find a slice what the part of the ephemeris that we're using
        i = getslice(time, ephem)

        # Calculate the size of the pole constraint, which is derived from the
        # size of the earth and the earth limb avoidance angle
        pole_cons = ephem.earthsize[i] + (self.earthoccult - 90 * u.deg)

        # Calculate orbit pole vector
        polevec = ephem.posvec[i].cross(ephem.velvec[i])
        pole = SkyCoord(polevec / polevec.norm())

        # Calculate the angular distance of the source from the North and South poles
        pole_dist = pole.separation(coord)

        # Create an array of pole constraints for the south and north orbit poles
        inconstraint = np.logical_or(
            pole_dist < pole_cons, pole_dist > 360 * u.deg - pole_cons
        )

        # Return the result as True or False, or an array of True/False
        return inconstraint[0] if time.isscalar else inconstraint


class InContinousViewingZone:
    """
    Calculate if a target is inside a spacecraft's continuous viewing zone
    (CVZ). CVZ is an area of the sky that a spacecraft can continuously observe
    throughout an orbit without any Earth occultation.
    """

    def __init__(self, earthoccult: u.Quantity):
        self.earthoccult = earthoccult

    def __call__(self, coord: SkyCoord, time: Time, ephem: EphemBase):
        """
        Is the spacecraft in an Earth eclipse? Defined as when the Sun > 50%
        behind the Earth.

        Returns
        -------
            A boolean array indicating if the spacecraft is in eclipse.
        """
        # Find a slice what the part of the ephemeris that we're using
        i = getslice(time, ephem)

        # Calculate the size of the pole constraint, which is derived from the
        # size of the earth and the earth limb avoidance angle
        cvz_size = 90 * u.deg - ephem.earthsize[i] - self.earthoccult

        # Calculate orbit pole vector
        polevec = ephem.posvec[i].cross(ephem.velvec[i])
        pole = SkyCoord(polevec / polevec.norm())

        # Calculate the angular distance of the source from the North and South poles
        pole_dist = pole.separation(coord)

        # Create an array of pole constraints for the south and north orbit poles
        incvz = np.logical_or(pole_dist < cvz_size, pole_dist > 360 * u.deg - cvz_size)

        # Return the result as True or False, or an array of True/False
        return incvz[0] if time.isscalar else incvz
