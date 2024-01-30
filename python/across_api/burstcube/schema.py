# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.


from enum import Enum
from typing import List, Optional

import astropy.units as u  # type: ignore

from ..base.schema import (
    AstropySeconds,
    AstropyTime,
    BaseSchema,
    DateRangeSchema,
    OptionalCoordSchema,
    OptionalDateRangeSchema,
    OptionalPositionSchema,
    PointSchema,
)


class TOOReason(str, Enum):
    """
    Reasons for rejecting TOO observations

    Attributes
    ----------
    saa : str
        In SAA
    earth_occult : str
        Earth occulted
    moon_occult : str
        Moon occulted
    sun_occult : str
        Sun occulted
    too_old : str
        Too old
    other : str
        Other
    none : str
        None
    """

    saa = "In SAA"
    earth_occult = "Earth occulted"
    moon_occult = "Moon occulted"
    sun_occult = "Sun occulted"
    too_old = "Too old"
    other = "Other"
    none = "None"


class TOOStatus(str, Enum):
    """
    Enumeration class representing the status of a Target of Opportunity (TOO) request.

    Attributes:
    requested : str
        The TOO request has been submitted.
    rejected : str
        The TOO request has been rejected.
    declined : str
        The TOO request has been declined.
    approved : str
        The TOO request has been approved.
    executed : str
        The TOO request has been executed.
    other : str
        The TOO request has a status other than the predefined ones.
    deleted : str
        The TOO request has been deleted.
    """

    requested = "Requested"
    rejected = "Rejected"
    declined = "Declined"
    approved = "Approved"
    executed = "Executed"
    deleted = "Deleted"
    other = "Other"


class BurstCubeTOOSchema(OptionalPositionSchema):
    """
    Schema to retrieve all information about a BurstCubeTOO Request

    Parameters
    ----------
    id : Optional[int], optional
        The ID of the BurstCubeTOO Request, by default None
    sub : str
        The authentication sub associated with the BurstCubeTOO Request
    timestamp : Optional[datetime], optional
        The timestamp of the BurstCubeTOO Request, by default None
    trigger_mission : Optional[str], optional
        The mission associated with the trigger, by default None
    trigger_instrument : Optional[str], optional
        The instrument associated with the trigger, by default None
    trigger_id : Optional[str], optional
        The ID of the trigger, by default None
    trigger_time : Optional[datetime], optional
        The time of the trigger, by default None
    trigger_duration : Optional[float], optional
        The duration of the trigger, by default None
    classification : Optional[str], optional
        The classification of the trigger, by default None
    justification : Optional[str], optional
        The justification for the BurstCubeTOO Request, by default None
    begin : Optional[datetime], optional
        The start time of the BurstCubeTOO observation, by default None
    end : Optional[datetime], optional
        The end time of the BurstCubeTOO observation, by default None
    exposure : float, optional
        The exposure time for the BurstCubeTOO observation, by default 200
    offset : float, optional
        The offset for the BurstCubeTOO observation, by default -50
    reason : TOOReason, optional
        The reason for the BurstCubeTOO Request, by default TOOReason.none
    status : TOOStatus, optional
        The status of the BurstCubeTOO Request, by default TOOStatus.requested
    too_info : str, optional
        Additional information about the BurstCubeTOO Request, by default ""
    """

    id: Optional[str] = None
    sub: str
    timestamp: Optional[AstropyTime] = None
    trigger_mission: Optional[str] = None
    trigger_instrument: Optional[str] = None
    trigger_id: Optional[str] = None
    trigger_time: Optional[AstropyTime] = None
    trigger_duration: Optional[float] = None
    classification: Optional[str] = None
    justification: Optional[str] = None
    begin: AstropySeconds
    exposure: AstropySeconds
    reject_reason: TOOReason = TOOReason.none
    status: TOOStatus = TOOStatus.requested
    too_info: str = ""


class BurstCubeTOODelSchema(BaseSchema):
    """
    Schema for BurstCubeTOO DELETE API call.

    Attributes
    ----------
    id : int
        The ID of the BurstCubeTOODel object.
    """

    id: str


class BurstCubeTOOPostSchema(OptionalPositionSchema):
    """
    Schema to submit a TOO request for BurstCube.

    Parameters
    ----------
    sub : str
        The authentication sub associated with the request.
    trigger_mission : str
        The mission associated with the trigger.
    trigger_instrument : str
        The instrument associated with the trigger.
    trigger_id : str
        The ID of the trigger.
    trigger_time : datetime
        The time of the trigger.
    trigger_duration : float, optional
        The duration of the trigger, default is 0.
    classification : str, optional
        The classification of the trigger, default is None.
    justification : str, optional
        The justification for the trigger, default is None.
    begin : datetime, optional
        The beginning time of the trigger, default is None.
    end : datetime, optional
        The end time of the trigger, default is None.
    exposure : float, optional
        The exposure time, default is 200.
    offset : float, optional
        The offset value, default is -50.
    """

    trigger_mission: str
    trigger_instrument: str
    trigger_id: str
    trigger_time: AstropyTime
    trigger_duration: Optional[float] = 0
    classification: Optional[str] = None
    justification: Optional[str] = None
    begin: Optional[AstropyTime] = None
    end: Optional[AstropyTime] = None
    exposure: AstropySeconds = 200 * u.s
    offset: AstropySeconds = -50 * u.s


class BurstCubeFOVCheckGetSchema(OptionalCoordSchema, DateRangeSchema):
    """
    Schema for BurstCube FOV Check Get request.

    Parameters
    ----------
    healpix_loc : Optional[list], optional
        HEALPix map localization.
    stepsize : int, optional
        Step size in seconds, by default 60.
    earthoccult : bool, optional
        Flag indicating whether to consider Earth occultation, by default True.
    """

    healpix_loc: Optional[list] = None
    stepsize: AstropySeconds
    earthoccult: bool = True


class BurstCubeFOVCheckSchema(BaseSchema):
    """
    Schema for BurstCube FOV Check.

    Attributes
    ----------
    entries
        List of BurstCube points.
    """

    entries: List[PointSchema]


class BurstCubeTOOGetSchema(BaseSchema):
    """
    Schema for BurstCubeTOO GET request.

    Parameters
    ----------
    id : int
        The ID of the BurstCube TOO.
    """

    id: str


class BurstCubeTOOPutSchema(BaseSchema):
    """
    Schema for BurstCubeTOO GET request.

    Parameters
    ----------
    id : int
        The ID of the BurstCube TOO.
    """

    id: str


class BurstCubeTOORequestsGetSchema(OptionalPositionSchema, OptionalDateRangeSchema):
    """
    Schema for GET requests to retrieve BurstCube Target of Opportunity (TOO) requests.

    Parameters:
    -----------
    ra : Optional[float]
        The right ascension of the TOO requests.
    dec : Optional[float]
        The declination of the TOO requests.
    radius : Optional[float]
        The radius around the target coordinates to search for TOO requests.
    begin : Optional[datetime]
        The start time of the TOO requests.
    end : Optional[datetime]
        The end time of the TOO requests.
    trigger_time : Optional[datetime]
        The trigger time of the TOO requests.
    trigger_mission : Optional[str]
        The mission associated with the trigger of the TOO requests.
    trigger_instrument : Optional[str]
        The instrument associated with the trigger of the TOO requests.
    trigger_id : Optional[str]
        The ID of the trigger associated with the TOO requests.
    limit : Optional[int]
        The maximum number of TOO requests to retrieve.
    """

    trigger_time: Optional[AstropyTime] = None
    trigger_mission: Optional[str] = None
    trigger_instrument: Optional[str] = None
    trigger_id: Optional[str] = None
    limit: Optional[int] = None


class BurstCubeTOORequestsSchema(BaseSchema):
    """
    Schema for BurstCube TOO requests.

    Attributes
    ----------
    entries : List[BurstCubeTOOSchema]
        List of BurstCube TOOs.
    """

    entries: List[BurstCubeTOOSchema]
