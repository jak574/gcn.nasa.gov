# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

import hashlib
from decimal import Decimal
from typing import Optional

from pydantic import computed_field

from arc import tables  # type: ignore
from ..base.models import DynamoDBBase
from ..base.schema import BaseSchema


class BurstCubeTOOModel(BaseSchema, DynamoDBBase):
    __tablename__ = "burstcube_too"
    ra: Optional[Decimal] = None
    dec: Optional[Decimal] = None
    username: str
    timestamp: str
    trigger_mission: str
    trigger_instrument: str
    trigger_id: str
    trigger_time: str
    trigger_duration: Optional[Decimal] = None
    classification: Optional[str] = None
    justification: Optional[str] = None
    begin: Optional[str] = None
    end: Optional[str] = None
    exposure: Decimal = Decimal(200)
    offset: Decimal = Decimal(-50)
    reason: str = "None"
    status: str = "Requested"
    too_info: str = ""

    @computed_field  # type: ignore
    @property
    def id(self) -> str:
        return hashlib.md5(
            f"{self.trigger_time}{self.trigger_mission}".encode()
        ).hexdigest()

    @classmethod
    def delete_table(cls):
        tables.table(cls.__tablename__).delete()
