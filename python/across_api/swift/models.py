# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column  # type: ignore

from ..api_db import Base
from ..base.models import PlanEntryModelBase
from .schema import SwiftObsEntry


class SwiftObsEntryModel(PlanEntryModelBase, Base):
    """
    Database model for Swift observation entries.

    Inherits from PlanEntryModelBase and Base.
    """

    # Database structure and values
    __tablename__ = "swift_observations"
    _schema = SwiftObsEntry

    # Values
    slew: Mapped[int] = mapped_column(Integer())
    roll: Mapped[float] = mapped_column(Float())
    obsid: Mapped[str] = mapped_column(String())
    targetid: Mapped[int] = mapped_column(Integer())
    segment: Mapped[int] = mapped_column(Integer())
    xrtmode: Mapped[int] = mapped_column(Integer())
    uvotmode: Mapped[int] = mapped_column(Integer())
    batmode: Mapped[int] = mapped_column(Integer())
    merit: Mapped[int] = mapped_column(Integer())


class SwiftPlanEntryModel(PlanEntryModelBase, Base):
    """
    Represents a single entry in the Swift mission plan.

    Attributes:
        roll (float): The roll angle of the spacecraft in degrees.
        obsid (str): The observation ID.
        targetid (int): The target ID.
        segment (int): The segment number.
        xrtmode (int): The XRT observing mode.
        uvotmode (int): The UVOT observing mode.
        batmode (int): The BAT observing mode.
        merit (int): The merit value of the observation.
    """

    # Database structure and values
    __tablename__ = "swift_plan"

    # Values
    roll: Mapped[float] = mapped_column(Float())
    obsid: Mapped[str] = mapped_column(String())
    targetid: Mapped[int] = mapped_column(Integer())
    segment: Mapped[int] = mapped_column(Integer())
    xrtmode: Mapped[int] = mapped_column(Integer())
    uvotmode: Mapped[int] = mapped_column(Integer())
    batmode: Mapped[int] = mapped_column(Integer())
    merit: Mapped[int] = mapped_column(Integer())
