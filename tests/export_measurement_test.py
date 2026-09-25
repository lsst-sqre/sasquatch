"""Tests for exporting a measurement from a live DB."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from click.testing import CliRunner
from safir.testing.data import Data

from sasquatch.cli import main
from sasquatch.models.influxdb import Point
from sasquatch.services.influxdb import InfluxDBService
from tests.constants import INFLUXDB_CUSTOM_RETENTION_POLICY

from .support.influxdb_testcontainer import InfluxDBConnection

START_TIMESTAMP = datetime(year=2000, month=1, day=1, tzinfo=UTC)


def load_data(service: InfluxDBService) -> None:
    """Load test data."""
    points = [
        # measurement m1
        Point(
            retention_policy="autogen",
            measurement="m1",
            time=START_TIMESTAMP - timedelta(seconds=1),
            fields={"field1": "somefield"},
            tags={"tag1": "sometag"},
        ),
        Point(
            retention_policy="autogen",
            measurement="m1",
            time=START_TIMESTAMP - timedelta(seconds=2),
            fields={"field1": "somefield"},
            tags={"tag1": "sometag"},
        ),
        Point(
            retention_policy="autogen",
            measurement="m1",
            time=START_TIMESTAMP - timedelta(seconds=3),
            fields={"field1": "somefield"},
            tags={"tag1": "sometag"},
        ),
        Point(
            retention_policy="autogen",
            measurement="m1",
            time=START_TIMESTAMP - timedelta(seconds=4),
            fields={"field1": "somefield"},
            tags={"tag1": "sometag"},
        ),
        Point(
            retention_policy="autogen",
            measurement="m1",
            time=START_TIMESTAMP - timedelta(seconds=4),
            fields={"field1": "somefield"},
            tags={"tag1": "sometag"},
        ),
        # measurement m2
        Point(
            retention_policy="autogen",
            measurement="m2",
            time=START_TIMESTAMP - timedelta(seconds=4),
            fields={"field1": "somefield"},
            tags={"tag1": "sometag"},
        ),
    ]
    service.write_points(
        points, retention_policy=INFLUXDB_CUSTOM_RETENTION_POLICY
    )


def test_export_measurement(
    influxdb_connection: InfluxDBConnection,
    tmp_path: Path,
    data: Data,
) -> None:
    """Test the measurement list-stale command."""
    load_data(service=influxdb_connection.service)
    file = tmp_path / "export.lp"

    runner = CliRunner()
    cmd = [
        "influxdb",
        "export-measurement",
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
        "--measurement",
        "m1",
        "--output-file",
        str(file),
    ]
    result = runner.invoke(main, cmd)
    assert result.exit_code == 0
    contents = file.read_text()
    data.assert_text_matches(contents, "exported_measurement_1.pl")

    runner = CliRunner()
    cmd = [
        "influxdb",
        "export-measurement",
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
        "--measurement",
        "m2",
        "--output-file",
        str(file),
    ]
    result = runner.invoke(main, cmd)
    assert result.exit_code == 0
    contents = file.read_text()
    data.assert_text_matches(contents, "exported_measurement_2.pl")
