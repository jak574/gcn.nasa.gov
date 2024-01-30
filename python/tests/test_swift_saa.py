# Perform an SwiftEphem API call


import numpy as np
from astropy.time import Time  # type: ignore
import astropy.units as u  # type: ignore
from across_api.swift.ephem import SwiftEphem  # type: ignore
from across_api.swift.tle import SwiftTLE  # type: ignore
from across_api.base.schema import TLEEntry
from across_api.swift.saa import SwiftSAA

# Define a TLE by hand
satname = "SWIFT"
tle1 = "1 28485U 04047A   24029.43721350  .00012795  00000-0  63383-3 0  9994"
tle2 = "2 28485  20.5570  98.6682 0008279 273.6948  86.2541 15.15248522 52921"
tleentry = TLEEntry(satname=satname, tle1=tle1, tle2=tle2)

# Manually load this TLE
tle = SwiftTLE(epoch=Time("2024-01-29"), tle=tleentry)

# Calculate a Swift Ephemeris
eph = SwiftEphem(begin=Time("2024-01-29"), end=Time("2024-01-30"), tle=tle.tle)

# Calculate Swift SAA passages
saa = SwiftSAA(begin=Time("2024-01-29"), end=Time("2024-01-30"), ephem=eph)

# Make array of SAA entries in unix time
saa_entries = np.array([(e.begin.unix, e.end.unix) for e in saa.entries])

# Calculate Swift SAA passages using Swift API
# from swifttools.swift_too import SAA
#
# swift_saa = SAA(begin=Time("2024-01-29"), end=Time("2024-01-30"))
# swift_saa_entries = np.array(
#     [(e.begin.timestamp(), e.end.timestamp()) for e in swift_saa]
# )
swift_saa_entries = np.array(
    [
        [1.70648924e09, 1.70649016e09],
        [1.70652691e09, 1.70652721e09],
        [1.70653264e09, 1.70653389e09],
        [1.70653851e09, 1.70653998e09],
        [1.70654440e09, 1.70654596e09],
        [1.70655034e09, 1.70655191e09],
        [1.70655640e09, 1.70655785e09],
        [1.70656248e09, 1.70656379e09],
        [1.70656855e09, 1.70656972e09],
    ]
)


def test_swift_saa():
    """Assert that the SAA enter/exit times are within 60 seconds of the Swift
    API, where 60s is the default stepsize"""
    assert len(swift_saa_entries) == len(saa.entries)
    assert (np.abs(saa_entries - swift_saa_entries) < saa.stepsize.to(u.s).value).all()
