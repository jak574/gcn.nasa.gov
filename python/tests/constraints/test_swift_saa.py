# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.


import numpy as np
from across_api.swift.constraints import swift_saa_constraint  # type: ignore


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


def test_swift_saa(swift_ephem, swiftapi_saa_entries):
    # Calculate a bool array for when Swift is in SAA
    swift_insaa = swift_saa_constraint(time=swift_ephem.timestamp, ephem=swift_ephem)

    # Convert this to a list of start/stop windows
    saa_entries = make_windows(swift_insaa, swift_ephem.timestamp)
    assert len(swiftapi_saa_entries) == len(saa_entries)
    assert (np.abs(saa_entries - swiftapi_saa_entries) <= 60).all()
