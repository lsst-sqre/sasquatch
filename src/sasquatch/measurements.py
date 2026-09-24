"""Commands for working with InfluxDB line protocol measurements."""

from collections import defaultdict
from datetime import timedelta
from pathlib import Path

import click
from influxdb import InfluxDBClient
from safir.datetime import parse_timedelta

from .line_protocol import (
    _escape_tag_key,
    _extract_measurement_and_field_keys,
    _extract_measurement_and_tag_keys,
    _extract_measurement_from_series_key,
    _find_unescaped_separator,
    _is_metadata_line,
    _rewrite_file_in_place,
)
from .logging import configure_logging
from .services.influxdb import InfluxDBService
from .storage.influxdb import InfluxDBStorage


def _drop_measurement_from_line(line: str, measurement_to_drop: str) -> str:
    """Drop a measurement from a single line of InfluxDB line protocol."""
    line_ending = "\n" if line.endswith("\n") else ""
    content = line.removesuffix(line_ending)
    if _is_metadata_line(content):
        return line

    field_separator = _find_unescaped_separator(content, " ")
    if field_separator == -1:
        return line

    series_key = content[:field_separator]
    line_measurement = _extract_measurement_from_series_key(series_key)
    if line_measurement == measurement_to_drop:
        return ""

    return line


def _rename_measurement_in_line(
    line: str,
    measurement_to_rename: str,
    new_measurement_name: str,
) -> str:
    """Rename a measurement in a single line of InfluxDB line protocol."""
    line_ending = "\n" if line.endswith("\n") else ""
    content = line.removesuffix(line_ending)
    if _is_metadata_line(content):
        return line

    field_separator = _find_unescaped_separator(content, " ")
    if field_separator == -1:
        return line

    series_key = content[:field_separator]
    remainder = content[field_separator:]
    first_tag_separator = _find_unescaped_separator(series_key, ",")
    line_measurement = _extract_measurement_from_series_key(series_key)
    if line_measurement != measurement_to_rename:
        return line
    escaped_measurement = _escape_tag_key(new_measurement_name)
    if first_tag_separator == -1:
        return f"{escaped_measurement}{remainder}{line_ending}"
    suffix = series_key[first_tag_separator:]
    return f"{escaped_measurement}{suffix}{remainder}{line_ending}"


def extract_measurement_keys(
    file_path: str | Path,
) -> dict[str, dict[str, list[str]]]:
    """Read an InfluxDB line protocol file and return tag and field keys."""
    measurement_tags: defaultdict[str, set[str]] = defaultdict(set)
    measurement_fields: defaultdict[str, set[str]] = defaultdict(set)
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as file_handle:
        for raw_line in file_handle:
            parsed_tags = _extract_measurement_and_tag_keys(raw_line)
            if parsed_tags is not None:
                measurement, tag_keys = parsed_tags
                measurement_tags[measurement].update(tag_keys)
            else:
                continue

            parsed_fields = _extract_measurement_and_field_keys(raw_line)
            if parsed_fields is not None:
                _measurement, field_keys = parsed_fields
                measurement_fields[measurement].update(field_keys)

    return {
        measurement: {
            "tags": sorted(measurement_tags[measurement]),
            "fields": sorted(measurement_fields[measurement]),
        }
        for measurement in sorted(measurement_tags)
    }


def drop_measurement(file_path: str | Path, measurement_name: str) -> int:
    """Remove a measurement from an InfluxDB line protocol file in place."""
    return _rewrite_file_in_place(
        file_path,
        lambda line: _drop_measurement_from_line(line, measurement_name),
    )


def rename_measurement(
    file_path: str | Path,
    measurement_name: str,
    new_measurement_name: str,
) -> int:
    """Rename a measurement in an InfluxDB line protocol file in place."""
    return _rewrite_file_in_place(
        file_path,
        lambda line: _rename_measurement_in_line(
            line,
            measurement_name,
            new_measurement_name,
        ),
    )


@click.command("show-measurements")
@click.argument(
    "filename", type=click.Path(exists=True, dir_okay=False, path_type=str)
)
def show_measurements(filename: str) -> None:
    """List measurements with their tag keys and field keys."""
    result = extract_measurement_keys(filename)

    if not result:
        click.echo("No measurements found.")
        return

    for measurement in sorted(result):
        tags = ", ".join(result[measurement]["tags"]) or "(no tags)"
        fields = ", ".join(result[measurement]["fields"]) or "(no fields)"
        click.echo(f"{measurement}: tags={tags}; fields={fields}")


@click.command("drop-measurement")
@click.argument(
    "filename", type=click.Path(exists=True, dir_okay=False, path_type=str)
)
@click.argument("measurement_name", nargs=1)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show how many lines were modified.",
)
def drop_measurement_command(
    filename: str,
    measurement_name: str,
    *,
    verbose: bool,
) -> None:
    """Drop a measurement from a line protocol file."""
    modified_line_count = drop_measurement(filename, measurement_name)
    if verbose:
        click.echo(f"Modified {modified_line_count} lines.")


@click.command("rename-measurement")
@click.argument(
    "filename", type=click.Path(exists=True, dir_okay=False, path_type=str)
)
@click.argument("measurement_name", nargs=1)
@click.argument("new_measurement_name", nargs=1)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show how many lines were modified.",
)
def rename_measurement_command(
    filename: str,
    measurement_name: str,
    new_measurement_name: str,
    *,
    verbose: bool,
) -> None:
    """Rename a measurement in a line protocol file."""
    modified_line_count = rename_measurement(
        filename,
        measurement_name,
        new_measurement_name,
    )
    if verbose:
        click.echo(f"Modified {modified_line_count} lines.")


@click.command("list-stale-measurements")
@click.option("--host", required=True, help="InfluxDB host name.")
@click.option("--port", type=int, default=8086, show_default=True)
@click.option("--path", type=str, default="", show_default=True)
@click.option("--username", required=True, help="InfluxDB username.")
@click.option("--password", required=True, help="InfluxDB password.")
@click.option(
    "--database",
    required=True,
    help="Database to look in.",
)
@click.option(
    "--retention-policy",
    type=str,
    default=None,
    help="Retention policy to query. None to query all retention policies.",
)
@click.option(
    "--since",
    type=parse_timedelta,
    default="30d",
    help="A measurement is stale if it has seen no data in this much time.",
)
@click.option(
    "--log-level",
    type=click.Choice(
        ["debug", "info", "warning", "error", "critical"],
        case_sensitive=False,
    ),
    default="warning",
    show_default=True,
)
@click.option(
    "--timeout",
    type=float,
    default=None,
    help=(
        "The time (in seconds)to wait for a response from InfluxDB for any"
        "request. If this is None, then no timeout gets set on the connection."
        " Note that this only sets a timeout on the client side, a query might"
        " continue running on the server even if this timeout is exceeded."
        " Similarly, if the server is configured with a lower query timeout"
        " than this, the server will send an error response if that timeout is"
        " exceeded."
    ),
)
@click.option("--ssl", type=bool, default=False, show_default=True)
def list_stale_measurements_command(
    host: str,
    port: int,
    path: str,
    username: str,
    password: str,
    database: str,
    retention_policy: str | None,
    since: timedelta,
    timeout: float,
    log_level: str,
    *,
    ssl: bool,
) -> None:
    """List all measurements that haven't recieved data in a while."""
    configure_logging(level=log_level.upper())

    client = InfluxDBClient(
        host=host,
        port=port,
        path=path,
        ssl=ssl,
        verify_ssl=True,
        username=username,
        password=password,
        timeout=timeout,
    )
    storage = InfluxDBStorage(client=client, database=database)
    service = InfluxDBService(storage=storage)
    stale = service.get_stale_measurements(
        since=since, retention_policy=retention_policy
    )
    if not stale:
        click.echo("There are no stale measurements", err=True)
        return
    for point in stale:
        click.echo(f"{point.retention_policy} - {point.measurement}")


@click.command("export-measurement")
@click.option("--host", required=True, help="InfluxDB host name.")
@click.option("--port", type=int, default=8086, show_default=True)
@click.option("--path", type=str, default="", show_default=True)
@click.option("--username", required=True, help="InfluxDB username.")
@click.option("--password", required=True, help="InfluxDB password.")
@click.option(
    "--database",
    required=True,
    help="Database that contains the measurement.",
)
@click.option(
    "--retention-policy",
    type=str,
    help="Retention policy that contains the measurement.",
)
@click.option(
    "--measurement", required=True, type=str, help="The measurement to export"
)
@click.option(
    "--output-file",
    required=True,
    type=click.Path(allow_dash=True),
    help="The file to write the line protocol points to.",
)
@click.option(
    "--timeout",
    type=float,
    default=None,
    help=(
        "The time (in seconds)to wait for a response from InfluxDB for any"
        "request. If this is None, then no timeout gets set on the connection."
        " Note that this only sets a timeout on the client side, a query might"
        " continue running on the server even if this timeout is exceeded."
        " Similarly, if the server is configured with a lower query timeout"
        " than this, the server will send an error response if that timeout is"
        " exceeded."
    ),
)
@click.option("--ssl", type=bool, default=False, show_default=True)
def export_measurement_command(
    host: str,
    port: int,
    path: str,
    username: str,
    password: str,
    database: str,
    retention_policy: str,
    measurement: str,
    output_file: str,
    timeout: float,
    *,
    ssl: bool,
) -> None:
    """Export all points in a measurement to a line protocol file."""
    client = InfluxDBClient(
        host=host,
        port=port,
        path=path,
        ssl=ssl,
        verify_ssl=True,
        username=username,
        password=password,
        timeout=timeout,
        # There is a bug in the InfluxDB client where chunked query results do
        # not work with the default msgpack protocol.
        headers={"Accept": "application/json"},
    )
    storage = InfluxDBStorage(client=client, database=database)
    service = InfluxDBService(storage=storage)
    with click.open_file(output_file, "w") as f:
        service.export_measurement(
            retention_policy=retention_policy,
            measurement=measurement,
            file=f,
        )
