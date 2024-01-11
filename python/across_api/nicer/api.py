# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from fastapi import status

from ..base.api import (
    DateRangeDep,
    EpochDep,
    LoginDep,
    OptionalDateRangeDep,
    OptionalObsIdDep,
    OptionalRaDecDep,
    OptionalRadiusDep,
    OptionalTargetIdDep,
    RaDecDep,
    app,
)
from ..base.schema import TLESchema, VisibilitySchema
from .plan import NICERPlan
from .schema import NICERPlanSchema
from .tle import NICERTLE
from .visibility import NICERVisibility


@app.get("/nicer/plan")
async def nicer_plan(
    daterange: OptionalDateRangeDep,
    ra_dec: OptionalRaDecDep,
    radius: OptionalRadiusDep,
    obsid: OptionalObsIdDep,
    targetid: OptionalTargetIdDep,
) -> NICERPlanSchema:
    """
    Returns a NICER observation plan based on the given parameters.
    """
    plan = NICERPlan(
        begin=daterange["begin"],
        end=daterange["end"],
        obsid=obsid,
        targetid=targetid,
        ra=ra_dec["ra"],
        dec=ra_dec["dec"],
        radius=radius,
    )
    plan.get()
    return plan.schema


@app.put("/nicer/plan", status_code=status.HTTP_201_CREATED)
async def nicer_plan_upload(
    user: LoginDep,
    data: NICERPlanSchema,
) -> NICERPlanSchema:
    """
    Uploads a NICER Plan.
    """
    plan = NICERPlan(username=user["username"], api_key=user["api_key"])
    plan.entries = data.entries
    plan.put()
    return plan.schema


@app.get("/nicer/tle")
async def nicer_tle(
    epoch: EpochDep,
) -> TLESchema:
    """
    Returns the best TLE for NICER for a given epoch.
    """
    return NICERTLE(epoch=epoch).schema


@app.get("/nicer/visibility")
async def nicer_visibility(
    daterange: DateRangeDep,
    ra_dec: RaDecDep,
) -> VisibilitySchema:
    """
    Returns the visibility of an astronomical object to NICER for a given date range and RA/Dec coordinates.
    """
    return NICERVisibility(
        begin=daterange["begin"],
        end=daterange["end"],
        ra=ra_dec["ra"],
        dec=ra_dec["dec"],
    ).schema
