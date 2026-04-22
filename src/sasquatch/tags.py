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


def _split_tag(tag: str) -> tuple[str, str] | None:
    """Split a tag assignment into key and value."""
    separator_index = _find_unescaped_separator(tag, "=")
    if separator_index == -1:
        return None

    tag_key = _unescape(tag[:separator_index])
    tag_value = _unescape(tag[separator_index + 1 :])
    return tag_key, tag_value


def _drop_tag_from_line(line: str, tag_key_to_drop: str) -> str:
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
    measurement_tags = defaultdict(set)
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            field_separator = _find_unescaped_separator(line, " ")
            if field_separator == -1:
                continue

            parts = _split_unescaped(line[:field_separator], ",")
            if not parts:
                continue

            measurement = _unescape(parts[0])
            measurement_tags[measurement]

            for tag in parts[1:]:
                tag_parts = _split_tag(tag)
                if tag_parts is not None:
                    tag_key, _tag_value = tag_parts
                    measurement_tags[measurement].add(tag_key)

    # Convert sets to sorted lists
    return {m: sorted(tags) for m, tags in measurement_tags.items()}


def drop_measurement_tag_key(
    file_path: str | Path,
    tag_key_to_drop: str,
) -> int:
    """Remove a tag key from an InfluxDB line protocol file in place."""
    modified_line_count = 0
    with fileinput.input(
        files=(str(file_path),),
        inplace=True,
        encoding="utf-8",
    ) as lines:
        for line in lines:
            updated_line = _drop_tag_from_line(line, tag_key_to_drop)
            if updated_line != line:
                modified_line_count += 1
            click.echo(
                updated_line,
                nl=False,
            )
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
def drop_tag(filename: str, tag_key: str, *, verbose: bool) -> None:
    """Drop a tag key from a line protocol file."""
    modified_line_count = drop_measurement_tag_key(filename, tag_key)
    if verbose:
        click.echo(f"Modified {modified_line_count} lines.")
