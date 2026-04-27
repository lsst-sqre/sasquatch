"""Commands for working with InfluxDB line protocol tags."""

import fileinput
from collections import defaultdict
from pathlib import Path

import click


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


def _split_unescaped(text: str, separator: str) -> list[str]:
    """Split a string on unescaped separator characters."""
    parts: list[str] = []
    current: list[str] = []
    escaped = False

    for char in text:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            current.append(char)
            continue
        if char == separator:
            parts.append("".join(current))
            current = []
            continue
        current.append(char)

    if escaped:
        current.append("\\")

    parts.append("".join(current))
    return parts


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


def _escape_tag_key(value: str) -> str:
    """Escape a tag key for line protocol output."""
    escaped = value.replace("\\", "\\\\")
    escaped = escaped.replace(",", "\\,")
    escaped = escaped.replace(" ", "\\ ")
    return escaped.replace("=", "\\=")


def _split_tag(tag: str) -> tuple[str, str] | None:
    """Split a tag assignment into key and value."""
    separator_index = _find_unescaped_separator(tag, "=")
    if separator_index == -1:
        return None

    tag_key = _unescape(tag[:separator_index])
    tag_value = _unescape(tag[separator_index + 1 :])
    return tag_key, tag_value


def _unescape_if_needed(value: str) -> str:
    """Unescape a value only when it contains escapes."""
    return _unescape(value) if "\\" in value else value


def _extract_measurement_and_tag_keys(  # noqa: C901, PLR0912, PLR0915
    line: str,
) -> tuple[str, set[str]] | None:
    """Extract a measurement name and tag keys with one pass over the line."""
    stripped_line = line.lstrip()
    if not stripped_line or stripped_line.startswith("#"):
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


def _rename_tag_in_line(
    line: str,
    tag_key_to_rename: str,
    new_tag_key: str,
    *,
    measurement: str | None = None,
) -> str:
    """Rename a tag key in a single line of InfluxDB line protocol."""
    stripped_line = line.strip()
    if not stripped_line or stripped_line.startswith("#"):
        return line

    field_separator = _find_unescaped_separator(line, " ")
    if field_separator == -1:
        return line

    series_key = line[:field_separator]
    remainder = line[field_separator:]
    parts = _split_unescaped(series_key, ",")
    if not parts:
        return line

    line_measurement = _unescape(parts[0])
    if measurement is not None and line_measurement != measurement:
        return line

    renamed_parts = [parts[0]]
    escaped_new_tag_key = _escape_tag_key(new_tag_key)
    for tag in parts[1:]:
        separator_index = _find_unescaped_separator(tag, "=")
        if separator_index == -1:
            renamed_parts.append(tag)
            continue

        tag_key = _unescape(tag[:separator_index])
        if tag_key == tag_key_to_rename:
            renamed_parts.append(
                f"{escaped_new_tag_key}={tag[separator_index + 1 :]}"
            )
        else:
            renamed_parts.append(tag)

    return ",".join(renamed_parts) + remainder


def _drop_tag_from_line(
    line: str,
    tag_key_to_drop: str,
    *,
    measurement: str | None = None,
) -> str:
    """Drop a tag key from a single line of InfluxDB line protocol."""
    stripped_line = line.strip()
    if not stripped_line or stripped_line.startswith("#"):
        return line

    field_separator = _find_unescaped_separator(line, " ")
    if field_separator == -1:
        return line

    series_key = line[:field_separator]
    remainder = line[field_separator:]
    parts = _split_unescaped(series_key, ",")
    if not parts:
        return line

    line_measurement = _unescape(parts[0])
    if measurement is not None and line_measurement != measurement:
        return line

    kept_parts = [parts[0]]
    for tag in parts[1:]:
        tag_parts = _split_tag(tag)
        if tag_parts is None:
            kept_parts.append(tag)
            continue
        tag_key, _tag_value = tag_parts
        if tag_key != tag_key_to_drop:
            kept_parts.append(tag)

    return ",".join(kept_parts) + remainder


def extract_measurement_tag_keys(
    file_path: str | Path,
) -> dict[str, list[str]]:
    """Read an InfluxDB line protocol file and return a dictionary."""
    measurement_tags: defaultdict[str, set[str]] = defaultdict(set)
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            parsed_line = _extract_measurement_and_tag_keys(raw_line)
            if parsed_line is None:
                continue

            measurement, tag_keys = parsed_line
            measurement_tags[measurement].update(tag_keys)

    # Convert sets to sorted lists
    return {m: sorted(tags) for m, tags in measurement_tags.items()}


def drop_measurement_tag_key(
    file_path: str | Path,
    tag_key_to_drop: str,
    *,
    measurement: str | None = None,
) -> int:
    """Remove a tag key from an InfluxDB line protocol file in place."""
    modified_line_count = 0
    with fileinput.input(
        files=(str(file_path),),
        inplace=True,
        encoding="utf-8",
    ) as lines:
        for line in lines:
            updated_line = _drop_tag_from_line(
                line,
                tag_key_to_drop,
                measurement=measurement,
            )
            if updated_line != line:
                modified_line_count += 1
            click.echo(
                updated_line,
                nl=False,
            )
    return modified_line_count


def rename_measurement_tag_key(
    file_path: str | Path,
    tag_key_to_rename: str,
    new_tag_key: str,
    *,
    measurement: str | None = None,
) -> int:
    """Rename a tag key in an InfluxDB line protocol file in place."""
    modified_line_count = 0
    with fileinput.input(
        files=(str(file_path),),
        inplace=True,
        encoding="utf-8",
    ) as lines:
        for line in lines:
            updated_line = _rename_tag_in_line(
                line,
                tag_key_to_rename,
                new_tag_key,
                measurement=measurement,
            )
            if updated_line != line:
                modified_line_count += 1
            click.echo(updated_line, nl=False)
    return modified_line_count


@click.command("show-tags")
@click.argument(
    "filename", type=click.Path(exists=True, dir_okay=False, path_type=str)
)
def show_tags(filename: str) -> None:
    """List measurements and unique tag keys from a line protocol file."""
    result = extract_measurement_tag_keys(filename)

    if not result:
        click.echo("No measurements found.")
        return

    for measurement in sorted(result):
        tags = (
            ", ".join(result[measurement])
            if result[measurement]
            else "(no tags)"
        )
        click.echo(f"{measurement}: {tags}")


@click.command("drop-tag")
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
    help="Only drop the tag from this measurement.",
)
def drop_tag(
    filename: str,
    tag_key: str,
    *,
    verbose: bool,
    measurement: str | None,
) -> None:
    """Drop a tag key from a line protocol file."""
    modified_line_count = drop_measurement_tag_key(
        filename,
        tag_key,
        measurement=measurement,
    )
    if verbose:
        click.echo(f"Modified {modified_line_count} lines.")


@click.command("rename-tag")
@click.argument(
    "filename", type=click.Path(exists=True, dir_okay=False, path_type=str)
)
@click.argument("tag_key", nargs=1)
@click.argument("new_tag_key", nargs=1)
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
    help="Only rename the tag on this measurement.",
)
def rename_tag(
    filename: str,
    tag_key: str,
    new_tag_key: str,
    *,
    verbose: bool,
    measurement: str | None,
) -> None:
    """Rename a tag key in a line protocol file."""
    modified_line_count = rename_measurement_tag_key(
        filename,
        tag_key,
        new_tag_key,
        measurement=measurement,
    )
    if verbose:
        click.echo(f"Modified {modified_line_count} lines.")
