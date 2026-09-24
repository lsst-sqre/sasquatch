"""Models for working with InfluxDB."""

__all__ = [
    "BasePoint",
    "ClientDict",
    "Measurement",
    "Point",
    "RetentionPolicy",
]


from datetime import datetime
from typing import TypedDict

from pydantic import AwareDatetime, BaseModel, Field

type ValidValue = str | float | int | bool


class ClientDict(TypedDict):
    """A dictionary to pass to the InfluxDB client for writing."""

    measurement: str
    """The measurement name."""

    tags: dict[str, ValidValue]
    """Tags on this point."""

    fields: dict[str, ValidValue]
    """Fields on this point."""

    time: str | datetime
    """The timestamp of this point."""


class BasePoint(BaseModel):
    """Basic information about a point."""

    measurement: str
    """The measurement name."""

    retention_policy: str | None = None
    """The name of the retention policy for the measurement."""


class Point(BasePoint):
    """An InfluxDB point."""

    tags: dict[str, ValidValue] = Field(default_factory=dict)
    """Tags on this point."""

    fields: dict[str, ValidValue] = Field(default_factory=dict)
    """Fields on this point."""

    time: AwareDatetime
    """The timestamp of this point.

    Note that Python timestamps are only microsecond precision, but InfluxDB
    timestamps go to nanosecond precision.
    """

    raw_time: str | None = None
    """A string of an integer unix timestamp to nanosecond precision.

    Store this if you need nanosecond precision.
    """


class Measurement(BaseModel):
    """A measurment returned from the InfluxDB client."""

    name: str
    """The name of this measurement"""


class RetentionPolicy(BaseModel):
    """A retention policy returned from the InfluxDB client."""

    name: str
    """The name of this retention policy."""
