"""Service to interact with an InfluxDB database."""

from datetime import timedelta
from itertools import product
from textwrap import dedent
from typing import IO, Any, final

from ..exceptions import RetentionPolicyNotFoundError
from ..models.influxdb import BasePoint, Point
from ..storage.influxdb import InfluxDBStorage

__all__ = ["InfluxDBService"]


@final
class InfluxDBService:
    """Service to interact with a live InfluxDB v1 DB.

    Parameters
    ----------
    storage
        A configured InfluxDBStorage for interacting with the DB.
    """

    def __init__(
        self,
        storage: InfluxDBStorage,
    ) -> None:
        self._storage = storage

    def get_stale_measurements(
        self,
        since: timedelta,
        retention_policy: str | None = None,
    ) -> list[BasePoint]:
        """Get measurements that have not been written to since some time.

        Parameters
        ----------
        since
            The amount of time for the database to have no data written to be
            considered stale, or None to return the latest point from all
            measurements with any data at all.
        retention_policy
            The retention policy to query for measurements. If ``None``, then
            the default retention policy will be used.

        Returns
        -------
        list[BasePoint]
            A list of info about the latest points in each measurement.
        """
        measurements = self._storage.get_measurements()

        policies = self._storage.get_policies()
        if retention_policy:
            policies = [p for p in policies if p == retention_policy]
            if len(policies) == 0:
                msg = f"Retention policy {retention_policy} not found"
                raise RetentionPolicyNotFoundError(msg)

        stale: list[BasePoint] = []

        # There is no way that I or the LLMs du jour can see to efficiently get
        # a list of retention-policy-qualified measurements. All we can do is
        # list all measurements, and list all retention policies, and query
        # every combination, even though some of those combinations might not
        # exist. In that case, the query just returns nothing.
        for policy, measurement in product(policies, measurements):
            if not self._storage.exists(
                retention_policy=policy, measurement=measurement
            ):
                continue

            is_stale = self._storage.is_stale(
                retention_policy=policy, measurement=measurement, since=since
            )

            if is_stale:
                stale.append(
                    BasePoint(measurement=measurement, retention_policy=policy)
                )

        return stale

    def export_measurement(
        self, retention_policy: str, measurement: str, file: IO[Any]
    ) -> None:
        """Write a line protocol file with all points in a measurement.

        Parameters
        ----------
        retention_policy
            The retention policy that contains the measurement.
        measurement
            The name of the measurement.
        file
            An open stream to write to.
        """
        header = dedent(f"""\
            # DML
            # CONTEXT-DATABASE: {self._storage.database}
            # CONTEXT-RETENTION-POLICY: {retention_policy}

        """)
        file.writelines(header)

        for point in self._storage.get_all_lp(
            retention_policy=retention_policy, measurement=measurement
        ):
            file.writelines([f"{point}\n"])

    def write_points(
        self,
        points: list[Point],
        batch_size: int = 5000,
        retention_policy: str | None = None,
    ) -> None:
        """Write the list of points to InfluxDB.

        Parameters
        ----------
        points
            A list of points to write
        batch_size
            The number of points to write in one batch
        retention_policy
            The retention policy to add points to. If ``None``, then the
            default retention policy will be used.

        """
        self._storage.write_points(
            points, batch_size=batch_size, retention_policy=retention_policy
        )
