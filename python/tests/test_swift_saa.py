# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.


import numpy as np
from astropy.time import Time  # type: ignore
from across_api.swift.ephem import SwiftEphem  # type: ignore
from across_api.swift.tle import SwiftTLE  # type: ignore
from across_api.base.schema import TLEEntry  # type: ignore
from across_api.swift.saa import swift_saa_constraint  # type: ignore


def make_windows(insaa, timestamp):
    """Function to make start and end windows from a boolean array of SAA
    constraints and array of timestamps"""
    # Find the start and end of the SAA windows
    buff = np.concatenate(([False], insaa.tolist(), [False]))
    begin = np.flatnonzero(~buff[:-1] & buff[1:])
    end = np.flatnonzero(buff[:-1] & ~buff[1:])
    indices = np.column_stack((begin, end - 1))
    windows = timestamp[indices]

    # Return as array of SAAEntry objects
    return np.array([(win[0].unix, win[1].unix) for win in windows])


# Define a TLE by hand
satname = "SWIFT"
tle1 = "1 28485U 04047A   24029.43721350  .00012795  00000-0  63383-3 0  9994"
tle2 = "2 28485  20.5570  98.6682 0008279 273.6948  86.2541 15.15248522 52921"
tleentry = TLEEntry(satname=satname, tle1=tle1, tle2=tle2)

# Manually load this TLE
tle = SwiftTLE(epoch=Time("2024-01-29"), tle=tleentry)

# Calculate a Swift Ephemeris
eph = SwiftEphem(begin=Time("2024-01-29"), end=Time("2024-01-30"), tle=tle.tle)

# Calculate a bool array for when Swift is in SAA
swift_insaa = swift_saa_constraint(time=eph.timestamp, ephem=eph)

# Convert this to a list of start/stop windows
saa_entries = make_windows(swift_insaa, eph.timestamp)

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
    assert len(swift_saa_entries) == len(saa_entries)
    assert (np.abs(saa_entries - swift_saa_entries) <= 60).all()
