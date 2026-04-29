"""Commands for working with InfluxDB line protocol fields."""

from collections import defaultdict
from pathlib import Path

import click

from .line_protocol import (
    _escape_tag_key,
    _extract_measurement_and_field_keys,
    _extract_measurement_from_series_key,
    _is_metadata_line,
    _iter_field_ranges,
    _rewrite_file_in_place,
    _split_record_content,
    _unescape_if_needed,
)


def _drop_field_from_line(
    line: str,
    field_key_to_drop: str,
    *,
    measurement: str | None = None,
) -> str:
    """Drop a field key from a single line of InfluxDB line protocol."""
    line_ending = "\n" if line.endswith("\n") else ""
    content = line.removesuffix(line_ending)
    if _is_metadata_line(content):
        return line

    record_parts = _split_record_content(content)
    if record_parts is None:
        return line

    series_key, field_set, remainder = record_parts
    line_measurement = _extract_measurement_from_series_key(series_key)
    if measurement is not None and line_measurement != measurement:
        return line

    kept_parts: list[str] = []
    for (
        field_start,
        field_end,
        separator_index,
    ) in _iter_field_ranges(field_set):
        field = field_set[field_start:field_end]
        if separator_index == -1:
            if field:
                kept_parts.append(field)
            continue

        field_key = _unescape_if_needed(field_set[field_start:separator_index])
        if field_key != field_key_to_drop:
            kept_parts.append(field)

    if not kept_parts:
        return ""

    return f"{series_key} {','.join(kept_parts)}{remainder}{line_ending}"


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
    if _is_metadata_line(content):
        return line

    record_parts = _split_record_content(content)
    if record_parts is None:
        return line

    series_key, field_set, remainder = record_parts
    line_measurement = _extract_measurement_from_series_key(series_key)
    if measurement is not None and line_measurement != measurement:
        return line

    escaped_new_field_key = _escape_tag_key(new_field_key)
    renamed_parts: list[str] = []
    for (
        field_start,
        field_end,
        separator_index,
    ) in _iter_field_ranges(field_set):
        field = field_set[field_start:field_end]
        if separator_index == -1:
            if field:
                renamed_parts.append(field)
            continue

        field_key = _unescape_if_needed(field_set[field_start:separator_index])
        if field_key == field_key_to_rename:
            field_value = field_set[separator_index + 1 : field_end]
            renamed_parts.append(f"{escaped_new_field_key}={field_value}")
        else:
            renamed_parts.append(field)

    return f"{series_key} {','.join(renamed_parts)}{remainder}{line_ending}"


def extract_measurement_field_keys(
    file_path: str | Path,
) -> dict[str, list[str]]:
    """Read an InfluxDB line protocol file and return field keys."""
    measurement_fields: defaultdict[str, set[str]] = defaultdict(set)
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as file_handle:
        for raw_line in file_handle:
            parsed_line = _extract_measurement_and_field_keys(raw_line)
            if parsed_line is None:
                continue

            measurement, field_keys = parsed_line
            measurement_fields[measurement].update(field_keys)

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
    return _rewrite_file_in_place(
        file_path,
        lambda line: _drop_field_from_line(
            line,
            field_key_to_drop,
            measurement=measurement,
        ),
    )


def rename_measurement_field_key(
    file_path: str | Path,
    field_key_to_rename: str,
    new_field_key: str,
    *,
    measurement: str | None = None,
) -> int:
    """Rename a field key in an InfluxDB line protocol file in place."""
    return _rewrite_file_in_place(
        file_path,
        lambda line: _rename_field_in_line(
            line,
            field_key_to_rename,
            new_field_key,
            measurement=measurement,
        ),
    )


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
