# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

import numpy as np
from across_api.burstcube.constraints import burstcube_saa_constraint  # type: ignore


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
    return np.array([(win[0], win[1]) for win in windows])


def test_burstcube_saa(burstcube_skyfield_saa, burstcube_ephem):
    # Set up the BurstCube SAA constraint. This is an instance of the
    # SAAPolygonConstraint class, with the polygon defined by the BurstCube team provided.
    burstcube_saa = burstcube_saa_constraint(
        time=burstcube_ephem.timestamp, ephem=burstcube_ephem
    )

    # Make windows for the BurstCube SAA constraint
    burstcube_saa_windows = make_windows(burstcube_saa, burstcube_ephem.timestamp.unix)

    assert (
        (burstcube_saa_windows - burstcube_skyfield_saa) == 0
    ).all(), "SAA calculated windows don't match"
