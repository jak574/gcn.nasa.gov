# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from typing import List, Literal, Optional

import astropy.units as u  # type: ignore

from ..base.schema import (
    AstropySeconds,
    BaseSchema,
    DateRangeSchema,
    OptionalCoordSchema,
    PointBase,
    PointingGetSchemaBase,
    PointingSchemaBase,
)


class FermiPoint(PointBase):
    pass


class FermiPointingSchema(PointingSchemaBase):
    pass


class FermiPointingGetSchema(PointingGetSchemaBase):
    pass


class FermiFOVCheckGetSchema(OptionalCoordSchema, DateRangeSchema):
    healpix_loc: Optional[list] = None
    healpix_order: str = "nested"
    stepsize: AstropySeconds = 60 * u.s
    earthoccult: bool = True
    instrument: Literal["LAT", "GBM"] = "GBM"


class FermiFOVCheckSchema(BaseSchema):
    entries: List[FermiPoint]
