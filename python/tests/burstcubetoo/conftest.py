from unittest.mock import Mock

import astropy.units as u  # type: ignore[import]

import pytest
from across_api.base.schema import TLEEntry  # type: ignore[import]
from across_api.burstcube.schema import BurstCubeTOOModel  # type: ignore[import]
from across_api.burstcube.toorequest import BurstCubeTOO, BurstCubeTriggerInfo  # type: ignore[import]
from astropy.time import Time  # type: ignore
from astropy.time.core import TimeDelta  # type: ignore[import]


@pytest.fixture
def burstcube_tle():
    return TLEEntry(
        tle1="1 25544U 98067A   24059.70586912  .00019555  00000-0  35623-3 0  9995",
        tle2="2 25544  51.6410 137.9505 0005676 302.8794 193.7648 15.49465684441577",
        satname="ISS (ZARYA)",
    )


@pytest.fixture
def mock_read_tle_db(mocker, burstcube_tle):
    """Mock TLEEntry find_tles_between_epochs to return burstcube_tle fixture,
    so we don't spam space-track.org or CelesTrak."""
    mock = Mock()
    mocker.patch.object(
        TLEEntry, "find_tles_between_epochs", return_value=[burstcube_tle]
    )
    return mock


@pytest.fixture
def mock_toorequest_table(mocker, dynamodb):
    """Replace the call to arc.tables.table with the pytest-dynamodb
    dynamodb.Table call."""
    mock = mocker.patch(
        "across_api.burstcube.toorequest.dynamodb_table",
        wraps=lambda x: dynamodb.Table(x),
    )
    return mock


@pytest.fixture(scope="function")
def create_too_table(dynamodb):
    """Create the TOO Table"""
    dynamodb.create_table(
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
        ],
        TableName=BurstCubeTOOModel.__tablename__,
        KeySchema=[
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )


@pytest.fixture(scope="function")
def create_tle_table(dynamodb):
    """Create the TLE Table so we can use BurstCubeEphem in tests"""
    dynamodb.create_table(
        TableName="acrossapi_tle",
        AttributeDefinitions=[
            {"AttributeName": "satname", "AttributeType": "S"},
            {"AttributeName": "epoch", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "satname", "KeyType": "HASH"},
            {"AttributeName": "epoch", "KeyType": "RANGE"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )


@pytest.fixture
def now():
    yield Time.now()


@pytest.fixture
def username():
    yield "testuser"


@pytest.fixture
def trigger_info():
    yield BurstCubeTriggerInfo(
        trigger_mission="BurstCube",
        trigger_type="GRB",
    )


@pytest.fixture
def burstcube_too(username, now, trigger_info):
    too = BurstCubeTOO(
        trigger_time=now,
        trigger_info=trigger_info,
        username=username,
    )
    yield too


@pytest.fixture
def burstcube_old_too(username, trigger_info):
    too = BurstCubeTOO(
        trigger_time=Time.now() - TimeDelta(48 * u.hr),
        trigger_info=trigger_info,
        username=username,
    )
    yield too
