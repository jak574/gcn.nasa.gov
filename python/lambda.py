# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from mangum import Mangum

from across_api.base.api import app  # type: ignore # noqa F401
import across_api.across.api  # type: ignore # noqa F401
import across_api.burstcube.api  # type: ignore # noqa F401
import across_api.fermi.api  # type: ignore # noqa F401
import across_api.nicer.api  # type: ignore # noqa F401
import across_api.nustar.api  # type: ignore # noqa F401
import across_api.swift.api  # type: ignore # noqa F401


from env import feature  # type: ignore

if feature("LABS"):
    handler = Mangum(app, api_gateway_base_path="/labs/api/v1", lifespan="off")
else:

    def handler(*_, **__):  # type: ignore
        return {"statusCode": 404}
