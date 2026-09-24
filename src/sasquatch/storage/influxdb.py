"""Storage for interacting with an InfluxDB database v1 DB via the HTTP API."""

import logging
from datetime import UTC, datetime, timedelta
from textwrap import dedent
from typing import final

from influxdb import InfluxDBClient
from influxdb.line_protocol import quote_ident
from influxdb.resultset import ResultSet

from ..models.influxdb import ClientDict, Measurement, Point, RetentionPolicy

__all__ = ["InfluxDBStorage"]

logger = logging.getLogger(__name__)


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
        self._database = database

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

    def exists(
        self,
        retention_policy: str,
        measurement: str,
    ) -> bool:
        """Return true if any data for the policy-qualified measurement exists.

        Parameters
        ----------
        retention_policy
            The retention policy of the measurement
        measurement
            The measurement
        """
        source = ".".join(
            (
                quote_ident(self._database),
                quote_ident(retention_policy),
                quote_ident(measurement),
            )
        )

        policies = self.get_policies()
        if len(policies) == 1:
            # This is MUCH faster than "SELECT * FROM <source> LIMIT 1", but
            # there is no way to scope it to a retention policy. The only case
            # where we can use it is if there is only one retention policy in
            # the db.
            query = dedent(f"""\
                SHOW SERIES
                FROM {source}
                LIMIT 1
            """)
        else:
            query = dedent(f"""\
                SELECT *
                FROM {source}
                ORDER BY time DESC
                LIMIT 1
            """)  # noqa: S608
        logger.info(f"Checking if measurement {source} exists")
        result = self._query(query)
        points = list(result.get_points())
        return bool(points)

    def is_stale(
        self,
        retention_policy: str,
        measurement: str,
        since: timedelta,
    ) -> bool:
        """Return True if a measurement doesn't have points since a given time.

        Parameters
        ----------
        retention_policy
            The retention policy of the measurement
        measurement
            The measurement
        since
            A measurement is active if it has points recorded in this amount of
            time before now.

        Returns
        -------
        bool
            Whether the measurement has points within the specified time before
            now.
        """
        source = ".".join(
            (
                quote_ident(retention_policy),
                quote_ident(measurement),
            )
        )
        time = datetime.now(UTC) - since

        query = dedent(f"""\
            SELECT * FROM {source}
            WHERE time >= '{time.isoformat()}'
            LIMIT 1
        """)  # noqa: S608
        logger.info(f"Checking if measurement {source} is stale")
        result = self._query(query)
        points = list(result.get_points())
        return not points

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

    def _query(self, query: str) -> ResultSet:
        """Execute a query and log how long it took.

        Parameters
        ----------
        query
            The query to execute.
        """
        start = datetime.now(UTC)
        try:
            return self._client.query(query)
        finally:
            elapsed = datetime.now(UTC) - start
            logger.debug(f"{query!r} - elapsed: {elapsed.total_seconds()}s")

    def _point_to_dict(self, point: Point) -> ClientDict:
        """Return a dict suitable for writing with the InfluxDB client."""
        return {
            "measurement": point.measurement,
            "tags": point.tags,
            "fields": point.fields,
            "time": point.raw_time or point.time,
        }
