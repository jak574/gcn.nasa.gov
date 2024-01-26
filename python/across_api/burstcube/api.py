# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from datetime import datetime
from io import BytesIO
from typing import Annotated, Optional

from astropy.io import fits  # type: ignore
from astropy.time import Time  # type: ignore
from fastapi import Depends, File, Query, status

from ..base.api import (
    ClassificationDep,
    DateRangeDep,
    EarthOccultDep,
    EpochDep,
    ErrorRadiusDep,
    ExposureDep,
    IdDep,
    JustificationDep,
    LimitDep,
    LoginDep,
    OffsetDep,
    OptionalDateRangeDep,
    OptionalRaDecDep,
    RaDecDep,
    StepSizeDep,
    TriggerIdDep,
    TriggerInstrumentDep,
    TriggerMissionDep,
    TriggerTimeDep,
    app,
)
from ..base.schema import EphemSchema, SAASchema, TLESchema, VisibilitySchema
from .ephem import BurstCubeEphem
from .fov import BurstCubeFOVCheck
from .requests import BurstCubeTOORequests
from .saa import BurstCubeSAA
from .schema import (
    BurstCubeFOVCheckSchema,
    BurstCubeTOORequestsSchema,
    BurstCubeTOOSchema,
)
from .tle import BurstCubeTLE
from .toorequest import BurstCubeTOO
from .visibility import BurstCubeVisibility


# BurstCube Deps
async def optional_trigger_time(
    trigger_time: Annotated[
        Optional[datetime],
        Query(
            title="Trigger Time",
            description="Time of trigger in UTC or ISO format.",
        ),
    ] = None,
) -> Optional[datetime]:
    return Time(trigger_time)


OptionalTriggerTimeDep = Annotated[datetime, Depends(optional_trigger_time)]


# BurstCube endpoints
@app.get("/burstcube/ephem")
async def burstcube_ephemeris(
    daterange: DateRangeDep,
    stepsize: StepSizeDep,
) -> EphemSchema:
    """
    Calculates the ephemeris for BurstCube.
    """
    return BurstCubeEphem(
        begin=daterange["begin"], end=daterange["end"], stepsize=stepsize
    ).schema


@app.get("/burstcube/fovcheck")
async def burstcube_fov_check(
    ra_dec: RaDecDep,
    daterange: DateRangeDep,
    stepsize: StepSizeDep,
    earth_occult: EarthOccultDep = True,
) -> BurstCubeFOVCheckSchema:
    """
    This endpoint checks if a given point in the sky is within the field of
    view of the BurstCube telescope, for a given time.
    """
    fov = BurstCubeFOVCheck(
        ra=ra_dec["ra"],
        dec=ra_dec["dec"],
        begin=daterange["begin"],
        end=daterange["end"],
        stepsize=stepsize,
        earthoccult=earth_occult,
    )
    fov.get()
    return fov.schema


@app.get("/burstcube/saa")
async def burstcube_saa(
    daterange: DateRangeDep,
    stepsize: StepSizeDep,
) -> SAASchema:
    """
    Endpoint to retrieve BurstCubeSAA data for a given date range and step size.
    """
    return BurstCubeSAA(stepsize=stepsize, **daterange).schema


@app.post("/burstcube/too", status_code=status.HTTP_201_CREATED)
async def burstcube_too_submit(
    user: LoginDep,
    ra_dec: OptionalRaDecDep,
    error: ErrorRadiusDep,
    trigger_time: TriggerTimeDep,
    trigger_mission: TriggerMissionDep,
    trigger_instrument: TriggerInstrumentDep,
    trigger_id: TriggerIdDep,
    classification: ClassificationDep,
    justification: JustificationDep,
    date_range: OptionalDateRangeDep,
    exposure: ExposureDep,
    offset: OffsetDep,
    healpix_file: Annotated[
        bytes, File(description="HEALPix file describing the localization.")
    ] = b"",
) -> BurstCubeTOOSchema:
    """
    Resolve the name of an astronomical object to its coordinates.
    """
    # Construct the TOO object.
    too = BurstCubeTOO(
        username=user["username"],
        api_key=user["api_key"],
        ra=ra_dec["ra"],
        dec=ra_dec["dec"],
        error_radius=error,
        trigger_time=trigger_time,
        trigger_mission=trigger_mission,
        trigger_instrument=trigger_instrument,
        trigger_id=trigger_id,
        classification=classification,
        justification=justification,
        begin=date_range["begin"],
        end=date_range["end"],
        exposure=exposure,
        offset=offset,
    )
    # If a HEALpix file was uploaded, open it and set the healpix_loc
    # and healpix_order attributes.
    if healpix_file != b"":
        hdu = fits.open(BytesIO(healpix_file))
        too.healpix_loc = hdu[1].data
        too.healpix_order = hdu[1].header["ORDERING"]
    too.post()
    return too.schema


@app.put("/burstcube/too/{id}", status_code=status.HTTP_201_CREATED)
async def burstcube_too_update(
    user: LoginDep,
    id: IdDep,
    data: BurstCubeTOOSchema,
) -> BurstCubeTOOSchema:
    """
    Update a BurstCube TOO object with the given ID number.
    """
    too = BurstCubeTOO(api_key=user["api_key"], **data.model_dump())
    too.put()
    return too.schema


@app.get("/burstcube/too/{id}", status_code=status.HTTP_200_OK)
async def burstcube_too(
    user: LoginDep,
    id: IdDep,
) -> BurstCubeTOOSchema:
    """
    Retrieve a BurstCube Target of Opportunity (TOO) by ID.
    """
    too = BurstCubeTOO(username=user["username"], api_key=user["api_key"], id=id)
    too.get()
    return too.schema


@app.delete("/burstcube/too/{id}", status_code=status.HTTP_200_OK)
async def burstcube_delete_too(
    user: LoginDep,
    id: IdDep,
) -> BurstCubeTOOSchema:
    """
    Delete a BurstCube Target of Opportunity (TOO) with the given ID.
    """
    too = BurstCubeTOO(username=user["username"], api_key=user["api_key"], id=id)
    too.delete()
    return too.schema


@app.get("/burstcube/toorequests")
async def burstcube_too_requests(
    user: LoginDep,
    daterange: OptionalDateRangeDep,
    ra_dec: OptionalRaDecDep,
    trigger_time: OptionalTriggerTimeDep,
    limit: LimitDep = None,
) -> BurstCubeTOORequestsSchema:
    """
    Endpoint to retrieve BurstCube TOO requests.
    """
    return BurstCubeTOORequests(
        username=user["username"],
        api_key=user["api_key"],
        begin=daterange["begin"],
        end=daterange["end"],
        ra=ra_dec["ra"],
        dec=ra_dec["dec"],
        trigger_time=trigger_time,
        limit=limit,
    ).schema


@app.get("/burstcube/tle")
async def burstcube_tle(
    epoch: EpochDep,
) -> TLESchema:
    """
    Returns the best TLE for BurstCube for a given epoch.
    """
    return BurstCubeTLE(epoch=epoch).schema


@app.get("/burstcube/visibility")
async def burstcube_visibility(
    daterange: DateRangeDep,
    ra_dec: RaDecDep,
) -> VisibilitySchema:
    """
    Returns the visibility of an astronomical object to BurstCube for a given date range and RA/Dec coordinates.
    """
    return BurstCubeVisibility(
        begin=daterange["begin"],
        end=daterange["end"],
        ra=ra_dec["ra"],
        dec=ra_dec["dec"],
    ).schema
