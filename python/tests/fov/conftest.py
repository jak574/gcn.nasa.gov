# Define a TLE by hand. For the sake of this test, we're going to use the Fermi TLE on the day that GW170817 triggered.


import pytest

from across_api.base.schema import TLEEntry  # type: ignore[import]
from across_api.across.resolve import Resolve  # type: ignore[import]
from astropy.coordinates import SkyCoord  # type: ignore[import]
from astropy.time import Time  # type: ignore[import]
from across_api.burstcube.ephem import BurstCubeEphem  # type: ignore[import]
import astropy.units as u  # type: ignore[import]
from skyfield.api import load, EarthSatellite, utc  # type: ignore[import]


@pytest.fixture
def burstcube_tle():
    satname = "FGRST (GLAST)"
    tle1 = "1 33053U 08029A   17229.56317825 +.00000508 +00000-0 +12437-4 0  9995"
    tle2 = "2 33053 025.5829 306.0377 0012114 272.5539 087.3609 15.10926454506590"
    # Pretend we're Burstcube
    satname = "ISS (ZARYA)"

    tle = TLEEntry(satname=satname, tle1=tle1, tle2=tle2)

    return tle


@pytest.fixture
def at2017gfo_skycoord():
    # We use AT2017gfo as our trigger
    r = Resolve(name="AT2017gfo")
    skycoord = SkyCoord(r.ra, r.dec, unit="deg")
    return skycoord


@pytest.fixture
def at2017gfo_trigger_time():
    trigger_time = Time("2017-08-17 12:41:06.47")
    return trigger_time


@pytest.fixture
def burstcube_ephem(burstcube_tle, at2017gfo_trigger_time):
    # Calculate a BurstCube Ephemeris
    eph = BurstCubeEphem(
        begin=at2017gfo_trigger_time - 2 * u.s,
        end=at2017gfo_trigger_time + 2 * u.s,
        tle=burstcube_tle,
        stepsize=1 * u.s,
    )
    return eph


# Compute GCRS position using Skyfield library


@pytest.fixture
def skyfield_earth_skycoord(burstcube_tle, at2017gfo_trigger_time):
    ts = load.timescale()
    satellite = EarthSatellite(
        burstcube_tle.tle1, burstcube_tle.tle2, burstcube_tle.satname, ts
    )
    bodies = load("de421.bsp")
    nowts = ts.from_datetime(at2017gfo_trigger_time.datetime.replace(tzinfo=utc))
    earthpos = (bodies["Earth"] + satellite).at(nowts).observe(bodies["Earth"])
    radec = earthpos.radec()
    skyfield_earthra = radec[0]._degrees * u.deg
    skyfield_earthdec = radec[1].degrees * u.deg
    return SkyCoord(skyfield_earthra, skyfield_earthdec)
