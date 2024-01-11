# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from typing import List, Literal, Optional

from ..base.schema import (
    BaseSchema,
    DateRangeSchema,
    OptionalCoordSchema,
    PlanEntryBase,
    PlanGetSchemaBase,
    PlanSchemaBase,
    UserSchema,
)


class SwiftPlanEntry(PlanEntryBase):
    roll: float
    obsid: str
    targetid: int
    segment: int
    xrtmode: int
    uvotmode: int
    batmode: int
    merit: int


class SwiftPlanGetSchema(PlanGetSchemaBase):
    pass


class SwiftPlanPutSchema(UserSchema):
    entries: List[SwiftPlanEntry]


class SwiftPlanEntriesSchema(BaseSchema):
    entries: List[SwiftPlanEntry]


class SwiftPlanSchema(PlanSchemaBase):
    entries: List[SwiftPlanEntry]  # type: ignore


class SwiftObsEntry(PlanEntryBase):
    slew: int
    roll: float
    obsid: str
    targetid: int
    segment: int
    xrtmode: int
    uvotmode: int
    batmode: int
    merit: int


class SwiftObservationsGetSchema(PlanGetSchemaBase):
    pass


class SwiftObservationsPutSchema(UserSchema):
    entries: List[SwiftObsEntry]
    pass


class SwiftObservationsSchema(PlanSchemaBase):
    entries: List[SwiftObsEntry]  # type: ignore


class SwiftFOVCheckGetSchema(OptionalCoordSchema, DateRangeSchema):
    healpix_loc: Optional[list] = None
    healpix_order: str = "nested"
    stepsize: int = 60
    earthoccult: bool = True
    instrument: Literal["XRT", "UVOT", "BAT"] = "XRT"


class SwiftFOVCheckSchema(BaseSchema):
    ...
