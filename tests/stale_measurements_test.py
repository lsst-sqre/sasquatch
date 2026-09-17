"""Tests for manipulating measurements in a live DB."""

from datetime import UTC, datetime, timedelta

from click.testing import CliRunner
from influxdb import InfluxDBClient

from sasquatch.cli import main
from sasquatch.models.influxdb import Point
from sasquatch.services.influxdb import InfluxDB

from .support.influxdb_testcontainer import InfluxDBConnection


def seconds(seconds: int) -> timedelta:
    """Return a timedelta representing a number of seconds."""
    return timedelta(seconds=seconds)


def load_data(client: InfluxDBClient) -> None:
    """Load test data."""
    db = InfluxDB(scoped_client=client)
    now = datetime.now(UTC)
    stale = timedelta(days=30)
    fresh = timedelta(days=25)

    stale_points = [
        Point(
            measurement="stale",
            timestamp=(now - stale - seconds(1)),
            fields={"field1": "first"},
        ),
        Point(
            measurement="stale2",
            timestamp=(now - stale - seconds(1)),
            fields={"field1": "first"},
        ),
    ]
    db.write_points(stale_points)

    fresh_points = [
        Point(
            measurement="fresh",
            timestamp=(now - fresh - seconds(1)),
            fields={"field1": "first"},
        ),
        Point(
            measurement="fresh2",
            timestamp=(now - fresh - seconds(1)),
            fields={"field1": "first"},
        ),
    ]
    db.write_points(fresh_points)


def test_list_stale(
    influxdb_connection: InfluxDBConnection,
) -> None:
    """Test the measurement list-stale command."""
    load_data(influxdb_connection.client)
    runner = CliRunner()
    cmd = [
        "influxdb",
        "list-stale-measurements",
        "--host",
        influxdb_connection.host,
        "--port",
        str(influxdb_connection.port),
        "--username",
        influxdb_connection.username,
        "--password",
        influxdb_connection.password,
        "--database",
        influxdb_connection.database,
    ]
    result = runner.invoke(main, cmd)
    assert result.output.splitlines() == ["stale", "stale2"]


def test_list_stale_takes_since(
    influxdb_connection: InfluxDBConnection,
) -> None:
    """Test the measurement list-stale command 'since' option."""
    load_data(influxdb_connection.client)
    runner = CliRunner()
    cmd = [
        "influxdb",
        "list-stale-measurements",
        "--host",
        influxdb_connection.host,
        "--port",
        str(influxdb_connection.port),
        "--username",
        influxdb_connection.username,
        "--password",
        influxdb_connection.password,
        "--database",
        influxdb_connection.database,
        "--since",
        "10d",
    ]
    result = runner.invoke(main, cmd)
    assert result.output.splitlines() == ["fresh", "fresh2", "stale", "stale2"]
