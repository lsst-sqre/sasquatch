"""Commands for working with InfluxDB line protocol fields."""

import fileinput
from collections import defaultdict
from pathlib import Path

import click

from .tags import (
    _escape_tag_key,
    _find_unescaped_separator,
    _split_unescaped,
    _unescape,
)


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


def _drop_field_from_line(
    line: str,
    field_key_to_drop: str,
    *,
    measurement: str | None = None,
) -> str:
    """Drop a field key from a single line of InfluxDB line protocol."""
    line_ending = "\n" if line.endswith("\n") else ""
    content = line.removesuffix(line_ending)
    stripped_line = content.strip()
    if not stripped_line or stripped_line.startswith("#"):
        return line

    series_separator = _find_unescaped_separator(content, " ")
    if series_separator == -1:
        return line

    series_key = content[:series_separator]
    field_and_timestamp = content[series_separator + 1 :]
    field_end = _find_unquoted_separator(field_and_timestamp, " ")
    field_set = (
        field_and_timestamp
        if field_end == -1
        else field_and_timestamp[:field_end]
    )
    remainder = "" if field_end == -1 else field_and_timestamp[field_end:]
    measurement_parts = _split_unescaped(series_key, ",")
    if not measurement_parts:
        return line

    line_measurement = _unescape(measurement_parts[0])
    if measurement is not None and line_measurement != measurement:
        return line

    kept_fields: list[str] = []
    for field in _split_fields(field_set):
        field_parts = _split_field(field)
        if field_parts is None:
            kept_fields.append(field)
            continue
        field_key, _field_value = field_parts
        if field_key != field_key_to_drop:
            kept_fields.append(field)

    if not kept_fields:
        return ""

    return f"{series_key} {','.join(kept_fields)}{remainder}{line_ending}"


def _rename_field_in_line(
    line: str,
    field_key_to_rename: str,
    new_field_key: str,
    *,
    measurement: str | None = None,
) -> str:
    """Rename a field key in a single line of InfluxDB line protocol."""
    line_ending = "\n" if line.endswith("\n") else ""
    content = line.removesuffix(line_ending)
    stripped_line = content.strip()
    if not stripped_line or stripped_line.startswith("#"):
        return line

    series_separator = _find_unescaped_separator(content, " ")
    if series_separator == -1:
        return line

    series_key = content[:series_separator]
    field_and_timestamp = content[series_separator + 1 :]
    field_end = _find_unquoted_separator(field_and_timestamp, " ")
    field_set = (
        field_and_timestamp
        if field_end == -1
        else field_and_timestamp[:field_end]
    )
    remainder = "" if field_end == -1 else field_and_timestamp[field_end:]
    measurement_parts = _split_unescaped(series_key, ",")
    if not measurement_parts:
        return line

    line_measurement = _unescape(measurement_parts[0])
    if measurement is not None and line_measurement != measurement:
        return line

    renamed_fields: list[str] = []
    escaped_new_field_key = _escape_tag_key(new_field_key)
    for field in _split_fields(field_set):
        separator_index = _find_unescaped_separator(field, "=")
        if separator_index == -1:
            renamed_fields.append(field)
            continue

        field_key = _unescape(field[:separator_index])
        if field_key == field_key_to_rename:
            renamed_fields.append(
                f"{escaped_new_field_key}={field[separator_index + 1 :]}"
            )
        else:
            renamed_fields.append(field)

    return f"{series_key} {','.join(renamed_fields)}{remainder}{line_ending}"


def extract_measurement_field_keys(
    file_path: str | Path,
) -> dict[str, list[str]]:
    """Read an InfluxDB line protocol file and return field keys."""
    measurement_fields: defaultdict[str, set[str]] = defaultdict(set)
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


def drop_measurement_field_key(
    file_path: str | Path,
    field_key_to_drop: str,
    *,
    measurement: str | None = None,
) -> int:
    """Remove a field key from an InfluxDB line protocol file in place."""
    modified_line_count = 0
    with fileinput.input(
        files=(str(file_path),),
        inplace=True,
        encoding="utf-8",
    ) as lines:
        for line in lines:
            updated_line = _drop_field_from_line(
                line,
                field_key_to_drop,
                measurement=measurement,
            )
            if updated_line != line:
                modified_line_count += 1
            click.echo(updated_line, nl=False)
    return modified_line_count


def rename_measurement_field_key(
    file_path: str | Path,
    field_key_to_rename: str,
    new_field_key: str,
    *,
    measurement: str | None = None,
) -> int:
    """Rename a field key in an InfluxDB line protocol file in place."""
    modified_line_count = 0
    with fileinput.input(
        files=(str(file_path),),
        inplace=True,
        encoding="utf-8",
    ) as lines:
        for line in lines:
            updated_line = _rename_field_in_line(
                line,
                field_key_to_rename,
                new_field_key,
                measurement=measurement,
            )
            if updated_line != line:
                modified_line_count += 1
            click.echo(updated_line, nl=False)
    return modified_line_count


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


@click.command("drop-field")
@click.argument(
    "filename", type=click.Path(exists=True, dir_okay=False, path_type=str)
)
@click.argument("field_key", nargs=1)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show how many lines were modified.",
)
@click.option(
    "-m",
    "--measurement",
    type=str,
    default=None,
    help="Only drop the field from this measurement.",
)
def drop_field(
    filename: str,
    field_key: str,
    *,
    verbose: bool,
    measurement: str | None,
) -> None:
    """Drop a field key from a line protocol file."""
    modified_line_count = drop_measurement_field_key(
        filename,
        field_key,
        measurement=measurement,
    )
    if verbose:
        click.echo(f"Modified {modified_line_count} lines.")


@click.command("rename-field")
@click.argument(
    "filename", type=click.Path(exists=True, dir_okay=False, path_type=str)
)
@click.argument("field_key", nargs=1)
@click.argument("new_field_key", nargs=1)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show how many lines were modified.",
)
@click.option(
    "-m",
    "--measurement",
    type=str,
    default=None,
    help="Only rename the field on this measurement.",
)
def rename_field(
    filename: str,
    field_key: str,
    new_field_key: str,
    *,
    verbose: bool,
    measurement: str | None,
) -> None:
    """Rename a field key in a line protocol file."""
    modified_line_count = rename_measurement_field_key(
        filename,
        field_key,
        new_field_key,
        measurement=measurement,
    )
    if verbose:
        click.echo(f"Modified {modified_line_count} lines.")
