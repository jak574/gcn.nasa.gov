# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

import hashlib
from decimal import Decimal
from typing import Optional

from pydantic import computed_field

from ..api_db import dydbtable, dynamodb
from ..base.models import DynamoDBBase
from ..base.schema import OptionalCoordSchema


class BurstCubeTOOModel(OptionalCoordSchema, DynamoDBBase):
    __tablename__ = "burstcube_too"
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
    too_status: str = "Requested"
    too_info: str = ""

    @computed_field  # type: ignore
    @property
    def id(self) -> str:
        return hashlib.md5(
            f"{self.trigger_time}{self.trigger_mission}".encode()
        ).hexdigest()

    @classmethod
    def create_table(cls):
        # Create this DynamoDB table

        dynamodb.create_table(
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
            ],
            TableName=cls.__tablename__,
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )

    @classmethod
    def delete_table(cls):
        dydbtable(cls.__tablename__).delete()
