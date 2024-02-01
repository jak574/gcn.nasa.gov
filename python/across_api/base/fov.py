# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from typing import Optional, Union

import astropy_healpix as ah  # type: ignore
import astropy.units as u  # type: ignore
from astropy.io.fits import FITS_rec  # type: ignore
import numpy as np
from astropy.coordinates import SkyCoord, angular_separation  # type: ignore
from astropy.time import Time  # type: ignore
from .constraints import EarthLimbConstraint
from .common import ACROSSAPIBase
from .ephem import EphemBase


# Some math stuff for calculating the probability inside for circular error
# regions
def normal_pdf(x, standard_deviation):
    """
    Calculate the probability density function (PDF) of a standard normal distribution (mean=0).

    Parameters
    ----------
    x
        The value at which to calculate the PDF.
    standard_deviation
        The standard deviation of the normal distribution.

    Returns
    -------
    pdf
        The probability density at the given x.
    """

    # Calculate the exponent term
    exponent = -(x**2) / (2 * standard_deviation**2)

    # Calculate the PDF using the simplified formula
    pdf = (1 / (standard_deviation * np.sqrt(2 * np.pi))) * np.exp(exponent)

    return pdf


def healpix_map_from_position_error(
    skycoord: SkyCoord, error_radius: u.Quantity, nside=512
) -> np.ndarray:
    """
    For a given sky position and error radius, create a HEALPix map of the
    probability density distribution.

    Parameters
    ----------
    skycoord
        The sky position for which to create the probability density
        distribution.
    error_radius
        The 1 sigma error radius for the sky position.
    nside
        The NSIDE value for the HEALPix map. Default is 512.

    Returns
    -------
    prob
        The probability density distribution HEALPix map.
    """
    # Create HEALPix map
    hp = ah.HEALPix(nside=nside, order="nested")

    # Find RA/Dec for each pixel in HEALPix map
    hpra, hpdec = hp.healpix_to_lonlat(range(ah.nside_to_npix(nside)))

    # Find angular distance of each HEALPix pixel to the skycoord
    distance = angular_separation(hpra, hpdec, skycoord.ra, skycoord.dec).to(u.deg)

    # Create the probability density distribution HEALPix map
    prob = normal_pdf(distance, error_radius).value

    # Normalize it
    prob /= sum(prob)

    return prob


class FOVBase(ACROSSAPIBase):
    ephem: EphemBase
    earth_constraint: EarthLimbConstraint

    def earth_occulted(
        self,
        skycoord: SkyCoord,
        time: Time,
        ephem: EphemBase,
    ) -> Union[bool, np.ndarray]:
        """
        Check if a celestial object is occulted by the Earth.

        Parameters
        ----------
        skycoord: SkyCoord, optional
            SkyCoord object representing the celestial object.
        earth
            SkyCoord object representing the Earth.
        earth_size
            Angular size of the Earth.

        Returns
        -------
        bool or np.ndarray
            True if the celestial object is occulted by the Earth, False otherwise.
        """
        return self.earth_constraint(coord=skycoord, time=time, ephem=ephem)

    def infov(
        self,
        skycoord: SkyCoord,
        time: Time,
        ephem: EphemBase,
    ) -> Union[bool, np.ndarray]:
        """
        Is the target at a given coordinate, inside the given coordinates
        inside the FOV and not Earth occulted. Note that this method only
        checks for Earth occultation, so defines a simple 'all-sky' FOV with no
        other constraints.

        Parameters
        ----------
        skycoord
            SkyCoord object representing the celestial object.
        time
            Time object representing the time of the observation.
        ephem
            Ephemeris object

        Returns
        -------
        bool
            True or False
        """
        # If simple is True or error radius is below a critical value, just
        # treat as a point source
        # Check for Earth occultation
        earth_occultation = self.earth_occulted(
            skycoord=skycoord,
            time=time,
            ephem=ephem,
        )
        return np.logical_not(earth_occultation)

    def infov_circular_error(
        self,
        skycoord: SkyCoord,
        error_radius: u.Quantity,
        time: Time,
        ephem: EphemBase,
        simple: bool = False,
        nside: int = 512,
        point_source_tolerance: u.Quantity = 5 * u.arcmin,
    ) -> Union[bool, float, np.ndarray]:
        """
        Calculate the probability of a celestial object with a circular error
        region being inside the FOV defined by the given parameters. This works
        by creating a HEALPix map of the probability density distribution, and
        then using the `infov_hp` method to calculate the amount of probability
        inside the FOV.

        Parameters
        ----------
        skycoord
            SkyCoord object representing the celestial object.
        time
            Time object representing the time of the observation.
        ephem
            Ephemeris object
        error_radius
            The error radius for the sky position.
        simple
            If True, treat the object as a point source.
        nside
            The NSIDE value for the HEALPix map. Default is 512.
        point_source_tolerance
            The maximum error radius to treat as a point source. Default is
            5 arcmin.

        Returns
        -------
        bool
            True or False
        """
        # Sanity check
        assert skycoord.isscalar, "SkyCoord must be scalar"

        # If simple is True or error radius is below a critical value, just
        # treat as a point source
        if simple or error_radius < point_source_tolerance:
            # Check for Earth occultation
            return self.infov(skycoord=skycoord, time=time, ephem=ephem)

        # Create a HEALPix map of the probability density distribution
        prob = healpix_map_from_position_error(
            skycoord=skycoord, error_radius=error_radius, nside=nside
        )

        return self.infov_hp(
            healpix_loc=prob,
            time=time,
            ephem=ephem,
            healpix_nside=nside,
        )

    def infov_hp(
        self,
        healpix_loc: FITS_rec,
        time: Time,
        ephem: EphemBase,
        healpix_nside: Optional[int] = None,
        healpix_order: str = "NESTED",
    ) -> float:
        """
        Calculates the amount of probability inside the field of view (FOV)
        defined by the given parameters. This works by calculating a SkyCoord
        containing every non-zero probability pixel, uses the `infov` method to
        check which ones are inside the FOV, and then finding the integrated
        probability of the remaining pixels. Note this method makes no attempt
        to deal with pixels that are only partially inside the FOV.

        If `healpix_order` == "NUNIQ", it assumes that `healpix_loc` contains
        a multi-order HEALPix map.

        Parameters
        ----------
        healpix_loc
            An array containing the probability density values for each HEALPix
            pixel.
        healpix_nside
            The NSIDE value of the HEALPix map. If not provided, it will be
            calculated based on the length of healpix_loc.
        healpix_order
            The ordering scheme of the HEALPix map. Default is "NESTED".
        earth
            SkyCoord of the Earth's center in degrees. If provided along with
            earth_size, it will be used to remove Earth occulted pixels from
            the FOV.
        earth_size
            The size of the Earth in degrees.

        Returns
        -------
        float
            The amount of probability inside the FOV.

        """
        # Extract the NSIDE value from the HEALPix map, also level and ipix if
        # this is a MOC map
        if healpix_order == "NUNIQ":
            level, ipix = ah.uniq_to_level_ipix(healpix_loc["UNIQ"])
            uniq_nside = ah.level_to_nside(level)
            healpix_loc = healpix_loc["PROBDENSITY"]
        else:
            nside = ah.npix_to_nside(len(healpix_loc))

        # Find where in HEALPix map the probability is > 0
        nonzero_prob_pixels = np.where(healpix_loc > 0.0)[0]

        # Create a list of RA/Dec coordinates for these pixels
        if healpix_order == "NUNIQ":
            ra, dec = ah.healpix_to_lonlat(
                ipix[nonzero_prob_pixels],
                nside=uniq_nside[nonzero_prob_pixels],  # type: ignore
                order="NESTED",
            )
        else:
            ra, dec = ah.healpix_to_lonlat(
                nonzero_prob_pixels, nside=nside, order=healpix_order
            )

        # Convert these coordinates into a SkyCoord
        skycoord = SkyCoord(ra=ra, dec=dec, unit="deg")

        # Calculate pixel indicies of the all the regions inside of the FOV
        visible_pixels = nonzero_prob_pixels[
            self.infov(skycoord=skycoord, time=time, ephem=ephem)
        ]

        # Calculate the amount of probability inside the FOV
        if healpix_order == "NUNIQ":
            # Calculate probability in FOV by multiplying the probability density by
            # area of each pixel and summing up
            pixarea = ah.nside_to_pixel_area(uniq_nside[visible_pixels])
            return float(round(np.sum(healpix_loc[visible_pixels] * pixarea.value), 5))
        else:
            # Calculate the amount of probability inside the FOV
            return float(round(np.sum(healpix_loc[visible_pixels]), 5))


class AllSkyFOV(FOVBase):
    """
    All sky instrument FOV. This is a simple FOV that is always visible unless
    Earth occulted.
    """

    def __init__(self, **kwargs):
        pass
