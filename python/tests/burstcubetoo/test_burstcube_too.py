import astropy.units as u  # type: ignore[import]
from across_api.burstcube.schema import TOOReason  # type: ignore[import]
from across_api.burstcube.toorequest import BurstCubeTOO  # type: ignore[import]
from across_api.burstcube.toorequest import BurstCubeTOORequests  # type: ignore[import]
from astropy.time.core import Time, TimeDelta  # type: ignore[import]


# @mock_aws
def test_burstcube_too_crud(
    username,
    burstcube_too,
    create_tle_table,
    create_too_table,
    mock_read_tle_db,
    mock_toorequest_table,
):
    from across_api.burstcube.toorequest import dynamodb_table

    assert dynamodb_table == mock_toorequest_table
    assert burstcube_too.post() is True
    assert burstcube_too.id is not None

    # Test fetching posted TOO
    too = BurstCubeTOO(id=burstcube_too.id)
    too.get()
    assert too.id == burstcube_too.id

    assert too.trigger_time == burstcube_too.trigger_time
    assert too.trigger_info == burstcube_too.trigger_info
    assert too.created_by == burstcube_too.username
    assert too.status == "Requested" or too.status == "Rejected"
    assert too.trigger_info.trigger_mission == "BurstCube"
    assert too.trigger_info.trigger_type == "GRB"
    # If the TOO was rejected, it should only be rejected due to SAA as no
    # coordinates were given, and trigger time is less than 48 hours old
    assert (
        too.reject_reason == TOOReason.none
        and too.status == "Requested"
        or too.reject_reason == TOOReason.saa
        and too.status == "Rejected"
    )

    # Test deleting posted TOO
    too = BurstCubeTOO(id=burstcube_too.id, username=username)
    too.delete()

    too = BurstCubeTOO(id=burstcube_too.id)
    too.get()
    assert too.status == "Deleted"

    # Test changing status to Approved
    too.status = "Approved"
    too.put()

    too = BurstCubeTOO(id=burstcube_too.id)
    too.get()
    assert too.status == "Approved"


def test_burstcube_old_too(
    burstcube_old_too,
    create_tle_table,
    create_too_table,
    mock_read_tle_db,
    mock_toorequest_table,
):
    assert burstcube_old_too.post() is True
    assert burstcube_old_too.trigger_time < Time.now() - TimeDelta(48 * u.hr)
    assert burstcube_old_too.status == "Rejected"
    assert "Trigger is too old." in burstcube_old_too.too_info
    assert burstcube_old_too.reject_reason == TOOReason.too_old


def test_burstcube_too_double_post(
    burstcube_too,
    create_tle_table,
    create_too_table,
    mock_read_tle_db,
    mock_toorequest_table,
):
    assert burstcube_too.post() is True
    try:
        burstcube_too.post()
    except Exception as e:
        assert e.status_code == 409
        assert e.detail == "BurstCubeTOO already exists."


def test_burstcube_toorequests(
    mock_toorequest_table,
    create_tle_table,
    create_too_table,
    mock_read_tle_db,
    now,
    trigger_info,
):
    # Submit three TOOs to the API
    now = Time("2024-03-01 16:40:00")
    newtoos = []
    for i in range(3):
        newtoo = BurstCubeTOO(
            trigger_time=now - TimeDelta(i * u.hr),
            trigger_info=trigger_info,
            username="testuser",
        )
        newtoo.post()
        newtoos.append(newtoo)

    # Check that BurstCube TOORequests returns the same number of TOOs as were
    # submitted, and that the contents match

    toos = BurstCubeTOORequests()
    toos.get()
    assert len(toos) == len(newtoos)
    assert toos[0].model_dump_json() == newtoos[0].schema.model_dump_json()
    assert toos[1].reject_reason == newtoos[1].reject_reason
    assert toos[1].model_dump_json() == newtoos[1].schema.model_dump_json()

    assert toos[2].model_dump_json() == newtoos[2].schema.model_dump_json()

    # Check the limit parameter
    toos = BurstCubeTOORequests(limit=1)
    toos.get()

    assert len(toos) == 1

    # Check the duration parameter by fetching only TOOs that arrived in the
    # last hour, this should be three. Then check the hour before, should be
    # zero
    toos = BurstCubeTOORequests(duration=1 * u.hr)
    toos.get()
    assert len(toos) == 3

    # Use begin and end to fetch the TOOs from the hour before the previous one
    # checked, should be no TOOs.
    toos = BurstCubeTOORequests(
        begin=Time.now() - TimeDelta(2 * u.hr), end=Time.now() - TimeDelta(2 * u.hr)
    )
    toos.get()
    assert len(toos) == 0
