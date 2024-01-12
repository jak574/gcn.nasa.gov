# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

import io

import requests
from astropy.io.votable import parse_single_table  # type: ignore
from astropy.time import Time  # type: ignore
from fastapi import HTTPException, status

from ..base.config import set_observatory
from ..base.schema import VisWindow
from ..base.visibility import VisibilityBase
from .config import NICER


@set_observatory(NICER)
class NICERVisibility(VisibilityBase):
    """
    NICERVisibility calculator for NICER. Leverages the NICER visibility calculator
    website API in order to perform complex calculations that account for
    the structure of the ISS.

    This class is a wrapper of that API.
    """

    def get(self) -> bool:
        """
        Query NICER visibility using the online NICER NICERVisibility calculator.

        Returns
        -------
            Did it work? True | False
        """
        # Construct Query URL and parameters
        url = "https://heasarc.gsfc.nasa.gov/wsgi-scripts/nicer/visibility/nicervis.wsgi/get_vis"
        args = dict()
        args["POS"] = f"{self.ra},{self.dec}"

        # If beginning and end set, then append to URL
        if self.begin is not None and self.end is not None:
            args["T_MIN"] = self.begin.utc.datetime  # type: ignore
            args["T_MAX"] = self.end.utc.datetime  # type: ignore
        args["OUTPUT"] = "XML"

        # Request XML visibility VOTABLE from NICER website
        r = requests.get(url, params=args)  # type: ignore
        if r.status_code == 200:
            # Parse VOTABLE into VisWindow objects
            xmlvo = r.text
            votablefile = io.BytesIO(xmlvo.encode())
            votable = parse_single_table(votablefile)

            for i in range(len(votable.array.data)):  # type: ignore
                vw = VisWindow(
                    begin=Time(votable.array.data["UTC Start"][i]),
                    end=Time(votable.array.data["UTC End"][i]),
                    initial=votable.array.data["Initial Interference"][i].title(),
                    final=votable.array.data["Final Interference"][i].title(),
                )
                self.entries.append(vw)
            return True
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="NICER visibility tool offline.",
            )
