from datetime import datetime

import astropy.units as u  # type: ignore
import numpy as np
from astropy.time import Time  # type: ignore

from ..base.config import ConfigSchema

NICER = {
    # Top level details about the mission
    "mission": {
        "name": "Neutron star Interior Composition ExploreR",
        "shortname": "NICER",
        "agency": "NASA",
        "type": "Astrophysics Mission of Opportunity",
        "pi": "Keith Gendreau",
        "description": "Astrophysics on the International Space Station - Understanding ultra-dense matter through soft X-ray timing",
        "website": "https://heasarc.gsfc.nasa.gov/docs/nicer/nicer_about.html",
    },
    "instruments": [
        {
            "name": "X-ray Timing Instrument",
            "shortname": "XTI",
            "description": "X-ray (0.2-12 keV) 'concentrator' optics and silicon-drift detectors. GPS position and absolute time reference to better than 300 ns.",
            "website": "https://heasarc.gsfc.nasa.gov/docs/nicer/nicer_about.html",
            "energy_low": (0.2 * u.keV).value,
            "energy_high": (12 * u.keV).value,
            "fov": {
                "type": "circular",
                "area": ((5 / 60 / 2) ** 2 * np.pi * u.deg**2).value,
                "dimension": 5 / 60 / 2,  # 5' diameter = 2.5' radius
                "filename": None,
            },
        }
    ],
    # Ephemeris options
    "ephem": {
        "parallax": False,  # Calculate parallax for Moon/Sun
        "apparent": True,  # Use apparent positions for Moon/Sun
        "velocity": False,  # Calculate Velocity of spacecraft (slower)
        "stepsize": 60 * u.s,  # Stepsize
    },
    # Visibility constraint calculation defaults. i.e. what constraints should be considered
    "visibility": {
        # Constraint switches, set to True to calculate this constraint
        "earth_cons": True,  # Calculate Earth Constraint
        "moon_cons": False,  # Calculate Moon Constraint
        "sun_cons": False,  # Calculate Sun Constraint
        "ram_cons": False,  # Calculate Ram Constraint
        "pole_cons": False,  # Calcualte Orbit Pole Constraint
        "saa_cons": True,  # Calculate time in SAA as a constraint
        # Constraint avoidance values
        "earthoccult": 0 * u.deg,  # How many degrees from Earth Limb can you look?
        "moonoccult": 0 * u.deg,  # degrees from center of Moon
        "sunoccult": 0 * u.deg,  # degrees from center of Sun
        "sunextra": 0 * u.deg,  # degrees buffer used for planning purpose
        "earthextra": 0 * u.deg,  # degrees buffer used for planning purpose
        "moonextra": 0 * u.deg,  # degrees buffer used for planning purpose
        "ramsize": 0 * u.deg,  # degrees buffer used for planning purpose
        "ramextra": 0 * u.deg,  # degrees buffer used for planning purpose
    },
    # Information on where to obtain a TLE for this Observatory
    "tle": {
        "tle_bad": 4 * u.day,  # days
        "tle_name": "ISS (ZARYA)",
        "tle_norad_id": 25544,
        "tle_concat": None,
        "tle_url": "https://celestrak.org/NORAD/elements/gp.php?INTDES=1998-067",
        # Set the following to the NICER launch date
        "tle_min_epoch": Time(datetime(2017, 6, 14, 0, 0, 0)),
    },
}

# Validate Config Dict
nicer_config = ConfigSchema.model_validate(NICER)
