import aioboto3  # type: ignore[import]
import os

"""If running in Architect, return tables.table, else return boto3 dynamodb
table. This enables the use of moto to mock the dynamodb table in tests."""


async def dynamodb_resource():
    dynamodb_session = aioboto3.Session()
    if os.environ.get("ARC_ENV") == "testing" or os.environ.get("ARC_ENV") is None:
        return dynamodb_session.resource(
            "dynamodb", region_name="us-east-1", endpoint_url="http://localhost:5555"
        )
    else:
        return dynamodb_session.resource("dynamodb", region_name="us-east-1")

if os.environ.get("ARC_ENV") == "testing" or os.environ.get("ARC_ENV") is None:
    table_prefix = "remix-gcn-staging-"
else:
    table_prefix = ""