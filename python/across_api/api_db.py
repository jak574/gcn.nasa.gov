# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase  # type: ignore
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.functions import Function, func

from .api_secrets import (
    ACROSS_DB_HOST,
    ACROSS_DB_NAME,
    ACROSS_DB_PASSWD,
    ACROSS_DB_PORT,
    ACROSS_DB_USER,
)

# Database connection string
DATABASE = f"postgresql://{ACROSS_DB_USER}:{ACROSS_DB_PASSWD}@{ACROSS_DB_HOST}:{ACROSS_DB_PORT}/{ACROSS_DB_NAME}"
engine = create_engine(DATABASE, echo=False)


class Base(DeclarativeBase):
    @classmethod
    def create_table(cls) -> bool:
        """Create the table if it does not exist"""
        cls.metadata.create_all(engine)
        return True


def sa_angular_distance(
    ra: float, dec: float, racol: InstrumentedAttribute, deccol: InstrumentedAttribute
) -> Function:
    """
    SQLAlchemy function to calculate angular distance between
    RA/Dec in a database and a given RA/Dec in decimal degrees.

    Parameters
    ----------
    ra : float
        Right ascension in decimal degrees
    dec : float
        Declination in decimal degrees
    racol : InstrumentedAttribute
        SQLAlchemy model attribute
    deccol : InstrumentedAttribute
        SQLAlchemy model attribute

    Returns
    -------
    Function
        SQLAlchemy function calculating angular distance
    """
    # Convert arguments to radians
    ra = np.radians(ra)
    dec = np.radians(dec)

    # Return function to calculate angular separation
    return func.degrees(
        func.acos(
            func.cos(func.radians(deccol))
            * func.cos(dec)
            * func.cos(ra - func.radians(racol))
            + func.sin(func.radians(deccol)) * func.sin(dec)
        )
    )
