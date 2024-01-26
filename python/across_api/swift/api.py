# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from typing import Annotated, Literal, Optional

from fastapi import Depends, Query, status

from ..base.api import (
    DateRangeDep,
    EarthOccultDep,
    EpochDep,
    LoginDep,
    OptionalDateRangeDep,
    OptionalRaDecDep,
    OptionalRadiusDep,
    OptionalTargetIdDep,
    RaDecDep,
    StepSizeDep,
    app,
)
from ..base.schema import EphemSchema, SAASchema, TLESchema, VisibilitySchema
from .ephem import SwiftEphem
from .fov import SwiftFOVCheck
from .observations import SwiftObservations
from .plan import SwiftPlan
from .saa import SwiftSAA
from .schema import SwiftFOVCheckSchema, SwiftObservationsSchema, SwiftPlanSchema
from .tle import SwiftTLE
from .visibility import SwiftVisibility


# Swift only Depends
def swift_instrument_query(
    instrument: Annotated[
        Literal["XRT", "UVOT", "BAT"],
        Query(
            title="Instrument",
            description="Instrument to use in FOV calculation.",
        ),
    ] = "XRT"
) -> dict:
    return {"instrument": instrument}


SwiftInstrumentDep = Annotated[
    Literal["XRT", "UVOT", "BAT"], Depends(swift_instrument_query)
]


async def optional_obsid(
    obsid: Annotated[
        Optional[str],
        Query(
            title="ObsID",
            description="ObsID to search for.",
        ),
    ] = None,
) -> Optional[str]:
    return obsid


OptionalObsIdDep = Annotated[Optional[str], Depends(optional_obsid)]


# Swift API Endpoints
@app.get("/swift/ephem")
def swift_ephemeris(
    daterange: DateRangeDep,
    stepsize: StepSizeDep,
) -> EphemSchema:
    """
    Returns a Swift Ephemeris object for the given date range and step size.
    """
    return SwiftEphem(
        begin=daterange["begin"], end=daterange["end"], stepsize=stepsize
    ).schema


@app.get("/swift/fovcheck")
async def swift_fov_check(
    ra_dec: RaDecDep,
    daterange: DateRangeDep,
    stepsize: StepSizeDep,
    instrument: SwiftInstrumentDep,
    earthoccult: EarthOccultDep = True,
) -> SwiftFOVCheckSchema:
    """
    Endpoint for checking if a given celestial object is within the field of view of the Swift satellite.
    """
    fov = SwiftFOVCheck(
        ra=ra_dec["ra"],
        dec=ra_dec["dec"],
        begin=daterange["begin"],
        end=daterange["end"],
        stepsize=stepsize,
        earthoccult=earthoccult,
        instrument=instrument,
    )
    fov.get()
    return fov.schema


@app.get("/swift/observations")
async def swift_observation(
    daterange: OptionalDateRangeDep,
    ra_dec: OptionalRaDecDep,
    radius: OptionalRadiusDep,
    obsid: OptionalObsIdDep,
    targetid: OptionalTargetIdDep,
) -> SwiftObservationsSchema:
    """
    Endpoint to retrieve Swift observations based on optional filters on date range, RA/Dec, radius, obsid, and targetid.
    """
    observation = SwiftObservations(
        begin=daterange["begin"],
        end=daterange["end"],
        ra=ra_dec["ra"],
        dec=ra_dec["dec"],
        radius=radius,
        obsid=obsid,
        targetid=targetid,
    )
    observation.get()
    return observation.schema


@app.put("/swift/observations", status_code=status.HTTP_201_CREATED)
async def swift_observations_upload(
    user: LoginDep,
    data: SwiftObservationsSchema,
) -> SwiftObservationsSchema:
    """
    Upload Swift Observations to the server.
    """
    observations = SwiftObservations(username=user["username"], api_key=user["api_key"])
    observations.entries = data.entries
    observations.put()
    return observations.schema


@app.get("/swift/plan")
async def swift_plan(
    daterange: OptionalDateRangeDep,
    ra_dec: OptionalRaDecDep,
    radius: OptionalRadiusDep,
    obsid: OptionalObsIdDep,
    targetid: OptionalTargetIdDep,
) -> SwiftPlanSchema:
    """
    Endpoint for retrieving Swift observation plan.
    """
    plan = SwiftPlan(
        begin=daterange["begin"],
        end=daterange["end"],
        ra=ra_dec["ra"],
        dec=ra_dec["dec"],
        radius=radius,
        obsid=obsid,
        targetid=targetid,
    )
    plan.get()
    return plan.schema


@app.put("/swift/plan", status_code=status.HTTP_201_CREATED)
async def swift_plan_upload(
    user: LoginDep,
    data: SwiftPlanSchema,
) -> SwiftPlanSchema:
    """
    This function uploads a Swift plan to the server.
    """
    plan = SwiftPlan(username=user["username"], api_key=user["api_key"])
    plan.entries = data.entries
    plan.put()
    return plan.schema


@app.get("/swift/saa")
async def swift_saa(daterange: DateRangeDep) -> SAASchema:
    """
    Endpoint for retrieving the times of Swift SAA passages for a given date range.
    """
    return SwiftSAA(**daterange).schema


@app.get("/swift/tle")
def swift_tle(
    epoch: EpochDep,
) -> TLESchema:
    """
    Returns the best TLE for Swift for a given epoch.
    """
    return SwiftTLE(epoch=epoch).schema


@app.get("/swift/visibility")
async def swift_visibility(
    daterange: DateRangeDep,
    ra_dec: RaDecDep,
) -> VisibilitySchema:
    """
    Calculates the visibility of a celestial object to the Swift satellite.
    """
    return SwiftVisibility(
        begin=daterange["begin"],
        end=daterange["end"],
        ra=ra_dec["ra"],
        dec=ra_dec["dec"],
    ).schema
