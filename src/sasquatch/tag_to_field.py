"""Commands for converting line protocol tags into fields."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import click

from .fields import _find_unquoted_separator
from .tags import _find_unescaped_separator, _unescape_if_needed


class TagToFieldConflictError(Exception):
    """Raised when a tag-to-field conversion would overwrite a field."""


def _split_record_content(
    content: str,
) -> tuple[str, str, str] | None:
    """Split record content into series key, field set, and any remainder."""
    field_separator = _find_unescaped_separator(content, " ")
    if field_separator == -1:
        return None

    series_key = content[:field_separator]
    field_and_timestamp = content[field_separator + 1 :]
    field_end = _find_unquoted_separator(field_and_timestamp, " ")
    field_set = (
        field_and_timestamp
        if field_end == -1
        else field_and_timestamp[:field_end]
    )
    remainder = "" if field_end == -1 else field_and_timestamp[field_end:]
    return series_key, field_set, remainder


def _escape_string_field_value(value: str) -> str:
    """Escape a string value for line protocol field output."""
    escaped = value.replace("\\", "\\\\")
    escaped = escaped.replace('"', '\\"')
    return f'"{escaped}"'


def _append_converted_field(  # noqa: C901
    field_set: str,
    tag_key: str,
    converted_tag_value: str,
    line_measurement: str,
) -> str:
    """Append the converted tag as a string field, checking for conflicts."""
    escaped = False
    in_quotes = False
    field_start = 0
    separator_index = -1
    field_end = len(field_set)

    for index, char in enumerate(field_set):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_quotes = not in_quotes
            continue
        if char == "=" and separator_index == -1 and not in_quotes:
            separator_index = index
            continue
        if char == "," and not in_quotes:
            if separator_index != -1:
                field_key = _unescape_if_needed(
                    field_set[field_start:separator_index]
                )
                if field_key == tag_key:
                    raise TagToFieldConflictError(
                        f"Cannot convert tag {tag_key!r} to field for "
                        "measurement "
                        f"{line_measurement!r}: field already exists."
                    )
            field_start = index + 1
            separator_index = -1

    if separator_index != -1:
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


def _convert_series_key_tag(  # noqa: C901
    series_key: str,
    tag_key: str,
    *,
    measurement: str | None = None,
) -> tuple[str, str | None, str]:
    """Convert a tag out of the series key and return conversion details."""
    first_tag_separator = _find_unescaped_separator(series_key, ",")
    if first_tag_separator == -1:
        return series_key, None, _unescape_if_needed(series_key)

    measurement_part = series_key[:first_tag_separator]
    line_measurement = _unescape_if_needed(measurement_part)
    if measurement is not None and line_measurement != measurement:
        return series_key, None, line_measurement

    kept_parts = [measurement_part]
    converted_tag_value: str | None = None
    tag_start = first_tag_separator + 1
    series_length = len(series_key)

    while tag_start < series_length:
        index = tag_start
        escaped = False
        separator_index = -1

        while index < series_length:
            char = series_key[index]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "=" and separator_index == -1:
                separator_index = index
            elif char == ",":
                break
            index += 1

        tag_end = index
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

        tag_start = tag_end + 1

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
    stripped_line = content.strip()
    if not stripped_line or stripped_line.startswith("#"):
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
    path = Path(file_path)
    modified_line_count = 0
    temp_path: Path | None = None

    try:
        with path.open("r", encoding="utf-8") as input_handle:
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=path.parent,
                delete=False,
            ) as temp_handle:
                temp_path = Path(temp_handle.name)
                for line in input_handle:
                    updated_line = _convert_tag_to_field_in_line(
                        line,
                        tag_key,
                        measurement=measurement,
                    )
                    if updated_line != line:
                        modified_line_count += 1
                    temp_handle.write(updated_line)
        if temp_path is not None:
            temp_path.replace(path)
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise

    return modified_line_count


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
