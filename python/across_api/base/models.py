# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from arc import tables  # type: ignore
from datetime import datetime
from typing import Any

from boto3.dynamodb.conditions import Key  # type: ignore
from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm.base import Mapped  # type: ignore
from sqlalchemy.orm._orm_constructors import mapped_column


class DynamoDBBase:
    __tablename__: str

    def save(self, history: bool = False):
        if history is True:
            # History table needs to be created (in app.arc) alongside regular
            # table if we are going to record historic values of entries.
            table = tables.table(self.__tablename__ + "_history")
        else:
            table = tables.table(self.__tablename__)
        table.put_item(Item=self.model_dump())  # type: ignore

    @classmethod
    def get_by_key(cls, value: str, key: str):
        table = tables.table(cls.__tablename__)
        response = table.query(KeyConditionExpression=Key(key).eq(value))
        items = response["Items"]
        if items:
            item = items[0]
            return cls(**item)
        return None

    @classmethod
    def delete_entry(cls, value: Any, key: str) -> bool:
        table = tables.table(cls.__tablename__)
        return table.delete_item(Key={key: value})


class PlanEntryModelBase:
    """Base for PlanEntry."""

    begin: Mapped[datetime] = mapped_column(DateTime(timezone=False), primary_key=True)
    end: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=False,
        )
    )
    targname: Mapped[str] = mapped_column(String(30))
    ra: Mapped[float] = mapped_column(Float())
    dec: Mapped[float] = mapped_column(Float())
    exposure: Mapped[int] = mapped_column(Integer())
