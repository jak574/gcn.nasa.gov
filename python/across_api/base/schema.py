# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.


from datetime import datetime
from typing import Annotated, Any, List, Optional, Union

import astropy.units as u  # type: ignore
from arc import tables  # type: ignore
from astropy.constants import c, h  # type: ignore
from astropy.time import Time  # type: ignore
from astropy.coordinates import Latitude, Longitude, SkyCoord, CartesianRepresentation  # type: ignore
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
    AnyUrl,
)

# Define a Pydantic type for astropy Time objects, which will be serialized as
# a naive UTC datetime object, or a string in ISO format for JSON.
AstropyTime = Annotated[
    Time,
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
        lambda x: x.xyz.to(u.km).value.T.tolist()
        if type(x) is CartesianRepresentation
        else x.cartesian.xyz.to(u.km).value.T.tolist(),
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

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))


class CoordSchema(BaseSchema):
    """Schema that defines basic RA/Dec

    Parameters
    ----------
    ra : float
        Right Ascension value in degrees. Must be 0 or greater
        and lower than 360.
    dec : float
        Declination value in degrees. Must be between -90 and 90.
    """

    ra: float = Field(ge=0, lt=360)
    dec: float = Field(ge=-90, le=90)


class PositionSchema(CoordSchema):
    """
    Schema for representing position information with an error radius.

    Attributes
    ----------
    error : Optional[float]
        The error associated with the position. Defaults to None.
    """

    error: Optional[float] = None


class OptionalCoordSchema(BaseSchema):
    """Schema that defines basic RA/Dec

    Parameters
    ----------
    ra : Optional[float], optional
        Right Ascension value in degrees. Must be between 0 and 360.
    dec : Optional[float], optional
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
        data : Any
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
    error : Optional[float]
        The error associated with the position. Defaults to None.
    """

    error: Optional[float] = None


class DateRangeSchema(BaseSchema):
    """
    Schema that defines date range

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
        assert data.begin <= data.end, "End date should not be before begin"
        return data


class TLEGetSchema(BaseSchema):
    epoch: AstropyTime


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

    def write(self) -> None:
        """Write the TLE entry to the database."""
        table = tables.table(self.__tablename__)
        table.put_item(Item=self.model_dump(mode="json"))


class TLESchema(BaseSchema):
    tle: Optional[TLEEntry]


class SAAEntry(DateRangeSchema):
    """
    Simple class to hold a single SAA passage.

    Parameters
    ----------
    begin : datetime
        The start datetime of the SAA passage.
    end : datetime
        The end datetime of the SAA passage.
    """

    @property
    def length(self) -> float:
        """
        Calculate the length of the SAA passage in days.

        Returns:
            float: The length of the SAA passage in days.
        """
        return (self.end - self.begin).total_seconds() / 86400


class SAASchema(BaseSchema):
    """
    Returns from the SAA class

    Parameters
    ----------
    entries : List[SAAEntry]
        List of SAAEntry objects.
    """

    entries: List[SAAEntry]


class SAAGetSchema(DateRangeSchema):
    """Schema defining required parameters for GET

    Inherits
    --------
    DateRangeSchema : Schema
        Schema for date range data.
    """

    ...


# Pointing Schemas
class PointSchema(OptionalCoordSchema):
    """
    Schema defining a spacecraft pointing

    Parameters
    ----------
    timestamp : datetime
        The timestamp of the pointing.
    roll : float, optional
        The roll angle of the spacecraft.
    observing : bool
        Indicates whether the spacecraft is observing.
    infov : bool, float, None, optional
        Flag indicating whether an object is in the instrument field of view,
        can be True/False or a numerical fraction for larger uncertainties.

    Inherits
    --------
    CoordSchema : Schema
        Schema for coordinate data.
    """

    timestamp: datetime
    roll: Optional[float] = None
    observing: bool
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
    DateRangeSchema : class
        The class representing the date range of the plan entry.
    CoordSchema : class
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


class PlanGetSchemaBase(OptionalDateRangeSchema, OptionalCoordSchema):
    """
    Schema for retrieving plan information.

    Parameters
    ----------
    obsid : Union[str, int, None], optional
        The observation ID. Defaults to None.
    radius : Optional[float], optional
        The radius for searching plans. Defaults to None.
    """

    obsid: Union[str, int, None] = None
    radius: Optional[float] = None


class PlanSchemaBase(BaseSchema):
    """
    Base schema for a plan.

    Parameters
    ----------
    entries : List[PlanEntryBase]
        List of plan entries.
    """

    entries: List[PlanEntryBase]


# Ephem Schema


class EphemSchema(BaseSchema):
    """
    Schema for ephemeral data.

    Attributes
    ----------
    timestamp : List[datetime]
        List of timestamps.
    posvec : List[List[float]]
        List of position vectors for the spacecraft in GCRS.
    earthsize : List[float]
        List of the angular size of the Earth to the spacecraft.
    polevec : Optional[List[List[float]]], optional
        List of orbit pole vectors, by default None.
    velvec : Optional[List[List[float]]], optional
        List of spacecraft velocity vectors, by default None.
    sunvec : List[List[float]]
        List of sun vectors.
    moonvec : List[List[float]]
        List of moon vectors.
    latitude : List[float]
        List of latitudes.
    longitude : List[float]
        List of longitudes.
    stepsize : int, optional
        Step size, by default 60.
    """

    timestamp: List[datetime] = []
    posvec: List[List[float]]
    earthsize: List[float]
    polevec: Optional[List[List[float]]] = None
    velvec: Optional[List[List[float]]] = None
    sunvec: List[List[float]]
    moonvec: List[List[float]]
    latitude: List[float]
    longitude: List[float]
    stepsize: int = 60


class EphemGetSchema(DateRangeSchema):
    """Schema to define required parameters for a GET

    Parameters
    ----------
    stepsize : int, optional
        The step size in seconds (default is 60).

    """

    stepsize: int = 60
    ...


# Config Schema


class MissionSchema(BaseSchema):
    """
    Schema for representing mission information.

    Parameters
    ----------
    name : str
        The name of the mission.
    shortname : str
        The short name of the mission.
    agency : str
        The agency responsible for the mission.
    type : str
        The type of the mission.
    pi : str, optional
        The principal investigator of the mission. Defaults to None.
    description : str
        A description of the mission.
    website : AnyUrl
        The website URL of the mission.
    """

    name: str
    shortname: str
    agency: str
    type: str
    pi: Optional[str] = None
    description: str
    website: AnyUrl


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
    ra_off : float
        The angular offset in Right Ascension (RA) direction.
    dec_off : float
        The angular offset in Declination (Dec) direction.
    roll_off : float
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
    type : str
        The type of the FOV. Currently "AllSky", "Circular", "Square" and "HEALPix" are supported.
    area : float
        The area of the FOV in degrees**2.
    dimension : Optional[float]
        The dimension of the FOV.
    filename : Optional[str], optional
        The filename associated with the FOV.
    boresight : Optional[FOVOffsetSchema], optional
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
    name : str
        The name of the instrument.
    shortname : str
        The short name of the instrument.
    description : str
        The description of the instrument.
    website : AnyUrl
        The website URL of the instrument.
    energy_low : float
        The low energy range of the instrument.
    energy_high : float
        The high energy range of the instrument.
    fov : FOVSchema
        The field of view of the instrument.

    Properties
    ----------
    frequency_high : Quantity
        The high frequency range of the instrument.
    frequency_low : Quantity
        The low frequency range of the instrument.
    wavelength_high : Quantity
        The high wavelength range of the instrument.
    wavelength_low : Quantity
        The low wavelength range of the instrument.
    """

    name: str
    shortname: str
    description: str
    website: AnyUrl
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
    parallax : bool
        Flag indicating whether to include parallax when calculating Moon/Sun
        positions.
    apparent : bool
        Flag indicating whether to use apparent rather than astrometric
        positions.
    velocity : bool
        Flag indicating whether to include velocity calculation (needed for
        calculating pole or ram constraints).
    stepsize : int, optional
        Step size in seconds. Default is 60.
    earth_radius : float or None, optional
        Earth radius value. If None, it will be calculated. If float, it will
        be fixed to this value.
    """

    parallax: bool
    apparent: bool
    velocity: bool
    stepsize: int = 60
    earth_radius: Optional[
        float
    ] = None  # if None, calculate it, if float, fix to this value


class VisibilityConfigSchema(BaseSchema):
    """
    Schema for configuring visibility constraints.

    Attributes:
    earth_cons : bool
        Calculate Earth Constraint.
    moon_cons : bool
        Calculate Moon Constraint.
    sun_cons : bool
        Calculate Sun Constraint.
    ram_cons : bool
        Calculate Ram Constraint.
    pole_cons : bool
        Calculate Orbit Pole Constraint.
    saa_cons : bool
        Calculate time in SAA as a constraint.
    earthoccult : float
        How many degrees from Earth Limb can you look?
    moonoccult : float
        Degrees from center of Moon.
    sunoccult : float
        Degrees from center of Sun.
    ramsize : float, optional
        Degrees from center of ram direction. Defaults to 0.
    sunextra : float, optional
        Degrees buffer used for planning purpose. Defaults to 0.
    earthextra : float, optional
        Degrees buffer used for planning purpose. Defaults to 0.
    moonextra : float, optional
        Degrees buffer used for planning purpose. Defaults to 0.
    ramextra : float, optional
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
    earthoccult: float
    moonoccult: float
    sunoccult: float
    ramsize: float = 0
    # Extra degrees buffer used for planning purpose
    sunextra: float = 0
    earthextra: float = 0
    moonextra: float = 0
    ramextra: float = 0


class TLEConfigSchema(BaseSchema):
    """
    Schema for TLE configuration.

    Parameters
    ----------
    tle_bad : float
        The threshold for determining if a TLE is considered bad in units
        of days. I.e. if the TLE is older than this value, it is considered
        bad.
    tle_url : Optional[AnyUrl], optional
        The URL for retrieving TLE data. Defaults to None.
    tle_name : str
        The name of the TLE.
    tle_heasarc : Optional[AnyUrl], optional
        The URL for retrieving TLE data from HEASARC in their multi-TLE format.
        Defaults to None.
    tle_celestrak : Optional[AnyUrl], optional
        The URL for retrieving TLE data from Celestrak. Defaults to None.
    """

    tle_bad: float
    tle_url: Optional[AnyUrl] = None
    tle_name: str
    tle_concat: Optional[AnyUrl] = None
    tle_min_epoch: datetime


class ConfigSchema(BaseSchema):
    """
    Configuration schema for ACROSS API.

    Parameters
    ----------
    mission : MissionSchema
        The mission schema.
    instruments : List[InstrumentSchema]
        The list of instrument schemas.
    primary_instrument : int, optional
        The index of the primary instrument, defaults to 0.
    ephem : EphemConfigSchema
        The ephem configuration schema.
    visibility : VisibilityConfigSchema
        The visibility configuration schema.
    tle : TLEConfigSchema
        The TLE configuration schema.
    """

    mission: MissionSchema
    instruments: List[InstrumentSchema]
    primary_instrument: int = 0
    ephem: EphemConfigSchema
    visibility: VisibilityConfigSchema
    tle: TLEConfigSchema
