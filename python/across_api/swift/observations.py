import os
from datetime import datetime
from typing import Optional, Union

from ..across.user import check_api_key
from ..base.config import set_observatory
from ..base.plan import PlanBase
from ..base.schema import JobInfo
from .config import SWIFT
from .models import SwiftObsEntryModel
from .schema import (
    SwiftObsEntry,
    SwiftObservationsGetSchema,
    SwiftObservationsPutSchema,
    SwiftObservationsSchema,
)


@set_observatory(SWIFT)
class SwiftObservations(PlanBase):
    """
    Class to calculate Swift spacecraft Planned observations. This class is
    used to query the Swift database for planned observations. It is not used
    to calculate planned observations. The Swift database is updated every
    throughout the day with the latest planned observations.

    Parameters
    ----------
    username
        API username
    api_key
        API key
    ra
        Right Ascension in decimal degrees
    dec
        Declination in decimal degrees
    begin
        Start time of visibility search
    end
        End time of visibility search
    radius
        Search radius in degrees (default: XRT FOV)
    limit
        Maximum number of entries to return (default: 1000)
    obsid
        Observation ID(s) to query
    targetid
        Target ID(s) to query

    Attributes
    ----------
    entries
        List of SwiftPlanEntry entries
    status
        Info about SwiftPlan query
    plan_max
        Latest observation in the observations database
    """

    _schema = SwiftObservationsSchema  # type: ignore
    _put_schema = SwiftObservationsGetSchema
    _get_schema = SwiftObservationsPutSchema  # type: ignore
    _entry_model = SwiftObsEntryModel
    _entry_schema = SwiftObsEntry  # type: ignore

    def __init__(
        self,
        username: str = "anonymous",
        api_key: str = "anonymous",
        ra: Optional[float] = None,
        dec: Optional[float] = None,
        begin: Optional[datetime] = None,
        end: Optional[datetime] = None,
        obsid: Union[str, list, None] = None,
        targetid: Union[int, list, None] = None,
        radius: Optional[float] = None,
        limit: int = 1000,
    ):
        self.username = username
        self.api_key = api_key
        self.obsid = obsid
        self.targetid = targetid
        self.begin = begin
        self.end = end
        self.ra = ra
        self.dec = dec
        self.limit = limit
        if radius is not None:
            self.radius = radius
        else:
            # Use XRT FOV as the default search radius
            self.radius = self.config.instruments[1].fov.dimension
        self.plan_max: Optional[datetime] = None
        self.entries: list = []
        self.status: JobInfo = JobInfo()

    def __getitem__(self, i) -> SwiftObsEntry:
        return self.entries[i]

    @check_api_key(anon=False, requser=["jak51"])
    def put(self):
        return super().put()

    def get(self):
        return super().get()


# Mission specific names for classes
Observations = SwiftObservations
ObservationsSchema = SwiftObservationsSchema
ObsEntry = SwiftObsEntry


# If we're in a dev environment, create the table if it doesn't exist
if os.environ.get("ARC_SANDBOX") is not None:
    SwiftObsEntryModel.create_table()
