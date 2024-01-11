from datetime import datetime

import astropy.units as u  # type: ignore
import numpy as np  # type: ignore
from astropy.time import Time  # type: ignore

from ..base.config import ConfigSchema

FERMI = {
    # Top level details about the mission
    "mission": {
        "name": "Fermi Gamma-Ray Space Telescope",
        "shortname": "Fermi",
        "agency": "NASA",
        "type": "Explorer",
        "pi": "",
        "description": "The Fermi Gamma-ray Space Telescope, formerly GLAST, is opening this high-energy world to exploration and helping us answer these questions. With Fermi, astronomers at long last have a superior tool to study how black holes, notorious for pulling matter in, can accelerate jets of gas outward at fantastic speeds. Physicists are able to study subatomic particles at energies far greater than those seen in ground-based particle accelerators. And cosmologists are gaining valuable information about the birth and early evolution of the Universe.",
        "website": "https://fermi.gsfc.nasa.gov",
    },
    "instruments": [
        {
            "name": "Gamma-ray Burst Monitor",
            "shortname": "GBM",
            "description": "",
            "website": "https://fermi.gsfc.nasa.gov/science/instruments/table1-2.html",
            "energy_low": (10 * u.keV).value,
            "energy_high": (25 * u.MeV).to(u.keV).value,
            "fov": {
                "type": "all-sky",
                "area": (4 * np.pi * u.sr).to(u.deg**2).value,
                "dimension": None,
                "filename": None,
            },
        },
        {
            "name": "Large Area Telescope",
            "shortname": "LAT",
            "description": "",
            "website": "https://fermi.gsfc.nasa.gov/science/instruments/table1-1.html",
            "energy_low": (20 * u.MeV).to(u.keV).value,
            "energy_high": (300 * u.GeV).to(u.keV).value,
            "fov": {
                "type": "circular",
                "area": (2.4 * u.sr).to(u.deg**2).value,
                "dimension": np.sqrt(
                    (2 * u.sr).to(u.deg**2).value,
                ),  # 5' diameter = 2.5' radius
                "filename": None,
            },
        },
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
        "earthoccult": 3 * u.deg,  # How many degrees from Earth Limb can you look?
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
        "tle_name": "FGRST (GLAST)",
        "tle_norad_id": 33053,
        "tle_concat": None,
        "tle_url": "http://celestrak.org/NORAD/elements/gp.php?INTDES=2008-029",
        "tle_min_epoch": Time(datetime(2008, 6, 1)),
    },
}

# Validate config dict
fermi_config = ConfigSchema.model_validate(FERMI)
