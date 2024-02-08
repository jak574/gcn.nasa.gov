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
    prob = np.divide(prob, np.sum(prob))

    return prob


class FOVBase(ACROSSAPIBase):
    ephem: EphemBase
    earth_constraint: EarthLimbConstraint

    def probability_infov(
        self,
        time: Time,
        ephem: EphemBase,
        skycoord: Optional[SkyCoord] = None,
        error_radius: Optional[u.Quantity] = None,
        healpix_loc: Optional[FITS_rec] = None,
    ) -> float:
        """
        For a given sky position and error radius, calculate the probability of
        the sky position being inside the field of view (FOV).

        Parameters
        ----------
        skycoord
            SkyCoord object representing the position of the celestial object.
        error_radius
            The error radius for the sky position. If not given, the `skycoord`
            will be treated as a point source.
        healpix_loc
            HEALPix map of the localization.
        time
            The time of the observation.
        ephem
            Ephemeris object.

        """
        # For a point source
        if skycoord is not None and error_radius is None:
            infov = self.infov(skycoord, time, ephem)
            return 1.0 if infov else 0.0
        # For a circular error region
        if skycoord is not None and error_radius is not None:
            return self.infov_circular_error(
                skycoord=skycoord, error_radius=error_radius, time=time, ephem=ephem
            )
        # For a HEALPix map
        elif healpix_loc is not None:
            return self.infov_healpix_map(
                healpix_loc=healpix_loc, time=time, ephem=ephem
            )

        # We should never get here
        raise AssertionError("No valid arguments provided")

    def infov(
        self,
        skycoord: SkyCoord,
        time: Time,
        ephem: EphemBase,
    ) -> Union[bool, np.ndarray]:
        """
        Is a coordinate or set of coordinates `skycoord` inside the FOV and not
        Earth occulted.

        Note that this method only checks if the given coordinate is Earth
        occulted, so defines a simple 'all-sky' FOV with no other constraints.
        For more complex FOVs, this method should be overridden with one that
        also checks if coordinate is inside the bounds of an instrument's FOV
        for a given spacecraft attitude.

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

        # Check for Earth occultation
        earth_occultation = self.earth_constraint(
            skycoord=skycoord, time=time, ephem=ephem
        )
        return np.logical_not(earth_occultation)

    def infov_circular_error(
        self,
        skycoord: SkyCoord,
        error_radius: u.Quantity,
        time: Time,
        ephem: EphemBase,
        nside: int = 512,
    ) -> float:
        """
        Calculate the probability of a celestial object with a circular error
        region being inside the FOV defined by the given parameters. This works
        by creating a HEALPix map of the probability density distribution, and
        then using the `infov_healpix_map` method to calculate the amount of
        probability inside the FOV.

        The FOV definition is based on the `infov` method, which checks if a
        given coordinate is inside the FOV and not Earth occulted.

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
        nside
            The NSIDE value for the HEALPix map. Default is 512.

        Returns
        -------
        bool
            True or False
        """
        # Sanity check
        assert skycoord.isscalar, "SkyCoord must be scalar"

        # Create a HEALPix map of the probability density distribution
        prob = healpix_map_from_position_error(
            skycoord=skycoord, error_radius=error_radius, nside=nside
        )

        return self.infov_healpix_map(
            healpix_loc=prob,
            time=time,
            ephem=ephem,
        )

    def infov_healpix_map(
        self,
        healpix_loc: FITS_rec,
        time: Time,
        ephem: EphemBase,
        healpix_order: str = "NESTED",
    ) -> float:
        """
        Calculates the amount of probability inside the field of view (FOV)
        defined by the given parameters. This works by calculating a SkyCoord
        containing every non-zero probability pixel, uses the
        `infov` method to check which pixels are inside the FOV,
        and then finding the integrated probability of those pixels.

        Note: This method makes no attempt to deal with pixels that are only
        partially inside the FOV, i.e. Earth occultation is calculated for
        location of the center of each HEALPix pixel.

        If `healpix_order` == "NUNIQ", it assumes that `healpix_loc` contains a
        multi-order HEALPix map, and handles that accordingly.

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
