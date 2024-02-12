from datetime import datetime

from ..across.jobs import check_cache, register_job
from ..base.config import set_observatory
from ..base.pointing import PointingBase
from ..base.schema import JobInfo
from .config import BURSTCUBE
from .schema import BurstCubePoint, BurstCubePointingGetSchema, BurstCubePointingSchema


@set_observatory(BURSTCUBE)
class BurstCubePointing(PointingBase):
    """Class to calculate BurstCube spacecraft pointing.

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
    status : JobInfo
        Status of pointing query
    """

    _schema = BurstCubePointingSchema
    _get_schema = BurstCubePointingGetSchema

    def __init__(self, begin: datetime, end: datetime, stepsize: int = 60):
        self.begin = begin
        self.end = end
        self.stepsize = stepsize
        self.entries = []
        self.status = JobInfo()
        if self._get_schema.model_validate(self):
            self.get()

    @check_cache
    @register_job
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
            BurstCubePoint(time=t, ra=0, dec=0, roll=0, observing=True)
            for t in self.times
        ]
        return True


# Short hand aliases
Pointing = BurstCubePointing
