from typing import List, Literal, Optional

from ..base.schema import (
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
    stepsize: int = 60
    earthoccult: bool = True
    instrument: Literal["LAT", "GBM"] = "GBM"


class FermiFOVCheckSchema(BaseSchema):
    entries: List[FermiPoint]
