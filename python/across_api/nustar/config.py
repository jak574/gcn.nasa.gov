# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from datetime import datetime

import astropy.units as u  # type: ignore
from astropy.time import Time  # type: ignore

from ..base.config import ConfigSchema

NUSTAR = {
    # Top level details about the mission
    "mission": {
        "name": "Nuclear Spectroscopic Telescope Array",
        "shortname": "NuSTAR",
        "agency": "NASA",
        "type": "Small Explorer",
        "pi": "Fiona Harrison",
        "description": "The NuSTAR (Nuclear Spectroscopic Telescope Array) mission has deployed the first orbiting telescopes to focus light in the high energy X-ray (3 - 79 keV) region of the electromagnetic spectrum. Our view of the universe in this spectral window has been limited because previous orbiting telescopes have not employed true focusing optics, but rather have used coded apertures that have intrinsically high backgrounds and limited sensitivity.",
        "website": "https://www.nustar.caltech.edu",
    },
    # Ephemeris options
    "ephem": {
        "parallax": False,  # Calculate parallax for Moon/Sun
        "apparent": True,  # Use apparent positions for Moon/Sun
        "velocity": False,  # Calculate Velocity of spacecraft (slower)
        "stepsize": 60 * u.s,  # Stepsize
    },
    "instruments": [
        {
            "name": "Focal Plane Mirror Array A",
            "shortname": "FPMA",
            "description": "",
            "website": "https://fermi.gsfc.nasa.gov/science/instruments/table1-2.html",
            "energy_low": (3 * u.keV).value,
            "energy_high": (79 * u.keV).value,
            "fov": {
                "type": "square",
                "area": (10 * u.arcmin**2).to(u.deg**2).value,
                "dimension": None,
                "filename": None,
            },
        },
        {
            "name": "Focal Plane Mirror Array B",
            "shortname": "FPMB",
            "description": "",
            "website": "https://fermi.gsfc.nasa.gov/science/instruments/table1-2.html",
            "energy_low": (3 * u.keV).value,
            "energy_high": (79 * u.keV).value,
            "fov": {
                "type": "square",
                "area": (10 * u.arcmin**2).to(u.deg**2).value,
                "dimension": 10 / 60,  # 10 arcmin on the side
                "filename": None,
            },
        },
    ],
    # Visibility constraint calculation defaults. i.e. what constraints should be considered
    "visibility": {
        # Constraint switches, set to True to calculate this constraint
        "earth_cons": True,  # Calculate Earth Constraint
        "moon_cons": True,  # Calculate Moon Constraint
        "sun_cons": True,  # Calculate Sun Constraint
        "ram_cons": False,  # Calculate Ram Constraint
        "pole_cons": False,  # Calcualte Orbit Pole Constraint
        "saa_cons": False,  # Calculate time in SAA as a constraint
        # Constraint avoidance values
        "earthoccult": 3 * u.deg,  # How many degrees from Earth Limb can you look?
        "moonoccult": 14 * u.deg,  # degrees from center of Moon
        "sunoccult": 50 * u.deg,  # degrees from center of Sun
        "sunextra": 0 * u.deg,  # degrees buffer used for planning purpose
        "earthextra": 0 * u.deg,  # degrees buffer used for planning purpose
        "moonextra": 0 * u.deg,  # degrees buffer used for planning purpose
        "ramsize": 0 * u.deg,  # degrees buffer used for planning purpose
        "ramextra": 0 * u.deg,  # degrees buffer used for planning purpose
    },
    # Information on where to obtain a TLE for this Observatory
    "tle": {
        "tle_bad": 4 * u.day,  # days
        "tle_name": "NuSTAR",
        "tle_norad_id": 38358,
        "tle_concat": "https://nustarsoc.caltech.edu/NuSTAR_Public/NuSTAROperationSite/NuSTAR.tle",
        "tle_url": None,
        # Set the following to NuSTAR's launch date
        "tle_min_epoch": Time(datetime(2012, 6, 13, 0, 0, 0)),
    },
}

# Validate Config Dict
nustar_config = ConfigSchema.model_validate(NUSTAR)
