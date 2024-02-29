# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

"""
Base API definitions for ACROSS API. This module is imported by all other API
modules.
"""

from astropy.time import Time  # type: ignore[import]
from datetime import datetime
from typing import Annotated, Optional
from fastapi import Depends, FastAPI, Path, Query
import astropy.units as u  # type: ignore[import]



# FastAPI app definition
app = FastAPI(
    title="ACROSS API",
    summary="Astrophysics Cross-Observatory Science Support (ACROSS).",
    description="API providing information on various NASA missions to aid in coordination of large observation efforts.",
    contact={
        "email": "support@gcn.nasa.gov",
    },
    root_path="/labs/api/v1",
)



# Depends functions for FastAPI calls.
async def optional_daterange(
    begin: Annotated[
        Optional[datetime],
        Query(
            description="Start time of period to be calculated.",
            title="Begin",
        ),
    ] = None,
    end: Annotated[
        Optional[datetime],
        Query(
            description="Start time of period to be calculated.",
            title="End",
        ),
    ] = None,
) -> dict:
    """
    Helper function to convert begin and end to datetime objects.
    """
    if begin is None or end is None:
        return {"begin": None, "end": None}
    return {"begin": Time(begin), "end": Time(end)}


OptionalDateRangeDep = Annotated[dict, Depends(optional_daterange)]


# Depends functions for FastAPI calls.
async def optional_duration(
    duration: Annotated[
        Optional[float],
        Query(
            description="Duration of time (days).",
            title="Duration",
        ),
    ] = None,
) -> Optional[u.Quantity]:
    """
    Helper function to convert begin and end to datetime objects.
    """
    if duration is None:
        return None
    return duration * u.day


OptionalDurationDep = Annotated[dict, Depends(optional_duration)]


async def optional_limit(
    limit: Annotated[
        Optional[int],
        Query(
            ge=0,
            title="Limit",
            description="Maximum number of results to return.",
        ),
    ] = None,
) -> Optional[int]:
    return limit


LimitDep = Annotated[Optional[int], Depends(optional_limit)]


async def error_radius(
    error_radius: Annotated[
        Optional[float],
        Query(
            ge=0,
            title="Error Radius",
            description="Error radius in degrees.",
        ),
    ] = None,
) -> Optional[float]:
    if error_radius is None:
        return None
    return error_radius * u.deg


ErrorRadiusDep = Annotated[float, Depends(error_radius)]


async def exposure(
    exposure: Annotated[
        float,
        Query(
            ge=0,
            title="Exposure",
            description="Exposure time in seconds.",
        ),
    ] = 200,
) -> u.Quantity:
    return exposure * u.s


ExposureDep = Annotated[float, Depends(exposure)]


async def offset(
    offset: Annotated[
        float,
        Query(
            ge=-200,
            le=200,
            title="Offset",
            description="Offset start of dump window from T0 by this amount (seconds).",
        ),
    ] = -50,
) -> u.Quantity:
    return offset * u.s


OffsetDep = Annotated[float, Depends(offset)]


async def optional_ra_dec(
    ra: Annotated[
        Optional[float],
        Query(
            ge=0,
            lt=360,
            title="RA (J2000)",
            description="Right Ascenscion in J2000 coordinates and units of decimal degrees.",
        ),
    ] = None,
    dec: Annotated[
        Optional[float],
        Query(
            ge=-90,
            le=90,
            title="Dec (J2000)",
            description="Declination in J2000 coordinates in units of decimal degrees.",
        ),
    ] = None,
) -> Optional[dict]:
    if ra is None or dec is None:
        return {"ra": None, "dec": None}
    return {"ra": ra * u.deg, "dec": dec * u.deg}


OptionalRaDecDep = Annotated[dict, Depends(optional_ra_dec)]


IdDep = Annotated[str, Path(description="TOO ID string")]


async def trigger_time(
    trigger_time: Annotated[
        datetime,
        Query(
            title="Trigger Time",
            description="Time of trigger in UTC or ISO format.",
        ),
    ],
) -> Optional[Time]:
    return Time(trigger_time)


TriggerTimeDep = Annotated[datetime, Depends(trigger_time)]
