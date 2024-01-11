# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from typing import Annotated, Literal

from fastapi import Query

from ..base.api import (
    DateRangeDep,
    EarthOccultDep,
    EpochDep,
    RaDecDep,
    StepSizeDep,
    app,
)
from ..base.schema import EphemSchema, SAASchema, TLESchema, VisibilitySchema
from .ephem import FermiEphem
from .fov import FermiFOVCheck
from .saa import FermiSAA
from .schema import FermiFOVCheckSchema
from .tle import FermiTLE
from .visibility import FermiVisibility


@app.get("/fermi/ephem")
async def fermi_ephemeris(
    daterange: DateRangeDep,
    stepsize: StepSizeDep,
) -> EphemSchema:
    """
    Returns the ephemeris data for the Fermi spacecraft for the given date range and step size.
    """
    return FermiEphem(
        begin=daterange["begin"], end=daterange["end"], stepsize=stepsize
    ).schema


@app.get("/fermi/fovcheck")
async def fermi_fov_check(
    ra_dec: RaDecDep,
    daterange: DateRangeDep,
    stepsize: StepSizeDep,
    earthoccult: EarthOccultDep = True,
    instrument: Annotated[
        Literal["GBM", "LAT"],
        Query(
            title="Instrument",
            description="Instrument to use in FOV calculation.",
        ),
    ] = "GBM",
) -> FermiFOVCheckSchema:
    """
    Endpoint for checking if a given celestial object is within the field of view of the Fermi satellite.
    """
    fov = FermiFOVCheck(
        ra=ra_dec["ra"],
        dec=ra_dec["dec"],
        begin=daterange["begin"],
        end=daterange["end"],
        stepsize=stepsize,
        earthoccult=earthoccult,
    )
    fov.get()
    return fov.schema


@app.get("/fermi/saa")
async def fermi_saa(
    daterange: DateRangeDep,
    stepsize: StepSizeDep,
) -> SAASchema:
    """
    Returns the Fermi SAA passage times for a given date range and step size.
    """
    return FermiSAA(
        begin=daterange["begin"], end=daterange["end"], stepsize=stepsize
    ).schema


@app.get("/fermi/tle")
async def fermi_tle(
    epoch: EpochDep,
) -> TLESchema:
    """
    Returns the best TLE for Fermi for a given epoch.
    """
    return FermiTLE(epoch=epoch).schema


@app.get("/fermi/visibility")
async def fermi_visibility(
    daterange: DateRangeDep,
    ra_dec: RaDecDep,
) -> VisibilitySchema:
    """
    Returns the visibility of an astronomical object to Fermi for a given date range and RA/Dec coordinates.
    """
    return FermiVisibility(
        begin=daterange["begin"],
        end=daterange["end"],
        ra=ra_dec["ra"],
        dec=ra_dec["dec"],
    ).schema
