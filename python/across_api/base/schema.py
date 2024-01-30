# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

import io
from datetime import datetime
from typing import IO, Annotated, Any, List, Optional, Union

import astropy.units as u  # type: ignore
from arc import tables  # type: ignore
from astropy.constants import c, h  # type: ignore
from astropy.coordinates import (  # type: ignore
    CartesianRepresentation,
    Latitude,
    Longitude,
    SkyCoord,
)
from astropy.time import Time  # type: ignore
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    WithJsonSchema,
    computed_field,
    conlist,
    model_validator,
)
from pydantic_core import Url

# Define a Pydantic type for astropy Time objects, which will be serialized as
# a naive UTC datetime object, or a string in ISO format for JSON.
AstropyTime = Annotated[
    Time,
    BeforeValidator(lambda x: Time(x)),
    PlainSerializer(
        lambda x: x.utc.datetime,
        return_type=datetime,
    ),
    WithJsonSchema({"type": "string", "format": "date-time"}, mode="serialization"),
    WithJsonSchema({"type": "string", "format": "date-time"}, mode="validation"),
]
# Define a Pydantic type for list-type astropy Time objects, which will be
# serialized as a list of naive UTC datetime objects, or a list of strings in
# ISO format for JSON.
AstropyTimeList = Annotated[
    Time,
    BeforeValidator(lambda x: Time(x)),
    PlainSerializer(
        lambda x: x.utc.datetime.tolist(),
        return_type=List[datetime],
    ),
    WithJsonSchema(
        {"type": "array", "items": {"type": "string", "format": "date-time"}},
        mode="serialization",
    ),
    WithJsonSchema(
        {"type": "array", "items": {"type": "string", "format": "date-time"}},
        mode="validation",
    ),
]

# Define a Pydantic type for astropy Latitude, Longitude and u.Quantity list-type
# objects, which will be serialized as a list of float in units of degrees.
AstropyDegrees = Annotated[
    Union[Latitude, Longitude, u.Quantity],
    PlainSerializer(
        lambda x: x.deg.tolist()
        if type(x) is not u.Quantity
        else x.to(u.deg).value.tolist(),
        return_type=List[float],
    ),
]

AstropyAngle = Annotated[
    u.Quantity,
    PlainSerializer(
        lambda x: x.deg,
        return_type=float,
    ),
]

# Pydantic type to serialize astropy SkyCoord or CartesianRepresentation objects as a list
# of vectors in units of km
AstropyPositionVector = Annotated[
    Union[CartesianRepresentation, SkyCoord],
    PlainSerializer(
        lambda x: (
            x.xyz.to(u.km).value.T.tolist()
            if type(x) is CartesianRepresentation
            else x.cartesian.xyz.to(u.km).value.T.tolist()
        ),
        return_type=List[conlist(float, min_length=3, max_length=3)],  # type: ignore
    ),
]

# Pydantic type to serialize astropy CartesianRepresentation velocity objects as a list
# of vectors in units of km/s
AstropyVelocityVector = Annotated[
    CartesianRepresentation,
    PlainSerializer(
        lambda x: x.xyz.to(u.km / u.s).value.T.tolist(),
        return_type=List[conlist(float, min_length=3, max_length=3)],  # type: ignore
    ),
]

# Pydantic type to serialize astropy SkyCoord objects as a list
# of vectors with no units
AstropyUnitVector = Annotated[
    SkyCoord,
    PlainSerializer(
        lambda x: x.cartesian.xyz.value.T.tolist(),
        return_type=List[conlist(float, min_length=3, max_length=3)],  # type: ignore
    ),
]


# Pydantic type for a Astropy Time  in days
AstropyDays = Annotated[
    u.Quantity,
    PlainSerializer(
        lambda x: x.to(u.day).value,
        return_type=float,
    ),
]

# Pydantic type for a Astropy Time  in seconds
AstropySeconds = Annotated[
    u.Quantity,
    BeforeValidator(lambda x: x * u.s if type(x) is not u.Quantity else x.to(u.s)),
    PlainSerializer(
        lambda x: x.to(u.s).value,
        return_type=float,
    ),
    WithJsonSchema(
        {"type": "number"},
        mode="serialization",
    ),
    WithJsonSchema(
        {"type": "number"},
        mode="validation",
    ),
]


class BaseSchema(BaseModel):
    """
    Base class for schemas.

    This class provides a base implementation for schemas and defines the `from_attributes` method.
    Subclasses can inherit from this class and override the `from_attributes` method to define their own schema logic.
    """

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class CoordSchema(BaseSchema):
    """Schema that defines basic RA/Dec

    Parameters
    ----------
    ra
        Right Ascension value in degrees. Must be 0 or greater
        and lower than 360.
    dec
        Declination value in degrees. Must be between -90 and 90.
    """

    ra: float = Field(ge=0, lt=360)
    dec: float = Field(ge=-90, le=90)


class PositionSchema(CoordSchema):
    """
    Schema for representing position information with an error radius.

    Attributes
    ----------
    error
        The error associated with the position. Defaults to None.
    """

    error: Optional[float] = None


class OptionalCoordSchema(BaseSchema):
    """Schema that defines basic RA/Dec

    Parameters
    ----------
    ra
        Right Ascension value in degrees. Must be between 0 and 360.
    dec
        Declination value in degrees. Must be between -90 and 90.

    Methods
    -------
    check_ra_dec(data: Any) -> Any
        Validates that RA and Dec are both set or both not set.

    """

    ra: Optional[float] = Field(ge=0, lt=360, default=None)
    dec: Optional[float] = Field(ge=-90, le=90, default=None)

    @model_validator(mode="after")
    @classmethod
    def check_ra_dec(cls, data: Any) -> Any:
        """Validates that RA and Dec are both set or both not set.

        Parameters
        ----------
        data
            The data to be validated.

        Returns
        -------
        Any
            The validated data.

        Raises
        ------
        AssertionError
            If RA and Dec are not both set or both not set.

        """
        if data.ra is None or data.dec is None:
            assert data.ra == data.dec, "RA/Dec should both be set, or both not set"
        return data


class OptionalPositionSchema(OptionalCoordSchema):
    """
    Schema for representing position information with an error radius.

    Attributes
    ----------
    error
        The error associated with the position. Defaults to None.
    """

    error: Optional[float] = None


class DateRangeSchema(BaseSchema):
    """Schema that defines date range

    Parameters
    ----------
    begin
        The start date of the range.
    end
        The end date of the range.

    Returns
    -------
    data
        The validated data with converted dates.

    Raises
    ------
    AssertionError
        If the end date is before the begin date.

    """

    begin: AstropyTime
    end: AstropyTime

    @model_validator(mode="after")
    @classmethod
    def check_dates(cls, data: Any) -> Any:
        data.end = Time(data.end)
        data.begin = Time(data.begin)
        assert data.begin <= data.end, "End date should not be before begin"
        assert data.begin.isscalar, "Begin date should not be a list"
        assert data.end.isscalar, "End date should not be a list"
        return data


class OptionalDateRangeSchema(BaseSchema):
    """Schema that defines date range, which is optional

    Parameters
    ----------
    begin
        The beginning date of the range, by default None
    end
        The end date of the range, by default None

    Methods
    -------
    check_dates(data: Any) -> Any
        Validates the date range and ensures that the begin and end dates are set correctly.

    """

    begin: Optional[AstropyTime] = None
    end: Optional[AstropyTime] = None

    @model_validator(mode="after")
    @classmethod
    def check_dates(cls, data: Any) -> Any:
        """Validates the date range and ensures that the begin and end dates are set correctly.

        Parameters
        ----------
        data
            The data to be validated.

        Returns
        -------
        Any
            The validated data.

        Raises
        ------
        AssertionError
            If the begin and end dates are not both set or both not set.
            If the end date is before the begin date.

        """
        if data.begin is None or data.end is None:
            assert (
                data.begin == data.end
            ), "Begin/End should both be set, or both not set"
        if data.begin != data.end:
            assert data.begin <= data.end, "End date should not be before begin"

        return data


class UserSchema(BaseSchema):
    """
    Username/API key Schema for API calls that require authentication

    Parameters
    ----------
    username
        The username for authentication.
    api_key
        The API key for authentication.
    """

    username: str
    api_key: str


class VisWindow(DateRangeSchema):
    """
    Represents a visibility window.

    Parameters
    ----------
    begin
        The beginning of the window.
    end
        The end of the window.
    initial
        The main constraint that ends at the beginning of the window.
    final
        The main constraint that begins at the end of the window.
    """

    initial: str
    final: str


class VisibilitySchema(BaseSchema):
    """
    Schema for visibility classes.

    Parameters
    ----------
    entries: List[VisWindow]
        List of visibility windows.

        Information about the job status.
    """

    entries: List[VisWindow]


class VisibilityGetSchema(CoordSchema, DateRangeSchema):
    """
    Schema for getting visibility data.

    Parameters
    ----------
    stepsize
        The step size in seconds for the visibility data.

    Inherits
    --------
    CoordSchema
        Schema for coordinate data.
    DateRangeSchema
        Schema for date range data.
    """

    stepsize: AstropySeconds


class TLEEntry(BaseSchema):
    """
    Represents a single TLE entry in the TLE database.

    Parameters
    ----------
    satname
        The name of the satellite from the Satellite Catalog.
    tle1
        The first line of the TLE.
    tle2
        The second line of the TLE.

    Attributes
    ----------
    epoch
    """

    __tablename__ = "acrossapi_tle"
    satname: str  # Partition Key
    tle1: str = Field(min_length=69, max_length=69)
    tle2: str = Field(min_length=69, max_length=69)

    @computed_field  # type: ignore[misc]
    @property
    def epoch(self) -> AstropyTime:
        """
        Calculate the Epoch of the TLE file. See
        https://celestrak.org/columns/v04n03/#FAQ04 for more information on
        how the year / epoch encoding works.

        Returns
        -------
            The calculated epoch of the TLE.
        """
        # Extract epoch from TLE
        tleepoch = self.tle1.split()[3]

        # Convert 2 number year into 4 number year.
        tleyear = int(tleepoch[0:2])
        if tleyear < 57:
            year = 2000 + tleyear
        else:
            year = 1900 + tleyear

        # Convert day of year into float
        day_of_year = float(tleepoch[2:])

        # Return Time epoch
        return Time(f"{year}-01-01", scale="utc") + (day_of_year - 1) * u.day

    @classmethod
    def find_tles_between_epochs(
        cls, satname: str, start_epoch: Time, end_epoch: Time
    ) -> List[Any]:
        """
        Find TLE entries between two epochs in the TLE database for a given
        satellite TLE name.

        Arguments
        ---------
        satname
            The common name for the spacecraft based on the Satellite Catalog.
        start_epoch
            The start time over which to search for TLE entries.
        end_epoch
            The end time over which to search for TLE entries.

        Returns
        -------
            A list of TLEEntry objects between the specified epochs.
        """
        table = tables.table(cls.__tablename__)

        # Query the table for TLEs between the two epochs
        response = table.query(
            KeyConditionExpression="satname = :satname AND epoch BETWEEN :start_epoch AND :end_epoch",
            ExpressionAttributeValues={
                ":satname": satname,
                ":start_epoch": str(start_epoch.utc.datetime),
                ":end_epoch": str(end_epoch.utc.datetime),
            },
        )

        # Convert the response into a list of TLEEntry objects and return them
        return [cls(**item) for item in response["Items"]]

    def write(self):
        """Write the TLE entry to the database."""
        table = tables.table(self.__tablename__)
        table.put_item(Item=self.model_dump(mode="json"))

    @classmethod
    def delete_entry(cls, satname: str, epoch: datetime) -> bool:
        """Delete a TLE entry from the database."""
        table = tables.table(cls.__tablename__)
        return table.delete_item(Key={"satname": satname, "epoch": str(epoch)})

    @property
    def io(self) -> IO:
        """
        Return the file handle for the TLE database.
        """
        tletext = f"{self.satname}\n{self.tle1}\n{self.tle2}\n"
        return io.BytesIO(tletext.encode())


class TLESchema(BaseSchema):
    """
    Schema for representing a Two-Line Element (TLE) entry.

    Attributes
    ----------
    tle
        The TLE entry object.
    """

    tle: TLEEntry


class TLEGetSchema(BaseSchema):
    """
    Schema for getting TLE data.

    Parameters
    ----------
    epoch
        The epoch of the TLE.
    """

    epoch: AstropyTime


class SAAEntry(DateRangeSchema):
    """
    Simple class to hold a single SAA passage.

    Parameters
    ----------
    begin
        The start datetime of the SAA passage.
    end
        The end datetime of the SAA passage.
    """

    @property
    def length(self) -> u.Quantity:
        """
        Calculate the length of the SAA passage in days.

        Returns
        -------
            The length of the SAA passage
        """
        return self.end - self.begin


class SAASchema(BaseSchema):
    """
    Returns from the SAA class

    Parameters
    ----------
    entries
        List of SAAEntry objects.
    """

    entries: List[SAAEntry]


class SAAGetSchema(DateRangeSchema):
    """Schema defining required parameters for GET

    Inherits
    --------
    DateRangeSchema
        Schema for date range data.
    """

    ...


# Pointing Schemas
class PointSchema(BaseSchema):
    """
    Schema defining a spacecraft pointing

    Parameters
    ----------
    timestamp
        The timestamp of the pointing.
    roll
        The roll angle of the spacecraft.
    observing
        Indicates whether the spacecraft is observing.
    infov
        Flag indicating whether an object is in the instrument field of view,
        can be True/False or a numerical fraction for larger uncertainties.

    Inherits
    --------
    CoordSchema
        Schema for coordinate data.
    """

    timestamp: AstropyTime
    ra_point: Optional[float] = None
    dec_point: Optional[float] = None
    roll_point: Optional[float] = None
    observing: bool
    probability: Optional[float] = None
    infov: Union[bool, float, None] = None


class PointingSchema(BaseSchema):
    entries: List[PointSchema]


class PointingGetSchema(DateRangeSchema):
    stepsize: AstropySeconds


# Plan Schema
class PlanEntryBase(DateRangeSchema, CoordSchema):
    """
    Represents a base class for plan entries.

    Parameters
    ----------
    DateRangeSchema
        The class representing the date range of the plan entry.
    CoordSchema
        The class representing the coordinates of the plan entry.

    Attributes
    ----------
    targname: str
        The target name.
    exposure: int
        The exposure length in seconds.
    """

    targname: str
    exposure: int


class PlanGetSchemaBase(OptionalDateRangeSchema, OptionalCoordSchema):
    """
    Schema for retrieving plan information.

    Parameters
    ----------
    obsid
        The observation ID. Defaults to None.
    radius
        The radius for searching plans. Defaults to None.
    """

    obsid: Union[str, int, None] = None
    radius: Optional[float] = None


class PlanSchemaBase(BaseSchema):
    """
    Base schema for a plan.

    Parameters
    ----------
    entries
        List of plan entries.
    """

    entries: List[PlanEntryBase]


# Ephem Schema


class EphemSchema(BaseSchema):
    """
    Schema for ephemeris data.
    """

    timestamp: AstropyTimeList
    posvec: AstropyPositionVector
    earthsize: AstropyDegrees
    velvec: AstropyVelocityVector
    sun: AstropyPositionVector
    moon: AstropyPositionVector
    latitude: AstropyDegrees
    longitude: AstropyDegrees
    stepsize: AstropySeconds


class EphemGetSchema(DateRangeSchema):
    """Schema to define required parameters for a GET

    Parameters
    ----------
    stepsize
        The step size in seconds (default is 60).

    """

    stepsize: AstropySeconds
    ...


# Config Schema


class MissionSchema(BaseSchema):
    """
    Schema for representing mission information.

    Parameters
    ----------
    name
        The name of the mission.
    shortname
        The short name of the mission.
    agency
        The agency responsible for the mission.
    type
        The type of the mission.
    pi
        The principal investigator of the mission. Defaults to None.
    description
        A description of the mission.
    website
        The website URL of the mission.
    """

    name: str
    shortname: str
    agency: str
    type: str
    pi: Optional[str] = None
    description: str
    website: Url


class FOVCheckSchema(BaseSchema):
    """
    Schema for FOVCheck results.

    Parameters
    ----------
    entries
        List of FOVCheck entries.
    """

    entries: list  # FIXME: Add correct schema to list here


class FOVOffsetSchema(BaseSchema):
    """
    Schema to define an angular and rotational offset from the spacecraft pointing direction for an instrument.
    Tip: Add these values to the spacecraft pointing to get the instrument pointing and position angle.

    Parameters
    ----------
    ra_off
        The angular offset in Right Ascension (RA) direction.
    dec_off
        The angular offset in Declination (Dec) direction.
    roll_off
        The rotational offset around the spacecraft pointing direction.

    """

    ra_off: float
    dec_off: float
    roll_off: float


class FOVSchema(BaseSchema):
    """
    FOVSchema represents the field of view (FOV) of an instrument.

    Attributes
    ----------
    type
        The type of the FOV. Currently "AllSky", "Circular", "Square" and "HEALPix" are supported.
    area
        The area of the FOV in degrees**2.
    dimension
        The dimension of the FOV.
    filename
        The filename associated with the FOV.
    boresight
        The boresight offset of the FOV.

    """

    type: str
    area: float  # degrees**2
    dimension: Optional[float]
    filename: Optional[str] = None
    boresight: Optional[FOVOffsetSchema] = None


class InstrumentSchema(BaseSchema):
    """
    Schema for representing an instrument.

    Attributes
    ----------
    name
        The name of the instrument.
    shortname
        The short name of the instrument.
    description
        The description of the instrument.
    website
        The website URL of the instrument.
    energy_low
        The low energy range of the instrument.
    energy_high
        The high energy range of the instrument.
    fov
        The field of view of the instrument.

    Properties
    ----------
    frequency_high
        The high frequency range of the instrument.
    frequency_low
        The low frequency range of the instrument.
    wavelength_high
        The high wavelength range of the instrument.
    wavelength_low
        The low wavelength range of the instrument.
    """

    name: str
    shortname: str
    description: str
    website: Url
    energy_low: float
    energy_high: float
    fov: FOVSchema

    @property
    def frequency_high(self) -> u.Quantity:
        return ((self.energy_high * u.keV) / h).to(u.Hz)  # type: ignore

    @property
    def frequency_low(self) -> u.Quantity:
        return ((self.energy_low * u.keV) / h).to(u.Hz)  # type: ignore

    @property
    def wavelength_high(self) -> u.Quantity:
        return c / self.frequency_low.to(u.nm)

    @property
    def wavelength_low(self) -> u.Quantity:
        return c / self.frequency_high.to(u.nm)


class EphemConfigSchema(BaseSchema):
    """
    Schema for configuring ephemeris properties.

    Parameters
    ----------
    parallax
        Flag indicating whether to include parallax when calculating Moon/Sun
        positions.
    apparent
        Flag indicating whether to use apparent rather than astrometric
        positions.
    velocity
        Flag indicating whether to include velocity calculation (needed for
        calculating pole or ram constraints).
    stepsize
        Step size in seconds. Default is 60.
    earth_radius
        Earth radius value. If None, it will be calculated. If float, it will
        be fixed to this value.
    """

    parallax: bool
    apparent: bool
    velocity: bool
    stepsize: AstropySeconds
    earth_radius: Optional[
        AstropyAngle
    ] = None  # if None, calculate it, if float, fix to this value


class VisibilityConfigSchema(BaseSchema):
    """
    Schema for configuring visibility constraints.

    Attributes:
    earth_cons
        Calculate Earth Constraint.
    moon_cons
        Calculate Moon Constraint.
    sun_cons
        Calculate Sun Constraint.
    ram_cons
        Calculate Ram Constraint.
    pole_cons
        Calculate Orbit Pole Constraint.
    saa_cons
        Calculate time in SAA as a constraint.
    earthoccult
        How many degrees from Earth Limb can you look?
    moonoccult
        Degrees from center of Moon.
    sunoccult
        Degrees from center of Sun.
    ramsize
        Degrees from center of ram direction. Defaults to 0.
    sunextra
        Degrees buffer used for planning purpose. Defaults to 0.
    earthextra
        Degrees buffer used for planning purpose. Defaults to 0.
    moonextra
        Degrees buffer used for planning purpose. Defaults to 0.
    ramextra
        Degrees buffer used for planning purpose. Defaults to 0.
    """

    # Constraint switches, set to True to calculate this constraint
    earth_cons: bool
    moon_cons: bool
    sun_cons: bool
    ram_cons: bool
    pole_cons: bool
    saa_cons: bool
    # Constraint avoidance values
    earthoccult: AstropyAngle
    moonoccult: AstropyAngle
    sunoccult: AstropyAngle
    ramsize: AstropyAngle
    # Extra degrees buffer used for planning purpose
    sunextra: AstropyAngle
    earthextra: AstropyAngle
    moonextra: AstropyAngle
    ramextra: AstropyAngle


class TLEConfigSchema(BaseSchema):
    """
    Schema for TLE configuration.

    Parameters
    ----------
    tle_bad
        The threshold for determining if a TLE is considered bad in units
        of days. I.e. if the TLE is older than this value, it is considered
        bad.
    tle_url
        The URL for retrieving TLE data. Defaults to None.
    tle_name
        The name of the TLE.
    tle_heasarc
        The URL for retrieving TLE data from HEASARC in their multi-TLE format.
        Defaults to None.
    tle_celestrak
        The URL for retrieving TLE data from Celestrak. Defaults to None.
    """

    tle_bad: AstropyDays
    tle_url: Optional[Url] = None
    tle_name: str
    tle_norad_id: int
    tle_concat: Optional[Url] = None
    tle_min_epoch: AstropyTime


class ConfigSchema(BaseSchema):
    """
    Configuration schema for ACROSS API.

    Parameters
    ----------
    mission
        The mission schema.
    instruments
        The list of instrument schemas.
    primary_instrument
        The index of the primary instrument, defaults to 0.
    ephem
        The ephem configuration schema.
    visibility
        The visibility configuration schema.
    tle
        The TLE configuration schema.
    """

    mission: MissionSchema
    instruments: List[InstrumentSchema]
    primary_instrument: int = 0
    ephem: EphemConfigSchema
    visibility: VisibilityConfigSchema
    tle: TLEConfigSchema
