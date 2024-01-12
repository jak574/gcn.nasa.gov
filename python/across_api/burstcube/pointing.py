# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.


from astropy.time import Time  # type: ignore
import astropy.units as u  # type: ignore
from ..base.config import set_observatory
from ..base.pointing import PointingBase
from .config import BURSTCUBE
from .schema import PointSchema


@set_observatory(BURSTCUBE)
class BurstCubePointing(PointingBase):
    """Class to calculate BurstCube spacecraft pointing.

    Parameters
    ----------
    begin : Time
        Start time of pointing search
    end : Time
        End time of pointing search
    stepsize : int
        Step size in seconds for pointing calculations

    Attributes
    ----------
    entries : list
        List of spacecraft pointings
    status : JobInfo
        Status of pointing query
    """

    def __init__(self, begin: Time, end: Time, stepsize: u.Quantity = 60 * u.s):
        self.begin = begin
        self.end = end
        self.stepsize = stepsize
        self.entries = []

        if self._get_schema.model_validate(self):
            self.get()

    def get(self) -> bool:
        """Calculate list of spacecraft pointings for a given date range.

        Returns
        -------
        bool
            True
        """
        # BurstCube isn't a pointed instrument, so these are just dummy values. Note that they
        # have to be not None otherwise FOVCheck will think the spacecraft isn't observing.
        self.entries = [
            PointSchema(timestamp=t, ra=0, dec=0, roll=0, observing=True)
            for t in self.times
        ]
        return True
