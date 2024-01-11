# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from typing import List

import astropy.units as u  # type: ignore
import numpy as np
from astropy.time import Time  # type: ignore

from .common import ACROSSAPIBase, round_time
from .schema import PointSchema, PointingGetSchema, PointingSchema


class PointingBase(ACROSSAPIBase):
    """Base class for pointing calculations.

    Parameters
    ----------
    begin : datetime
        Start time of pointing search
    end : datetime
        End time of pointing search
    stepsize : int
        Step size in seconds for pointing calculations

    Attributes
    ----------
    entries : list
        List of spacecraft pointings
    """

    _schema = PointingSchema
    _get_schema = PointingGetSchema

    entries: List[PointSchema]
    stepsize: u.Quantity = 60 * u.s
    begin: Time
    end: Time

    @property
    def times(self) -> List[Time]:
        begin = round_time(self.begin, self.stepsize)
        end = round_time(self.end, self.stepsize)
        number = int((end - begin) / self.stepsize)
        return begin + np.arange(number + 1) * self.stepsize
