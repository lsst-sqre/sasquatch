"""Service to interact with an InfluxDB v1 DB via the HTTP API."""

from datetime import UTC, datetime, timedelta
from typing import final

from influxdb import InfluxDBClient
from influxdb.line_protocol import quote_ident

from ..models.influxdb import Measurement, Point

__all__ = ["InfluxDB"]


@final
class InfluxDB:
    """Service to interact with an InfluxDB v1 DB via the HTTP API.

    Parameters
    ----------
    scoped_client
        An InfluxDB v1 client scoped to a database
    """

    def __init__(self, scoped_client: InfluxDBClient) -> None:
        self.client = scoped_client

    def get_stale_measurements(self, since: timedelta) -> list[str]:
        """Get measurements that have not been written to since some time.

        Parameters
        ----------
        since
            The amount of time for the database to have no data written to be
            considered stale

        Returns
        -------
        list[str]
            A list of stale measurement names
        """
        raw = self.client.get_list_measurements()
        measurements = [Measurement.model_validate(val).name for val in raw]
        stale_time = datetime.now(UTC) - since

        stale: list[str] = []
        for measurement in measurements:
            query = (
                f"SELECT * FROM {quote_ident(measurement)}"  # noqa: S608
                f" WHERE time > $stale_time"
                f" LIMIT 1"
            )
            params = {"stale_time": stale_time.isoformat()}
            result = self.client.query(query, bind_params=params)
            if not any(result.get_points()):
                stale.append(measurement)

        return stale

    def write_points(
        self, points: list[Point], batch_size: int = 5000
    ) -> None:
        """Write the list of points to InfluxDB.

        Parameters
        ----------
        points
            A list of points to write
        batch_size
            The number of points to write in one batch

        """
        _ = self.client.write_points(
            [point.to_client_dict() for point in points], batch_size=batch_size
        )
