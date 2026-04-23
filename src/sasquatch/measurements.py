"""Commands for working with InfluxDB line protocol measurements."""

import fileinput
from collections import defaultdict
from pathlib import Path

import click

from .fields import _find_unquoted_separator, _split_field, _split_fields
from .tags import _find_unescaped_separator, _split_unescaped, _unescape


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
    parts = _split_unescaped(series_key, ",")
    if not parts:
        return line

    line_measurement = _unescape(parts[0])
    if line_measurement == measurement_to_drop:
        return ""

    return line


def extract_measurement_keys(
    file_path: str | Path,
) -> dict[str, dict[str, list[str]]]:
    """Read an InfluxDB line protocol file and return tag and field keys."""
    measurement_tags: defaultdict[str, set[str]] = defaultdict(set)
    measurement_fields: defaultdict[str, set[str]] = defaultdict(set)
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as file_handle:
        for raw_line in file_handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            field_separator = _find_unescaped_separator(line, " ")
            if field_separator == -1:
                continue

            series_key = line[:field_separator]
            field_and_timestamp = line[field_separator + 1 :]
            field_end = _find_unquoted_separator(field_and_timestamp, " ")
            field_set = (
                field_and_timestamp
                if field_end == -1
                else field_and_timestamp[:field_end]
            )

            parts = _split_unescaped(series_key, ",")
            if not parts:
                continue

            measurement = _unescape(parts[0])
            measurement_tags[measurement]
            measurement_fields[measurement]

            for tag in parts[1:]:
                separator_index = _find_unescaped_separator(tag, "=")
                if separator_index == -1:
                    continue
                tag_key = _unescape(tag[:separator_index])
                measurement_tags[measurement].add(tag_key)

            for field in _split_fields(field_set):
                field_parts = _split_field(field)
                if field_parts is None:
                    continue
                field_key, _field_value = field_parts
                measurement_fields[measurement].add(field_key)

    return {
        measurement: {
            "tags": sorted(measurement_tags[measurement]),
            "fields": sorted(measurement_fields[measurement]),
        }
        for measurement in sorted(measurement_tags)
    }


def drop_measurement(file_path: str | Path, measurement_name: str) -> int:
    """Remove a measurement from an InfluxDB line protocol file in place."""
    modified_line_count = 0
    with fileinput.input(
        files=(str(file_path),),
        inplace=True,
        encoding="utf-8",
    ) as lines:
        for line in lines:
            updated_line = _drop_measurement_from_line(line, measurement_name)
            if updated_line != line:
                modified_line_count += 1
            click.echo(updated_line, nl=False)
    return modified_line_count


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
