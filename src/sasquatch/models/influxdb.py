"""Models for working with InfluxDB."""

__all__ = ["ClientDict", "Measurement", "Point"]


from dataclasses import dataclass, field
from datetime import datetime
from typing import TypedDict

from pydantic import BaseModel

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


@dataclass(frozen=True)
class Point:
    """An InfluxDB point."""

    measurement: str
    """The measurement name."""

    timestamp: datetime
    """The timestamp of this point.

    Note that Python timestamps are only microsecond precision, but InfluxDB
    timestamps go to nanosecond precision.
    """
    tags: dict[str, ValidValue] = field(default_factory=dict)
    """Tags on this point."""

    fields: dict[str, ValidValue] = field(default_factory=dict)
    """Fields on this point."""

    raw_timestamp: str | None = None
    """A string of an integer unix timestamp to nanosecond precision.

    Store this if you need nanosecond precision.
    """

    def to_client_dict(self) -> ClientDict:
        """Return a dict suitable for writing with the InfluxDB client."""
        return {
            "measurement": self.measurement,
            "tags": self.tags,
            "fields": self.fields,
            "time": self.raw_timestamp or self.timestamp,
        }


class Measurement(BaseModel):
    """A measurment returned from the InfluxDB client."""

    name: str
    """The name of this measurement"""
