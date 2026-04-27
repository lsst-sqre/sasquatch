"""Commands for working with InfluxDB line protocol measurements."""

from collections import defaultdict
from pathlib import Path

import click

from .line_protocol import (
    _escape_tag_key,
    _extract_measurement_and_field_keys,
    _extract_measurement_and_tag_keys,
    _extract_measurement_from_series_key,
    _find_unescaped_separator,
    _rewrite_file_in_place,
)


def _drop_measurement_from_line(line: str, measurement_to_drop: str) -> str:
    """Drop a measurement from a single line of InfluxDB line protocol."""
    line_ending = "\n" if line.endswith("\n") else ""
    content = line.removesuffix(line_ending)
    stripped_line = content.strip()
    if not stripped_line or stripped_line.startswith("#"):
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
    stripped_line = content.strip()
    if not stripped_line or stripped_line.startswith("#"):
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
