# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
from fastapi import FastAPI

from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, Path, Query

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


def to_naive_utc(value: Optional[datetime]) -> Optional[datetime]:  #
    """
    Converts a datetime object to a naive datetime object in UTC timezone.

    Arguments
    ---------
    value
        The datetime object to be converted.

    Returns
    -------
        The converted naive datetime object in UTC timezone.
    """
    if value is None:
        return None

    return value.astimezone(tz=timezone.utc).replace(tzinfo=None)


# Globally defined Depends definitions
async def epoch(
    epoch: Annotated[
        datetime,
        Query(
            title="Epoch",
            description="Epoch in UTC or ISO format.",
        ),
    ],
) -> Optional[datetime]:
    return to_naive_utc(epoch)


EpochDep = Annotated[datetime, Depends(epoch)]


# Depends functions for FastAPI calls.
async def daterange(
    begin: Annotated[
        datetime,
        Query(description="Start time of period to be calculated.", title="Begin"),
    ],
    end: Annotated[
        datetime, Query(description="End time of period to be calculated.", title="End")
    ],
) -> dict:
    """
    Helper function to convert begin and end to datetime objects.
    """
    return {"begin": to_naive_utc(begin), "end": to_naive_utc(end)}


DateRangeDep = Annotated[dict, Depends(daterange)]


# Depends functions
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
    return {"begin": to_naive_utc(begin), "end": to_naive_utc(end)}


OptionalDateRangeDep = Annotated[dict, Depends(optional_daterange)]


async def stepsize(
    stepsize: Annotated[
        int,
        Query(
            ge=1,
            title="Step Size",
            description="Time resolution in which to calculate result in seconds.",
        ),
    ] = 60,
) -> int:
    return stepsize


StepSizeDep = Annotated[int, Depends(stepsize)]


async def ra_dec(
    ra: Annotated[
        float,
        Query(
            ge=0,
            lt=360,
            title="RA (J2000)",
            description="Right Ascenscion in J2000 coordinates and units of decimal degrees.",
        ),
    ],
    dec: Annotated[
        float,
        Query(
            ge=-90,
            le=90,
            title="Dec (J2000)",
            description="Declination in J2000 coordinates in units of decimal degrees.",
        ),
    ],
) -> dict:
    return {"ra": ra, "dec": dec}


RaDecDep = Annotated[dict, Depends(ra_dec)]


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
    return {"ra": ra, "dec": dec}


OptionalRaDecDep = Annotated[dict, Depends(optional_ra_dec)]


async def optional_radius(
    radius: Annotated[
        Optional[float],
        Query(
            ge=0,
            title="Radius",
            description="Radius in units of decimal degrees.",
        ),
    ] = None,
) -> Optional[float]:
    return radius


OptionalRadiusDep = Annotated[Optional[float], Depends(optional_radius)]


async def username_api_key(
    username: Annotated[
        str,
        Query(
            title="Username",
            description="ACROSS API Username",
        ),
    ],
    api_key: Annotated[
        str,
        Query(
            title="API Key",
            description="ACROSS API Key",
        ),
    ],
) -> dict:
    return {"username": username, "api_key": api_key}


LoginDep = Annotated[dict, Depends(username_api_key)]


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


async def optional_obsid(
    obsid: Annotated[
        Optional[int],
        Query(
            ge=0,
            title="ObsID",
            description="ObsID to search for.",
        ),
    ] = None,
) -> Optional[int]:
    return obsid


OptionalObsIdDep = Annotated[Optional[int], Depends(optional_obsid)]


async def optional_targetid(
    targetid: Annotated[
        Optional[int],
        Query(
            ge=0,
            title="TargetID",
            description="TargetID to search for.",
        ),
    ] = None,
) -> Optional[int]:
    return targetid


OptionalTargetIdDep = Annotated[Optional[int], Depends(optional_targetid)]


async def earth_occult(
    earthoccult: Annotated[
        bool,
        Query(
            title="Earth Occultation",
            description="Consider Earth occultation when calculating if target in FOV (default = True, Earth occulted sources are *not* in FOV)",
        ),
    ] = True,
) -> bool:
    return earthoccult


EarthOccultDep = Annotated[bool, Depends(earth_occult)]

IdDep = Annotated[str, Path(description="TOO ID string")]


async def trigger_time(
    trigger_time: Annotated[
        datetime,
        Query(
            title="Trigger Time",
            description="Time of trigger in UTC or ISO format.",
        ),
    ],
) -> Optional[datetime]:
    return to_naive_utc(trigger_time)


TriggerTimeDep = Annotated[datetime, Depends(trigger_time)]


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
    return error_radius


ErrorRadiusDep = Annotated[float, Depends(error_radius)]


async def trigger_mission(
    trigger_mission: Annotated[
        str,
        Query(
            title="Trigger Mission",
            description="Mission that triggered TOO request.",
        ),
    ],
) -> str:
    return trigger_mission


TriggerMissionDep = Annotated[str, Depends(trigger_mission)]


async def trigger_instrument(
    trigger_instrument: Annotated[
        str,
        Query(
            title="Trigger Instrument",
            description="Instrument that triggered TOO request.",
        ),
    ],
) -> str:
    return trigger_instrument


TriggerInstrumentDep = Annotated[str, Depends(trigger_instrument)]


async def trigger_id(
    trigger_id: Annotated[
        str,
        Query(
            title="Trigger ID",
            description="ID of trigger.",
        ),
    ],
) -> str:
    return trigger_id


TriggerIdDep = Annotated[str, Depends(trigger_id)]


async def classification(
    classification: Annotated[
        Optional[str],
        Query(
            title="Classification",
            description="Classification of trigger.",
        ),
    ] = None,
) -> Optional[str]:
    return classification


ClassificationDep = Annotated[str, Depends(classification)]


async def justification(
    justification: Annotated[
        str,
        Query(
            title="Justification",
            description="Justification for TOO request.",
        ),
    ] = "",
) -> str:
    return justification


JustificationDep = Annotated[str, Depends(justification)]


async def exposure(
    exposure: Annotated[
        float,
        Query(
            ge=0,
            title="Exposure",
            description="Exposure time in seconds.",
        ),
    ] = 200,
) -> float:
    return exposure


async def offset(
    offset: Annotated[
        float,
        Query(
            ge=-200,
            le=200,
            title="Offset",
            description="Offset window from T0 by this amount (seconds).",
        ),
    ] = -50,
) -> float:
    return offset


OffsetDep = Annotated[float, Depends(offset)]

ExposureDep = Annotated[float, Depends(exposure)]
