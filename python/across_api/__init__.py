# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from astropy.utils import iers  # type: ignore

from ._version import __version__  # noqa: F401

iers.conf.auto_download = False
