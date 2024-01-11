from typing import Optional

import astropy.units as u  # type: ignore
from arc import tables  # type: ignore
from astropy.coordinates import SkyCoord  # type: ignore
from astropy.time import Time  # type: ignore
from boto3.dynamodb.conditions import Key  # type: ignore

from ..across.user import check_api_key
from ..base.common import ACROSSAPIBase
from .schema import (
    BurstCubeTOORequestsGetSchema,
    BurstCubeTOORequestsSchema,
    BurstCubeTOOSchema,
)


class BurstCubeTOORequests(ACROSSAPIBase):
    """
    Class to fetch multiple BurstCubeTOO requests, based on various filters.

    Note that the filtering right now is based on DynamoDB scan, which is not
    very efficient. This should be replaced with a query at some point.

    Parameters
    ----------
    username
        Username for API
    api_key
        API Key for user
    begin
        Start time of plan search
    end
        End time of plan search
    limit
        Limit number of searches
    trigger_time
        Time of trigger
    trigger_mission
        Mission of trigger
    trigger_instrument
        Instrument of trigger
    trigger_id
        ID of trigger
    ra
        Right ascension of trigger search
    dec
        Declination of trigger search
    radius
        Radius of search around for trigger

    Attributes
    ----------
    entries
        List of BurstCubeTOO requests
    status
        Status of BurstCubeTOO query
    """

    _schema = BurstCubeTOORequestsSchema
    _get_schema = BurstCubeTOORequestsGetSchema
    mission = "ACROSS"

    def __getitem__(self, i):
        return self.entries[i]

    def __len__(self):
        return len(self.entries)

    def __init__(
        self,
        username: str,
        api_key: str,
        begin: Optional[Time] = None,
        end: Optional[Time] = None,
        limit: Optional[int] = None,
        trigger_time: Optional[Time] = None,
        trigger_mission: Optional[str] = None,
        trigger_instrument: Optional[str] = None,
        trigger_id: Optional[str] = None,
        ra: Optional[float] = None,
        dec: Optional[float] = None,
        radius: Optional[float] = None,
    ):
        # Default parameters
        self.username = username
        self.api_key = api_key
        self.trigger_time = trigger_time
        self.trigger_instrument = trigger_instrument
        self.trigger_mission = trigger_mission
        self.trigger_id = trigger_id
        self.limit = limit
        self.begin = begin
        self.end = end
        self.ra = ra
        self.dec = dec
        self.radius = radius
        # Attributes
        self.entries: list = []

        # Parse Arguments
        if self.validate_get():
            self.get()

    @check_api_key(anon=False)
    def get(self) -> bool:
        """
        Get a list of BurstCubeTOO requests

        Returns
        -------
        bool
            Did this work? True | False
        """
        # Validate query
        if not self.validate_get():
            return False
        table = tables.table("burstcube_too")

        filters = list()

        # Search for events that cover a given trigger_time
        if self.trigger_time is not None:
            filters.append(
                Key("begin").lte(str(self.trigger_time))
                & Key("end").gte(str(self.trigger_time))
            )

        # Search for events that overlap a given date range
        if self.begin is not None and self.end is not None:
            filters.append(
                Key("begin").between(str(self.begin), str(self.end))
                | Key("end").between(str(self.begin), str(self.end))
            )

        # Select on trigger_mission if given
        if self.trigger_mission is not None:
            filters.append(Key("trigger_mission").eq(self.trigger_mission))

        # Select on trigger_instrument if given
        if self.trigger_instrument is not None:
            filters.append(Key("trigger_instrument").eq(self.trigger_instrument))

        # Select on trigger_id if given
        if self.trigger_id is not None:
            filters.append(Key("trigger_id").eq(self.trigger_id))

        # Select on trigger_time if given
        if self.trigger_time is not None:
            filters.append(
                Key("begin").lte(str(self.trigger_time))
                & Key("end").gte(str(self.trigger_time))
            )

        # Check if a radius has been set, if not use default
        # FIXME: Set to specific instrument FOV
        if self.ra is not None and self.dec is not None and self.radius is None:
            self.radius = 1

        # Build the filter expression and query the table
        if len(filters) > 0:
            f = filters[0]
            for filt in filters[1:]:
                f = f & filt
            toos = table.scan(FilterExpression=f)
        else:
            toos = table.scan()

        # Convert entries for return
        self.entries = [BurstCubeTOOSchema.model_validate(too) for too in toos["Items"]]

        # Only include entries where the RA/Dec is within the given self.radius value
        # NOTE: This filters out any entries where RA/Dec is not given
        # FIXME: This is not very efficient, we should do this in the query
        if self.ra is not None and self.dec is not None and self.radius is not None:
            self.entries = [
                too
                for too in self.entries
                if too.ra is not None
                and (
                    SkyCoord(too.ra, too.dec, unit="deg").separation(
                        SkyCoord(self.ra, self.dec, unit="deg")
                    )
                    < self.radius * u.deg
                )
            ]

        # Sort and limit the results
        self.entries.sort(key=lambda x: x.trigger_time, reverse=True)
        self.entries = self.entries[: self.limit]

        return True


# Short aliases for classes
TOORequests = BurstCubeTOORequests
