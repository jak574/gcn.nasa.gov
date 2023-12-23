# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..api_db import Base
from ..base.models import PlanEntryModelBase


class NICERPlanEntryModel(PlanEntryModelBase, Base):
    """
    Represents a single entry in the NICER observation plan.

    Attributes:
        obsid (int): The observation ID.
        targetid (int): The target ID.
        mode (str): The observation mode.
    """

    __tablename__ = "nicer_plan"

    obsid: Mapped[int] = mapped_column(BigInteger())
    targetid: Mapped[int] = mapped_column(Integer())
    mode: Mapped[str] = mapped_column(String(20))
