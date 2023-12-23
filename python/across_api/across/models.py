# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

from ..base.models import DynamoDBBase  # type: ignore
from ..base.schema import BaseSchema


class UserModel(BaseSchema, DynamoDBBase):
    """
    Represents a user in the system.

    Attributes
    ----------
    username
        The username of the user.
    api_key
        The API key associated with the user.
    userlevel
        The user level. Defaults to 1.
    """

    __tablename__ = "acrossapi_users"

    username: str
    api_key: str
    userlevel: int = 1
