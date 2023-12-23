# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from typing import List

from ..base.schema import (
    BaseSchema,
    PlanEntryBase,
    PlanGetSchemaBase,
    PlanSchemaBase,
    VisWindow,
)


class NICERPlanEntry(PlanEntryBase):
    targetid: int
    obsid: int
    mode: str


class NICERPlanGetSchema(PlanGetSchemaBase):
    pass


class NICERPlanSchema(PlanSchemaBase):
    entries: List[NICERPlanEntry]  # type: ignore


class NICERPlanPutSchema(BaseSchema):
    entries: List[NICERPlanEntry]  # type: ignore


class NICERVisWindow(VisWindow):
    pass


class NICERVisibilitySchema(BaseSchema):
    entries: List[NICERVisWindow]
