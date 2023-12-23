# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from datetime import datetime, timedelta
from typing import Any

from boto3.dynamodb.conditions import Key  # type: ignore
from pydantic import Field, computed_field
from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..api_db import dydbtable, dynamodb
from .schema import BaseSchema


class DynamoDBBase:
    __tablename__: str

    def save(self):
        table = dydbtable(self.__tablename__)
        table.put_item(Item=self.model_dump())

    @classmethod
    def get_by_key(cls, value: str, key: str):
        table = dydbtable(cls.__tablename__)
        response = table.query(KeyConditionExpression=Key(key).eq(value))
        items = response["Items"]
        if items:
            item = items[0]
            return cls(**item)
        return None

    @classmethod
    def delete_entry(cls, value: Any, key: str) -> bool:
        table = dydbtable(cls.__tablename__)
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


class TLEEntry(BaseSchema):
    """
    Represents a single TLE entry in the TLE database.

    Parameters
    ----------
    satname : str
        The name of the satellite from the Satellite Catalog.
    tle1 : str
        The first line of the TLE.
    tle2 : str
        The second line of the TLE.

    Attributes
    ----------
    epoch
    """

    __tablename__ = "acrossapi_tle"
    satname: str  # Partition Key
    tle1: str = Field(min_length=69, max_length=69)
    tle2: str = Field(min_length=69, max_length=69)

    @computed_field  # type: ignore[misc]
    @property
    def epoch(self) -> datetime:
        """
        Calculate the Epoch datetime of the TLE file. See
        https://celestrak.org/columns/v04n03/#FAQ04 for more information on
        how the year / epoch encoding works.

        Returns
        -------
            The calculated epoch of the TLE.
        """
        # Extract epoch from TLE
        tleepoch = self.tle1.split()[3]

        # Convert 2 number year into 4 number year.
        tleyear = int(tleepoch[0:2])
        if tleyear < 57:
            year = 2000 + tleyear
        else:
            year = 1900 + tleyear

        # Convert day of year into float
        day_of_year = float(tleepoch[2:])

        # Return datetime epoch
        return datetime(year, 1, 1) + timedelta(day_of_year - 1)

    @classmethod
    def find_tles_between_epochs(cls, satname, start_epoch, end_epoch):
        """
        Find TLE entries between two epochs in the TLE database for a given
        satellite TLE name.

        Arguments
        ---------
        satname
            The common name for the spacecraft based on the Satellite Catalog.
        start_epoch
            The start time over which to search for TLE entries.
        end_epoch
            The end time over which to search for TLE entries.

        Returns
        -------
            A list of TLEEntry objects between the specified epochs.
        """
        table = dydbtable(cls.__tablename__)

        # Query the table for TLEs between the two epochs
        response = table.query(
            KeyConditionExpression="satname = :satname AND epoch BETWEEN :start_epoch AND :end_epoch",
            ExpressionAttributeValues={
                ":satname": satname,
                ":start_epoch": str(start_epoch),
                ":end_epoch": str(end_epoch),
            },
        )

        # Convert the response into a list of TLEEntry objects and return them
        return [cls(**item) for item in response["Items"]]

    def write(self):
        """Write the TLE entry to the database."""
        table = dydbtable(self.__tablename__)
        table.put_item(Item=self.model_dump(mode="json"))

    @classmethod
    def delete_entry(cls, satname: str, epoch: datetime) -> bool:
        """Delete a TLE entry from the database."""
        table = dydbtable(cls.__tablename__)
        return table.delete_item(Key={"satname": satname, "epoch": str(epoch)})

    @classmethod
    def create_table(cls) -> bool:
        """Create the table if it does not exist."""
        table = dydbtable(cls.__tablename__)
        table = dynamodb.create_table(
            TableName=cls.__tablename__,
            KeySchema=[
                {"AttributeName": "satname", "KeyType": "HASH"},
                {"AttributeName": "epoch", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "satname", "AttributeType": "S"},
                {"AttributeName": "epoch", "AttributeType": "S"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
        )
        table.meta.client.get_waiter("table_exists").wait(TableName=cls.__tablename__)
        return True
