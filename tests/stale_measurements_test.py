"""Tests for manipulating measurements in a live DB."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from click.testing import CliRunner

from sasquatch.cli import main
from sasquatch.models.influxdb import Point
from sasquatch.services.influxdb import InfluxDBService
from tests.constants import INFLUXDB_CUSTOM_RETENTION_POLICY

from .support.influxdb_testcontainer import InfluxDBConnection


def output(points: list[Point], retention_policy: str) -> set[str]:
    """Return a set of expected output lines given points."""
    lines: set[str] = set()
    for point in points:
        line = f"{retention_policy} - {point.measurement}"
        lines.add(line)
    return lines


@dataclass
class Data:
    """A collection of test data."""

    stale_points: list[Point]
    """Stale points in the default retention policy."""

    fresh_points: list[Point]
    """Fresh points in the default retention policy."""

    stale_points_rp: list[Point]
    """Stale points in the custom retention policy."""

    fresh_points_rp: list[Point]
    """Fresh points in the custom retention policy."""


def load_data(service: InfluxDBService) -> Data:
    """Load test data.

    Returns
    -------
    Data
        The test data written to the database
    """
    now = datetime.now(UTC)
    stale = timedelta(days=30)
    fresh = timedelta(days=25)
    stale1 = now - stale - timedelta(seconds=1)
    stale2 = now - stale - timedelta(seconds=1)
    fresh1 = now - fresh - timedelta(seconds=1)
    fresh2 = now - fresh - timedelta(seconds=1)

    stale_points = [
        Point(
            retention_policy="autogen",
            measurement="stale",
            time=stale1,
            fields={"field1": "first"},
        ),
        Point(
            measurement="stale2",
            time=stale2,
            fields={"field1": "first"},
        ),
    ]
    service.write_points(stale_points)

    fresh_points = [
        Point(
            measurement="fresh",
            time=fresh1,
            fields={"field1": "first"},
        ),
        Point(
            measurement="fresh2",
            time=fresh2,
            fields={"field1": "first"},
        ),
    ]
    service.write_points(fresh_points)

    stale_points_rp = [
        Point(
            measurement="stale_custom_rp",
            time=stale1,
            fields={"field1": "first"},
        ),
        Point(
            measurement="stale2_custom_rp",
            time=stale2,
            fields={"field1": "first"},
        ),
    ]
    service.write_points(
        stale_points_rp, retention_policy=INFLUXDB_CUSTOM_RETENTION_POLICY
    )

    fresh_points_rp = [
        Point(
            measurement="fresh_custom_rp",
            time=fresh2,
            fields={"field1": "first"},
        ),
        Point(
            measurement="fresh2_custom_rp",
            time=fresh2,
            fields={"field1": "first"},
        ),
    ]
    service.write_points(
        fresh_points_rp, retention_policy=INFLUXDB_CUSTOM_RETENTION_POLICY
    )

    return Data(
        stale_points=stale_points,
        fresh_points=fresh_points,
        stale_points_rp=stale_points_rp,
        fresh_points_rp=fresh_points_rp,
    )


def test_list_stale(
    influxdb_connection: InfluxDBConnection,
) -> None:
    """Test the measurement list-stale command."""
    data = load_data(service=influxdb_connection.service)
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
    stale = output(data.stale_points, retention_policy="autogen")
    stale_rp = output(
        data.stale_points_rp,
        retention_policy=INFLUXDB_CUSTOM_RETENTION_POLICY,
    )
    expected = stale | stale_rp

    actual = set(result.output.splitlines())
    assert actual == expected


def test_list_stale_takes_since(
    influxdb_connection: InfluxDBConnection,
) -> None:
    """Test the measurement list-stale command 'since' option."""
    data = load_data(service=influxdb_connection.service)
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

    stale = output(data.stale_points, retention_policy="autogen")
    stale_rp = output(
        data.stale_points_rp,
        retention_policy=INFLUXDB_CUSTOM_RETENTION_POLICY,
    )
    fresh = output(data.fresh_points, retention_policy="autogen")
    fresh_rp = output(
        data.fresh_points_rp,
        retention_policy=INFLUXDB_CUSTOM_RETENTION_POLICY,
    )

    expected = stale | stale_rp | fresh | fresh_rp
    actual = set(result.output.splitlines())

    assert actual == expected


def test_list_stale_takes_retention_policy(
    influxdb_connection: InfluxDBConnection,
) -> None:
    """Test the measurement list-stale command 'retention_policy' option."""
    data = load_data(service=influxdb_connection.service)
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
        "--retention-policy",
        INFLUXDB_CUSTOM_RETENTION_POLICY,
    ]
    result = runner.invoke(main, cmd)

    stale = output(
        data.stale_points_rp, retention_policy=INFLUXDB_CUSTOM_RETENTION_POLICY
    )
    expected = stale
    actual = set(result.output.splitlines())

    assert actual == expected
