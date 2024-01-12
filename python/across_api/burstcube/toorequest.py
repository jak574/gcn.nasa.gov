# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from datetime import datetime, timedelta
from typing import Optional

import astropy.units as u  # type: ignore
import numpy as np  # type: ignore
from astropy.coordinates import SkyCoord  # type: ignore
from boto3.dynamodb.conditions import Key  # type: ignore
from fastapi import HTTPException
from python.across_api.base.schema import PointSchema

from ..across.user import check_api_key
from arc import tables  # type: ignore
from ..base.common import ACROSSAPIBase
from ..base.config import set_observatory
from ..burstcube.fov import BurstCubeFOVCheck
from ..functions import round_time
from .config import BURSTCUBE
from .models import BurstCubeTOOModel
from .saa import BurstCubeSAA
from .schema import (
    BurstCubeTOODelSchema,
    BurstCubeTOOGetSchema,
    BurstCubeTOOModelSchema,
    BurstCubeTOOPostSchema,
    BurstCubeTOOPutSchema,
    BurstCubeTOORequestsGetSchema,
    BurstCubeTOORequestsSchema,
    BurstCubeTOOSchema,
    TOOReason,
    TOOStatus,
)


@set_observatory(BURSTCUBE)
class BurstCubeTOO(ACROSSAPIBase):
    """
    Class to handle BurstCube Target of Opportunity Requests

    Parameters
    ----------
    username : str
        Username of user making request
    api_key : str
        API key of user making request
    id : Optional[int], optional
        ID of BurstCubeTOO to fetch, by default None
    """

    _schema = BurstCubeTOOSchema
    _get_schema = BurstCubeTOOGetSchema
    _put_schema = BurstCubeTOOPutSchema
    _del_schema = BurstCubeTOODelSchema
    _post_schema = BurstCubeTOOPostSchema

    id: Optional[str]
    username: str
    timestamp: Optional[datetime]
    ra: Optional[float]
    dec: Optional[float]
    error: Optional[float]
    trigger_time: datetime
    trigger_mission: str
    trigger_instrument: str
    trigger_id: str
    trigger_duration: Optional[float]
    classification: Optional[str]
    justification: Optional[str]
    begin: Optional[Time]
    end: Optional[Time]
    exposure: u.Quantity
    offset: float
    reason: TOOReason
    healpix_loc: Optional[np.ndarray]
    healpix_order: str = "nested"
    healpix_minprob: float = 0.01  # 1% of probability in FOV
    status: TOOStatus
    too_info: str
    warnings: list

    def __init__(self, username: str, api_key: str, id: Optional[str] = None, **kwargs):
        # Set Optional Parameters to None
        self.begin = None
        self.end = None
        self.ra = None
        self.dec = None
        self.healpix_loc = None
        self.healpix_order = "nested"
        self.id = None
        self.timestamp = None
        self.too_info = ""
        self.warnings = []

        # Parameter defaults
        self.exposure = 200  # default exposure time (e.g. length of dump)
        # default offset. Moves the triggertime 50s before the middle of the dump window.
        self.offset = -50
        # Status of job

        # Parse Arguments
        self.username = username
        self.api_key = api_key
        self.id = id
        # Connect to the DynamoDB table
        self.table = tables.table("burstcube_too")

        # Parse other keyword arguments
        for k, v in kwargs.items():
            if k in self._schema.model_fields.keys():
                setattr(self, k, v)

    @check_api_key(anon=False)
    def get(self) -> bool:
        """
        Fetch a BurstCubeTOO for a given id.

        Returns
        -------
        bool
            Did this work? True | False
        """

        # Fetch BurstCubeTOO from database

        response = self.table.get_item(Key={"id": self.id})
        if "Item" not in response:
            raise HTTPException(404, "BurstCubeTOO not found.")

        too = BurstCubeTOOModelSchema.model_validate(response["Item"])
        for k, v in too:
            setattr(self, k, v)
        return True

    @check_api_key(anon=False)
    def delete(self) -> bool:
        """
        Delete a given too, specified by id. username of BurstCubeTOO has to match yours.

        Returns
        -------
        bool
            Did this work? True | False
        """
        if self.validate_del():
            username = self.username
            if self.get():
                if self.username != username:
                    raise HTTPException(401, "BurstCubeTOO not owned by user.")

                response = self.table.delete_item(Key={"id": self.id})
                if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                    return True
                else:
                    HTTPException(
                        response["ResponseMetadata"]["HTTPStatusCode"],
                        "BurstCubeTOO not deleted.",
                    )
            return True
        return False

    def check_for_previous_toos(self) -> bool:
        """
        Check if previous BurstCubeTOOs match the one to be submited.

        Returns
        -------
        bool
            Does a previous BurstCubeTOO match this one? True | False
        """

        # Fetch previous BurstCubeTOOs

        response = self.table.scan(
            FilterExpression=Key("epoch").between(
                str(self.trigger_time - timedelta(seconds=1)),
                str(self.trigger_time + timedelta(seconds=1)),
            )
        )

        if "Items" not in response:
            # If there's none, we're good
            return False

        # Check if any of the previous BurstCubeTOOs match this one
        found = len(response["Items"])
        deleted = 0
        for resp in response["Items"]:
            too = BurstCubeTOOModelSchema.model_validate(resp)
            # If this BurstCubeTOO gives RA/Dec and the previous didn't then we
            # should override the previous one
            if too.ra is None and self.ra is not None:
                print(f"deleting old BurstCubeTOO {too.id} as RA now given")
                self.table.delete_item(Key={"id": too.id})
                deleted += 1
                continue

            # Check if burst time is more accurate
            if (
                too.trigger_time is not None
                and too.trigger_time.microsecond == 0
                and self.trigger_time.microsecond != 0
            ):
                print(
                    f"deleting old BurstCubeTOO {too.id} as triggertime more accurate."
                )
                self.table.delete_item(Key={"id": too.id})
                deleted += 1
                continue

            # Check if more exposure time requested
            if too.exposure > self.exposure:
                print(
                    f"deleting old BurstCubeTOO {too.id} as triggertime as more exposure time requested."
                )
                self.table.delete_item(Key={"id": too.id})
                deleted += 1
                continue

        if deleted == found:
            return False

        return True

    @check_api_key(anon=False)
    def put(self) -> bool:
        """
        Alter existing BurstCube BurstCubeTOO using ACROSS API using POST

        Returns
        -------
        bool
            Did this work? True | False
        """
        # Make sure the PUT request validates
        if not self.validate_put():
            return False

        # If this is just a POST (i.e. no ID set), then just POST it
        if self.id is None:
            return self.post()

        # If id is given, assume we're modifying an existing BurstCubeTOO.
        # Check if this BurstCubeTOO exists and is of the same username

        response = self.table.delete_item(Key={"id": self.id})
        # Check if the TOO exists
        if "Item" not in response:
            raise HTTPException(404, "BurstCubeTOO not found.")

        # Check if the username matches
        if response["Item"]["username"] != self.username:
            raise HTTPException(401, "BurstCubeTOO not owned by user.")

        # Write BurstCubeTOO to the database
        too = BurstCubeTOOModel(**self.schema.model_dump(mode="json"))
        too.save()

        return True

    def check_constraints(self):
        """
        Check if BurstCubeTOO parameters are valid.

        Returns
        -------
        bool
            Are BurstCubeTOO parameters valid? True | False
        """
        # Check if the trigger time is in the future
        if self.trigger_time > datetime.utcnow():
            self.warnings.append("Trigger time is in the future.")
            self.reason = TOOReason.other
            self.status = TOOStatus.rejected
            return False

        # Reject if trigger is > 48 hours old
        if self.trigger_time < datetime.utcnow() - timedelta(hours=48):
            self.reason = TOOReason.too_old
            self.warnings.append("Trigger is too old.")
            self.status = TOOStatus.rejected
            return False

        # Check if the trigger time is in the SAA
        saa = BurstCubeSAA(
            begin=self.trigger_time, end=self.trigger_time, stepsize=1 * u.s
        )
        if saa.insaa(self.trigger_time):
            self.warnings.append("Trigger time inside SAA.")
            self.reason = TOOReason.saa
            self.status = TOOStatus.rejected
            return False
        print(f"{self.ra=} {self.dec=} {self.healpix_loc=}")
        # Check if the trigger time is inside FOV
        if (
            self.ra is not None and self.dec is not None
        ) or self.healpix_loc is not None:
            fov = BurstCubeFOVCheck(
                begin=self.trigger_time,
                end=self.trigger_time,
                ra=self.ra,
                dec=self.dec,
                healpix_loc=self.healpix_loc,
                healpix_order=self.healpix_order,
                stepsize=1,
            )
            if fov.get() is True:
                # Check to see if trigger was in instrument FOV
                # (for BurstCube this means, anywhere but Earth Occulted)
                infov = fov.infov(self.trigger_time)
                if infov is False:
                    self.warnings.append("Trigger was occulted at T0.")
                    self.reason = TOOReason.earth_occult
                    self.status = TOOStatus.rejected
                    return False
                # If a BurstCubePoint is returned by infov, check if IFOV coverage is None or < 1%, report occulted
                # FIXME: Rather than hardcoding, this should be a parameter in config.py
                elif type(infov) is PointSchema and (
                    infov.infov is None or infov.infov < self.healpix_minprob
                ):
                    self.warnings.append("Trigger was occulted at T0.")
                    self.reason = TOOReason.earth_occult
                    self.status = TOOStatus.rejected
                    return False
                else:
                    self.warnings.append(
                        f"Probability inside FOV: {100*infov.infov:.2f}%."
                    )

        # Check if any part of the dump time is inside the SAA, warn if so
        if sum(saa.insaacons) > 0:
            self.warnings.append("Dump time partially inside SAA.")

        # Return true
        return True

    @check_api_key(anon=False)
    def post(self) -> bool:
        """
        Upload BurstCubeTOO to ACROSS API using POST

        Returns
        -------
        bool
            Did this work? True | False
        """
        # Validate supplied BurstCubeTOO values against the Schema
        if not self.validate_post():
            return False

        # Set the start and end time of the BurstCube event dump
        if self.begin is None or self.end is None:
            # If self.offset = 0, triggertime will be at the center of the dump window
            # FIXME - why is it necessary to convert offset into a int from a string?
            self.offset = int(self.offset)
            self.begin = round_time(self.trigger_time, 1) - timedelta(
                seconds=self.exposure + self.offset
            )
            self.end = self.begin + timedelta(seconds=self.exposure)

        # Check if this matches a previous BurstCubeTOO
        if self.check_for_previous_toos():
            raise HTTPException(200, "TOO already submitted")

        # Check for various TOO constraints
        if not self.check_constraints():
            self.warnings.append(
                "TOO request was recorded, but rejected due to a constraint."
            )

        # Compile all warnings and put them into too_info
        self.too_info = self.too_info + " ".join(self.warnings)

        # Write BurstCubeTOO to the database
        self.timestamp = datetime.utcnow()
        too = BurstCubeTOOModel(
            **BurstCubeTOOModelSchema.model_validate(self).model_dump(mode="json")
        )

        too.save()
        self.id = too.id

        return True
