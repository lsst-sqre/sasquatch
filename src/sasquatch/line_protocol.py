"""Shared helpers for parsing InfluxDB line protocol."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path
from tempfile import NamedTemporaryFile


def _find_unescaped_separator(text: str, separator: str) -> int:
    """Find the first separator character that is not escaped."""
    escaped = False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == separator:
            return index
    return -1


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


def _unescape(value: str) -> str:
    """Unescape line protocol identifier content."""
    result: list[str] = []
    escaped = False

    for char in value:
        if escaped:
            result.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        result.append(char)

    if escaped:
        result.append("\\")

    return "".join(result)


def _unescape_if_needed(value: str) -> str:
    """Unescape a value only when it contains escapes."""
    return _unescape(value) if "\\" in value else value


def _is_metadata_line(line: str) -> bool:
    """Return whether a line is header metadata, not line protocol data."""
    stripped = line.strip()
    return not stripped or stripped.startswith(("#", "CREATE "))


def _escape_tag_key(value: str) -> str:
    """Escape a tag key for line protocol output."""
    escaped = value.replace("\\", "\\\\")
    escaped = escaped.replace(",", "\\,")
    escaped = escaped.replace(" ", "\\ ")
    return escaped.replace("=", "\\=")


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


def _iter_tag_ranges(
    series_key: str,
    start_index: int,
) -> Iterator[tuple[int, int, int]]:
    """Yield tag slice boundaries and key/value separator positions."""
    series_length = len(series_key)
    tag_start = start_index

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

        yield tag_start, index, separator_index
        tag_start = index + 1


def _iter_field_ranges(field_set: str) -> Iterator[tuple[int, int, int]]:
    """Yield field slice boundaries and key/value separator positions."""
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
            yield field_start, index, separator_index
            field_start = index + 1
            separator_index = -1

    yield field_start, len(field_set), separator_index


def _extract_measurement_and_tag_keys(  # noqa: C901, PLR0912, PLR0915
    line: str,
) -> tuple[str, set[str]] | None:
    """Extract a measurement name and tag keys with one pass over the line."""
    if _is_metadata_line(line):
        return None

    measurement_chars: list[str] = []
    tag_keys: set[str] = set()
    tag_key_chars: list[str] = []
    escaped = False
    in_tag_key = False
    in_tag_value = False

    for char in line:
        if escaped:
            if in_tag_key:
                tag_key_chars.append(char)
            elif not in_tag_value:
                measurement_chars.append(char)
            escaped = False
            continue

        if char == "\\":
            escaped = True
            if in_tag_key:
                tag_key_chars.append(char)
            elif not in_tag_value:
                measurement_chars.append(char)
            continue

        if in_tag_value:
            if char == ",":
                in_tag_value = False
                in_tag_key = True
                tag_key_chars = []
                continue
            if char == " ":
                break
            continue

        if in_tag_key:
            if char == "=":
                tag_keys.add(_unescape_if_needed("".join(tag_key_chars)))
                in_tag_key = False
                in_tag_value = True
                continue
            if char == ",":
                tag_key_chars = []
                continue
            if char == " ":
                break
            tag_key_chars.append(char)
            continue

        if char == ",":
            in_tag_key = True
            continue
        if char == " ":
            break
        measurement_chars.append(char)

    if not measurement_chars:
        return None

    measurement = _unescape_if_needed("".join(measurement_chars))
    return measurement, tag_keys


def _extract_measurement_and_field_keys(
    line: str,
) -> tuple[str, set[str]] | None:
    """Extract a measurement name and field keys with one pass over fields."""
    content = line.rstrip("\n")
    if _is_metadata_line(content):
        return None

    record_parts = _split_record_content(content)
    if record_parts is None:
        return None

    series_key, field_set, _remainder = record_parts
    measurement = _extract_measurement_from_series_key(series_key)

    field_keys: set[str] = set()
    for (
        field_start,
        _field_end,
        separator_index,
    ) in _iter_field_ranges(field_set):
        if separator_index == -1:
            continue
        field_keys.add(
            _unescape_if_needed(field_set[field_start:separator_index])
        )

    return measurement, field_keys


def _rewrite_file_in_place(
    file_path: str | Path,
    transform_line: Callable[[str], str],
) -> int:
    """Rewrite a file in place by transforming each line."""
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
                    updated_line = transform_line(line)
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
