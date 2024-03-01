from typing import Any
import arc  # type: ignore[import]
import boto3  # type: ignore[import]
import os


def dynamodb_table(tablename) -> Any:
    """If running in Architect, return tables.table, else return boto3 dynamodb
    table. This enables the use of moto to mock the dynamodb table in tests."""
    if os.environ.get("ARC_ENV") is not None:
        return arc.tables.table(tablename)
    else:
        session = boto3.Session()
        return session.resource(
            "dynamodb", region_name="us-east-1", endpoint_url="http://localhost:5555"
        ).Table(f"remix-gcn-staging-{tablename}")
