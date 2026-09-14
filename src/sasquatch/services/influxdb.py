"""Service to interact with an InfluxDB database."""

from datetime import UTC, datetime, timedelta
from itertools import product
from typing import final

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
        since: timedelta | None = None,
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

        if retention_policy:
            policies = [retention_policy]
        else:
            policies = self._storage.get_policies()

        stale: list[BasePoint] = []

        # There is no way that I or the LLMs du jour can see to efficiently get
        # a list of retention-policy-qualified measurements. All we can do is
        # list all measurements, and list all retention policies, and query
        # every combination, even though some of those combinations might not
        # exist. In that case, the query just returns nothing.
        for policy, measurement in product(policies, measurements):
            point = self._storage.get_latest_point(
                policy=policy, measurement=measurement
            )
            if point:
                stale.append(point)

        if since:
            oldest = datetime.now(UTC) - since
            stale = [p for p in stale if p.time < oldest]
        return stale

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
