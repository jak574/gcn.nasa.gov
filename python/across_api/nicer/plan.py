import os
from datetime import datetime
from typing import Optional, Union

from ..across.user import check_api_key
from ..base.config import set_observatory
from ..base.plan import PlanBase
from ..base.schema import ConfigSchema, JobInfo
from .config import NICER
from .models import NICERPlanEntryModel
from .schema import NICERPlanEntry, NICERPlanGetSchema, NICERPlanSchema


@set_observatory(NICER)
class NICERPlan(PlanBase):
    """Class to query NICER plan database.

    Parameters
    ----------
    username
        Username for API
    api_key
        API Key for user
    ra
        Right Ascension in decimal degrees
    dec
        Declination in decimal degrees
    begin
        Start time of plan search
    end
        End time of plan search
    obsid
        NICER Observation ID
    targetid
        NICER Target ID
    radius
        Radius for search in degrees (default: 1.5)
    """

    _schema = NICERPlanSchema  # type: ignore
    _put_schema = NICERPlanGetSchema
    _get_schema = NICERPlanGetSchema
    _entry_model = NICERPlanEntryModel
    _entry_schema = NICERPlanEntry  # type: ignore
    config: ConfigSchema

    def __init__(
        self,
        username: str = "anonymous",
        api_key: str = "anonymous",
        ra: Optional[float] = None,
        dec: Optional[float] = None,
        begin: Optional[datetime] = None,
        end: Optional[datetime] = None,
        obsid: Union[int, list, None] = None,
        targetid: Union[int, list, None] = None,
        radius: Optional[float] = None,
    ):
        self.username = username
        self.api_key = api_key
        self.obsid = obsid
        self.targetid = targetid
        self.begin = begin
        self.end = end
        self.ra = ra
        self.dec = dec
        if radius is not None:
            self.radius = radius
        else:
            # Read instrument radius from FOV Config
            self.radius = self.config.instruments[0].fov.dimension
        self.plan_max: Optional[datetime] = None
        self.entries: list = []
        self.status: JobInfo = JobInfo()

    @check_api_key(anon=False, requser=["nicer", "jak51"])
    def put(self) -> bool:
        """
        Put a plan into the database.

        Returns
        -------
        bool
            Did the query succeed?
        """
        return super().put()

    def get(self) -> bool:
        """
        Get a plan from the database.

        Returns
        -------
        bool
            Did the query succeed?
        """
        return super().get()


# Mission specific names for classes
Plan = NICERPlan
PlanEntry = NICERPlanEntry
PlanSchema = NICERPlanSchema


# If we're in a dev environment, create the table if it doesn't exist
if os.environ.get("ARC_SANDBOX") is not None:
    NICERPlanEntryModel.create_table()
