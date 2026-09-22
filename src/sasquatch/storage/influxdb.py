"""Storage for interacting with an InfluxDB database v1 DB via the HTTP API."""

from typing import final

from influxdb import InfluxDBClient
from influxdb.line_protocol import quote_ident

from ..models.influxdb import (
    BasePoint,
    ClientDict,
    Measurement,
    Point,
    RetentionPolicy,
)

__all__ = ["InfluxDBStorage"]


@final
class InfluxDBStorage:
    """Storage to interact with an InfluxDB v1 DB via the HTTP API.

    Parameters
    ----------
    client
        An InfluxDB v1 client
    database
        The name of the database the all operations will be  scoped to.
    """

    def __init__(self, client: InfluxDBClient, database: str) -> None:
        self._client = client
        self._client.switch_database(database)

    def get_measurements(self) -> list[str]:
        """Get a list of all measurements in the database.

        Note that this gives all measurements in every retention policy, but
        there is no way to know which retention policy they came from.

        Returns
        -------
        list[str]
            A list of all measurement names in the database
        """
        raw = self._client.get_list_measurements()
        return [Measurement.model_validate(val).name for val in raw]

    def get_policies(self) -> list[str]:
        """Get a list of all retention policies in the database.

        Returns
        -------
        list[str]
            A list of all retention policies in the database
        """
        raw = self._client.get_list_retention_policies()
        return [RetentionPolicy.model_validate(val).name for val in raw]

    def get_latest_point(
        self, policy: str, measurement: str
    ) -> BasePoint | None:
        """Get the latest point from a measurement.

        Parameters
        ----------
        policy
            The retention policy of the measurement
        measurement
            The measurement

        Returns
        -------
        BasePoint
            Basic information about the most recent point in the database for
            the given measurement and retention policy.
        """
        source = ".".join(
            (
                quote_ident(policy),
                quote_ident(measurement),
            )
        )
        query = (
            f"SELECT * FROM {source}"  # noqa: S608
            f" ORDER BY time DESC"
            f" LIMIT 1"
        )
        result = self._client.query(query)
        points = list(result.get_points())
        if not points:
            return None

        return BasePoint.model_validate(
            {
                "measurement": measurement,
                "retention_policy": policy,
                "time": points[0]["time"],
            }
        )

    def write_points(
        self,
        points: list[Point],
        batch_size: int = 5000,
        retention_policy: str | None = None,
    ) -> None:
        """Write points to the database in the given retention policy.

        Parameters
        ----------
        points
            A list of points to write to the database
        batch_size
            The number of points to write in each batch
        retention_policy
            The retention policy to write the points to. If None, write to the
            default retention policy.
        """
        raw = [self._point_to_dict(point) for point in points]
        _ = self._client.write_points(
            points=raw,
            batch_size=batch_size,
            retention_policy=retention_policy,
        )

    def _point_to_dict(self, point: Point) -> ClientDict:
        """Return a dict suitable for writing with the InfluxDB client."""
        return {
            "measurement": point.measurement,
            "tags": point.tags,
            "fields": point.fields,
            "time": point.raw_time or point.time,
        }
