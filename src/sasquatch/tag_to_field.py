"""Commands for converting line protocol tags into fields."""

from __future__ import annotations

from pathlib import Path

import click

from .line_protocol import (
    _extract_measurement_from_series_key,
    _find_unescaped_separator,
    _is_metadata_line,
    _iter_field_ranges,
    _iter_tag_ranges,
    _rewrite_file_in_place,
    _split_record_content,
    _unescape_if_needed,
)


class TagToFieldConflictError(Exception):
    """Raised when a tag-to-field conversion would overwrite a field."""


def _escape_string_field_value(value: str) -> str:
    """Escape a string value for line protocol field output."""
    escaped = value.replace("\\", "\\\\")
    escaped = escaped.replace('"', '\\"')
    return f'"{escaped}"'


def _append_converted_field(
    field_set: str,
    tag_key: str,
    converted_tag_value: str,
    line_measurement: str,
) -> str:
    """Append the converted tag as a string field, checking for conflicts."""
    field_end = len(field_set)

    for (
        field_start,
        _field_end,
        separator_index,
    ) in _iter_field_ranges(field_set):
        if separator_index == -1:
            continue
        field_key = _unescape_if_needed(field_set[field_start:separator_index])
        if field_key == tag_key:
            raise TagToFieldConflictError(
                f"Cannot convert tag {tag_key!r} to field for "
                f"measurement {line_measurement!r}: field already exists."
            )

    return (
        f"{field_set[:field_end]},"
        f"{tag_key}={_escape_string_field_value(converted_tag_value)}"
    )


def _convert_series_key_tag(
    series_key: str,
    tag_key: str,
    *,
    measurement: str | None = None,
) -> tuple[str, str | None, str]:
    """Convert a tag out of the series key and return conversion details."""
    first_tag_separator = _find_unescaped_separator(series_key, ",")
    if first_tag_separator == -1:
        return (
            series_key,
            None,
            _extract_measurement_from_series_key(series_key),
        )

    measurement_part = series_key[:first_tag_separator]
    line_measurement = _extract_measurement_from_series_key(series_key)
    if measurement is not None and line_measurement != measurement:
        return series_key, None, line_measurement

    kept_parts = [measurement_part]
    converted_tag_value: str | None = None
    for tag_start, tag_end, separator_index in _iter_tag_ranges(
        series_key, first_tag_separator + 1
    ):
        tag = series_key[tag_start:tag_end]

        if separator_index == -1:
            kept_parts.append("," + tag)
        else:
            current_tag_key = _unescape_if_needed(
                series_key[tag_start:separator_index]
            )
            if current_tag_key == tag_key:
                converted_tag_value = _unescape_if_needed(
                    series_key[separator_index + 1 : tag_end]
                )
            else:
                kept_parts.append("," + tag)

    return "".join(kept_parts), converted_tag_value, line_measurement


def _convert_tag_to_field_in_line(
    line: str,
    tag_key: str,
    *,
    measurement: str | None = None,
) -> str:
    """Convert one tag key into a string field on a single line."""
    line_ending = "\n" if line.endswith("\n") else ""
    content = line.removesuffix(line_ending)
    if _is_metadata_line(content):
        return line

    record_parts = _split_record_content(content)
    if record_parts is None:
        return line

    series_key, field_set, remainder = record_parts
    updated_series_key, converted_tag_value, line_measurement = (
        _convert_series_key_tag(series_key, tag_key, measurement=measurement)
    )
    if converted_tag_value is None:
        return line

    updated_fields = _append_converted_field(
        field_set,
        tag_key,
        converted_tag_value,
        line_measurement,
    )
    return f"{updated_series_key} {updated_fields}{remainder}{line_ending}"


def convert_tag_to_field(
    file_path: str | Path,
    tag_key: str,
    *,
    measurement: str | None = None,
) -> int:
    """Convert a tag key into a string field in a line protocol file."""
    return _rewrite_file_in_place(
        file_path,
        lambda line: _convert_tag_to_field_in_line(
            line,
            tag_key,
            measurement=measurement,
        ),
    )


@click.command("convert-tag-to-field")
@click.argument(
    "filename", type=click.Path(exists=True, dir_okay=False, path_type=str)
)
@click.argument("tag_key", nargs=1)
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
    help="Only convert the tag on this measurement.",
)
def convert_tag_to_field_command(
    filename: str,
    tag_key: str,
    *,
    verbose: bool,
    measurement: str | None,
) -> None:
    """Convert a tag key and value into a string field."""
    try:
        modified_line_count = convert_tag_to_field(
            filename,
            tag_key,
            measurement=measurement,
        )
        if verbose:
            click.echo(f"Modified {modified_line_count} lines.")
    except TagToFieldConflictError as exc:
        raise click.ClickException(str(exc)) from exc
