# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from ..base.api import DateRangeDep, RaDecDep, StepSizeDep, app, EpochDep
from ..base.schema import EphemSchema, SAASchema, VisibilitySchema, TLESchema
from .ephem import NuSTAREphem
from .saa import NuSTARSAA
from .tle import NuSTARTLE
from .visibility import NuSTARVisibility


@app.get("/nustar/ephem")
async def nustar_ephemeris(
    daterange: DateRangeDep,
    stepsize: StepSizeDep,
) -> EphemSchema:
    """
    Returns the ephemeris data for the NuSTAR satellite within the specified date range and step size.
    """
    return NuSTAREphem(
        begin=daterange["begin"], end=daterange["end"], stepsize=stepsize
    ).schema


@app.get("/nustar/saa")
async def nustar_saa(
    daterange: DateRangeDep,
    stepsize: StepSizeDep,
) -> SAASchema:
    """
    Endpoint for retrieving NuSTAR SAA data within a specified date range and step size.
    """
    return NuSTARSAA(
        begin=daterange["begin"], end=daterange["end"], stepsize=stepsize
    ).schema


@app.get("/nustar/tle")
async def nustar_tle(
    epoch: EpochDep,
) -> TLESchema:
    """
    Returns the best TLE for NuSTAR for a given epoch.
    """
    return NuSTARTLE(epoch=epoch).schema


@app.get("/nustar/visibility")
async def nustar_visibility(
    daterange: DateRangeDep,
    ra_dec: RaDecDep,
) -> VisibilitySchema:
    """
    Returns the visibility of an astronomical object to NuSTAR for a given date range and RA/Dec coordinates.
    """
    return NuSTARVisibility(
        begin=daterange["begin"],
        end=daterange["end"],
        ra=ra_dec["ra"],
        dec=ra_dec["dec"],
    ).schema
