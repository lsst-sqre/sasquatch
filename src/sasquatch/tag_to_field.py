"""Commands for converting line protocol tags into fields."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import click

from .fields import _find_unquoted_separator, _split_field, _split_fields
from .tags import (
    _find_unescaped_separator,
    _split_tag,
    _split_unescaped,
    _unescape,
)


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


def _convert_series_key_tag(
    series_key: str,
    tag_key: str,
    *,
    measurement: str | None = None,
) -> tuple[str, list[str], str | None, str]:
    """Convert a tag out of the series key and return conversion details."""
    parts = _split_unescaped(series_key, ",")
    if not parts:
        return series_key, [], None, ""

    line_measurement = _unescape(parts[0])
    if measurement is not None and line_measurement != measurement:
        return series_key, [], None, line_measurement

    converted_tag_value: str | None = None
    kept_tags = [parts[0]]
    for tag in parts[1:]:
        tag_parts = _split_tag(tag)
        if tag_parts is None:
            kept_tags.append(tag)
            continue

        current_tag_key, current_tag_value = tag_parts
        if current_tag_key == tag_key:
            converted_tag_value = current_tag_value
            continue
        kept_tags.append(tag)

    return (
        ",".join(kept_tags),
        kept_tags,
        converted_tag_value,
        line_measurement,
    )


def _append_converted_field(
    field_set: str,
    tag_key: str,
    converted_tag_value: str,
    line_measurement: str,
) -> str:
    """Append the converted tag as a string field, checking for conflicts."""
    fields = _split_fields(field_set)
    for field in fields:
        field_parts = _split_field(field)
        if field_parts is None:
            continue
        field_key, _field_value = field_parts
        if field_key == tag_key:
            raise TagToFieldConflictError(
                f"Cannot convert tag {tag_key!r} to field for "
                f"measurement {line_measurement!r}: field already exists."
            )

    updated_fields = [
        *fields,
        f"{tag_key}={_escape_string_field_value(converted_tag_value)}",
    ]
    return ",".join(updated_fields)


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
    updated_series_key, kept_tags, converted_tag_value, line_measurement = (
        _convert_series_key_tag(
            series_key,
            tag_key,
            measurement=measurement,
        )
    )
    if not kept_tags or converted_tag_value is None:
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
