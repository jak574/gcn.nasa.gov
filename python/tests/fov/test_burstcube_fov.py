from across_api.burstcube.fov import BurstCubeFOV  # type: ignore[import]
import astropy.units as u  # type: ignore[import]


def test_burstcube_fov_point_source(
    burstcube_ephem, at2017gfo_skycoord, at2017gfo_trigger_time, skyfield_earth_skycoord
):
    """Skyfield calculation of Earth Occultation and ACROSS API should give the same answer."""
    fov = BurstCubeFOV()
    assert (
        at2017gfo_skycoord.separation(skyfield_earth_skycoord) > 70 * u.deg
    ), "This trigger should be not earth occulted"
    assert (
        fov.probability_infov(
            skycoord=at2017gfo_skycoord,
            time=at2017gfo_trigger_time,
            ephem=burstcube_ephem,
        )
        == 1.0
    ), "BurstCubeFOV should report this trigger as outside of Earth Occultation"
