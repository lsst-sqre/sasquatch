"""Commands for working with InfluxDB line protocol fields."""

from collections import defaultdict
from pathlib import Path

import click

from .tags import _find_unescaped_separator, _split_unescaped, _unescape


def _find_unquoted_separator(text: str, separator: str) -> int:
    """Find the first unescaped separator outside quoted strings."""
    escaped = False
    in_quotes = False

    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_quotes = not in_quotes
            continue
        if char == separator and not in_quotes:
            return index

    return -1


def _split_fields(text: str) -> list[str]:
    """Split a field set on commas outside quoted strings."""
    parts: list[str] = []
    current: list[str] = []
    escaped = False
    in_quotes = False

    for char in text:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            current.append(char)
            escaped = True
            continue
        if char == '"':
            current.append(char)
            in_quotes = not in_quotes
            continue
        if char == "," and not in_quotes:
            parts.append("".join(current))
            current = []
            continue
        current.append(char)

    if escaped:
        current.append("\\")

    parts.append("".join(current))
    return parts


def _split_field(field: str) -> tuple[str, str] | None:
    """Split a field assignment into key and value."""
    separator_index = _find_unescaped_separator(field, "=")
    if separator_index == -1:
        return None

    field_key = _unescape(field[:separator_index])
    field_value = field[separator_index + 1 :]
    return field_key, field_value


def extract_measurement_field_keys(
    file_path: str | Path,
) -> dict[str, list[str]]:
    """Read an InfluxDB line protocol file and return field keys."""
    measurement_fields = defaultdict(set)
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as file_handle:
        for raw_line in file_handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            series_separator = _find_unescaped_separator(line, " ")
            if series_separator == -1:
                continue

            series_key = line[:series_separator]
            field_and_timestamp = line[series_separator + 1 :]
            field_end = _find_unquoted_separator(field_and_timestamp, " ")
            field_set = (
                field_and_timestamp
                if field_end == -1
                else field_and_timestamp[:field_end]
            )

            measurement_parts = _split_unescaped(series_key, ",")
            if not measurement_parts:
                continue

            measurement = _unescape(measurement_parts[0])
            measurement_fields[measurement]

            for field in _split_fields(field_set):
                field_parts = _split_field(field)
                if field_parts is not None:
                    field_key, _field_value = field_parts
                    measurement_fields[measurement].add(field_key)

    return {
        measurement: sorted(fields)
        for measurement, fields in measurement_fields.items()
    }


@click.command("show-fields")
@click.argument(
    "filename", type=click.Path(exists=True, dir_okay=False, path_type=str)
)
def show_fields(filename: str) -> None:
    """List measurements and unique field keys from a line protocol file."""
    result = extract_measurement_field_keys(filename)

    if not result:
        click.echo("No measurements found.")
        return

    for measurement in sorted(result):
        fields = (
            ", ".join(result[measurement])
            if result[measurement]
            else "(no fields)"
        )
        click.echo(f"{measurement}: {fields}")
