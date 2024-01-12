# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.


import astropy.units as u  # type: ignore
from astropy.time import Time  # type: ignore
from fastapi import HTTPException
from python.across_api.base.schema import PointSchema

from ..base.config import set_observatory
from ..base.pointing import PointingBase
from ..swift.observations import SwiftObservations
from ..swift.plan import SwiftPlan
from .config import SWIFT


@set_observatory(SWIFT)
class SwiftPointing(PointingBase):
    """
    Class to calculate Swift spacecraft pointing.

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
        Info about pointing query
    """

    def __init__(self, begin: Time, end: Time, stepsize: u.Quantity = 60 * u.s):
        self.begin = begin
        self.end = end
        self.stepsize = stepsize
        self.entries = []

        # Run GET automatically if parameters are valid, this is a GET only API
        if self.validate_get():
            self.get()

    def get(self) -> bool:
        """Calculate list of spacecraft pointings for a given date range.

        Returns
        -------
        bool
            True
        """

        # Fetch the observing timeline
        # FIXME: Only past obs
        try:
            observations = SwiftObservations(begin=self.begin, end=self.end)
            observations.get()
        except HTTPException:
            print("No obs for this date")

        plan = SwiftPlan(begin=self.begin, end=self.end)
        plan.get()

        # For each time, figure out which PlanEntry or ObsEntry was the target at the time, and record it
        for t in self.times:
            # If recorded observations exist, use them, otherwise use the plan
            if observations.plan_max is not None and t > observations.plan_max:
                ent = plan.which_entry(t)
            else:
                ent = observations.which_entry(t)  # type: ignore

            # If no entry, then the spacecraft is not observing
            if ent is None:
                self.entries.append(
                    PointSchema(
                        timestamp=t, ra=None, dec=None, roll=None, observing=True
                    )
                )
            else:
                # Check if the spacecraft is slewing, if yes, then the spacecraft is not observing
                observing = True
                if hasattr(ent, "slew"):
                    if t < ent.begin + ent.slew:
                        observing = False

                # Add the entry to the list
                self.entries.append(
                    PointSchema(
                        timestamp=t,
                        ra=ent.ra,
                        dec=ent.dec,
                        roll=ent.roll,
                        observing=observing,
                    )
                )
        return True
