# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from typing import Optional

import astropy.units as u  # type: ignore
from arc import tables  # type: ignore
from astropy.time import Time  # type: ignore
from boto3.dynamodb.conditions import Key  # type: ignore

from ..base.common import ACROSSAPIBase
from .schema import (
    BurstCubeTOOModel,
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
    begin
        Start time of plan search
    end
        End time of plan search
    limit
        Limit number of searches
    length
        Length of time to search from now

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
        begin: Optional[Time] = None,
        end: Optional[Time] = None,
        length: Optional[u.Quantity] = None,
        limit: Optional[int] = None,
    ):
        # Default parameters
        self.limit = limit
        self.begin = begin
        self.end = end
        self.length = length
        # Attributes
        self.entries: list = []

        # Parse Arguments
        if self.validate_get():
            self.get()

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
        table = tables.table(BurstCubeTOOModel.__tablename__)

        if self.length is not None:
            self.begin = Time.now()
            self.end = self.begin - self.length

        # Search for events that overlap a given date range
        if self.begin is not None and self.end is not None:
            toos = table.scan(
                FilterExpression=Key("created_on").between(
                    str(self.begin), str(self.end)
                )
            )
        else:
            toos = table.scan()

        # Convert entries for return
        self.entries = [BurstCubeTOOSchema.model_validate(too) for too in toos["Items"]]

        # Sort and limit the results
        self.entries.sort(key=lambda x: x.trigger_time, reverse=True)
        self.entries = self.entries[: self.limit]

        return True


# Short aliases for classes
TOORequests = BurstCubeTOORequests
