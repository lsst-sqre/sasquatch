"""Commands for working with InfluxDB line protocol fields."""

from collections import defaultdict
from pathlib import Path
from tempfile import NamedTemporaryFile

import click

from .tags import (
    _escape_tag_key,
    _find_unescaped_separator,
    _unescape,
    _unescape_if_needed,
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


def _extract_measurement_from_series_key(series_key: str) -> str:
    """Extract the measurement name from a series key."""
    first_tag_separator = _find_unescaped_separator(series_key, ",")
    measurement_part = (
        series_key
        if first_tag_separator == -1
        else series_key[:first_tag_separator]
    )
    return _unescape_if_needed(measurement_part)


def _split_record_content(
    content: str,
) -> tuple[str, str, str] | None:
    """Split record content into series key, field set, and any remainder."""
    series_separator = _find_unescaped_separator(content, " ")
    if series_separator == -1:
        return None

    series_key = content[:series_separator]
    field_and_timestamp = content[series_separator + 1 :]
    field_end = _find_unquoted_separator(field_and_timestamp, " ")
    field_set = (
        field_and_timestamp
        if field_end == -1
        else field_and_timestamp[:field_end]
    )
    remainder = "" if field_end == -1 else field_and_timestamp[field_end:]
    return series_key, field_set, remainder


def _extract_measurement_and_field_keys(  # noqa: C901
    line: str,
) -> tuple[str, set[str]] | None:
    """Extract a measurement name and field keys with one pass over fields."""
    content = line.rstrip("\n")
    stripped_line = content.lstrip()
    if not stripped_line or stripped_line.startswith("#"):
        return None

    record_parts = _split_record_content(content)
    if record_parts is None:
        return None

    series_key, field_set, _remainder = record_parts
    measurement = _extract_measurement_from_series_key(series_key)

    field_keys: set[str] = set()
    escaped = False
    in_quotes = False
    field_start = 0
    separator_index = -1

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
                field_keys.add(
                    _unescape_if_needed(field_set[field_start:separator_index])
                )
            field_start = index + 1
            separator_index = -1

    if separator_index != -1:
        field_keys.add(
            _unescape_if_needed(field_set[field_start:separator_index])
        )

    return measurement, field_keys


def _drop_field_from_line(  # noqa: C901, PLR0912
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

    record_parts = _split_record_content(content)
    if record_parts is None:
        return line

    series_key, field_set, remainder = record_parts
    line_measurement = _extract_measurement_from_series_key(series_key)
    if measurement is not None and line_measurement != measurement:
        return line

    kept_parts: list[str] = []
    escaped = False
    in_quotes = False
    field_start = 0
    separator_index = -1

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
            field = field_set[field_start:index]
            if separator_index == -1:
                kept_parts.append(field)
            else:
                field_key = _unescape_if_needed(
                    field_set[field_start:separator_index]
                )
                if field_key != field_key_to_drop:
                    kept_parts.append(field)
            field_start = index + 1
            separator_index = -1

    final_field = field_set[field_start:]
    if separator_index == -1:
        if final_field:
            kept_parts.append(final_field)
    else:
        field_key = _unescape_if_needed(field_set[field_start:separator_index])
        if field_key != field_key_to_drop:
            kept_parts.append(final_field)

    if not kept_parts:
        return ""

    return f"{series_key} {','.join(kept_parts)}{remainder}{line_ending}"


def _rename_field_in_line(  # noqa: C901, PLR0912, PLR0915
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

    record_parts = _split_record_content(content)
    if record_parts is None:
        return line

    series_key, field_set, remainder = record_parts
    line_measurement = _extract_measurement_from_series_key(series_key)
    if measurement is not None and line_measurement != measurement:
        return line

    escaped_new_field_key = _escape_tag_key(new_field_key)
    renamed_parts: list[str] = []
    escaped = False
    in_quotes = False
    field_start = 0
    separator_index = -1

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
            field = field_set[field_start:index]
            if separator_index == -1:
                renamed_parts.append(field)
            else:
                field_key = _unescape_if_needed(
                    field_set[field_start:separator_index]
                )
                if field_key == field_key_to_rename:
                    field_value = field_set[separator_index + 1 : index]
                    renamed_parts.append(
                        f"{escaped_new_field_key}={field_value}"
                    )
                else:
                    renamed_parts.append(field)
            field_start = index + 1
            separator_index = -1

    final_field = field_set[field_start:]
    if separator_index == -1:
        if final_field:
            renamed_parts.append(final_field)
    else:
        field_key = _unescape_if_needed(field_set[field_start:separator_index])
        if field_key == field_key_to_rename:
            renamed_parts.append(
                f"{escaped_new_field_key}={field_set[separator_index + 1 :]}"
            )
        else:
            renamed_parts.append(final_field)

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
                    updated_line = _drop_field_from_line(
                        line,
                        field_key_to_drop,
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


def rename_measurement_field_key(
    file_path: str | Path,
    field_key_to_rename: str,
    new_field_key: str,
    *,
    measurement: str | None = None,
) -> int:
    """Rename a field key in an InfluxDB line protocol file in place."""
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
                    updated_line = _rename_field_in_line(
                        line,
                        field_key_to_rename,
                        new_field_key,
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
