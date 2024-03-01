import astropy.units as u  # type: ignore[import]
from across_api.burstcube.schema import TOOReason  # type: ignore[import]
from across_api.burstcube.toorequest import BurstCubeTOO  # type: ignore[import]
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
