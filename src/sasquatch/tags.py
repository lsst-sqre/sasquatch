"""Commands for working with InfluxDB line protocol tags."""

from collections import defaultdict
from pathlib import Path

import click

from .line_protocol import (
    _escape_tag_key,
    _extract_measurement_and_tag_keys,
    _find_unescaped_separator,
    _iter_tag_ranges,
    _rewrite_file_in_place,
    _unescape_if_needed,
)


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
    first_tag_separator = _find_unescaped_separator(series_key, ",")
    if first_tag_separator == -1:
        return line

    measurement_part = series_key[:first_tag_separator]
    line_measurement = _unescape_if_needed(measurement_part)
    if measurement is not None and line_measurement != measurement:
        return line

    renamed_parts = [measurement_part]
    escaped_new_tag_key = _escape_tag_key(new_tag_key)
    for tag_start, tag_end, separator_index in _iter_tag_ranges(
        series_key, first_tag_separator + 1
    ):
        tag = series_key[tag_start:tag_end]

        if separator_index == -1:
            renamed_parts.append("," + tag)
        else:
            tag_key = _unescape_if_needed(
                series_key[tag_start:separator_index]
            )
            if tag_key == tag_key_to_rename:
                tag_value = series_key[separator_index + 1 : tag_end]
                renamed_parts.append(f",{escaped_new_tag_key}={tag_value}")
            else:
                renamed_parts.append("," + tag)

    return "".join(renamed_parts) + remainder


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
    first_tag_separator = _find_unescaped_separator(series_key, ",")
    if first_tag_separator == -1:
        return line

    measurement_part = series_key[:first_tag_separator]
    line_measurement = _unescape_if_needed(measurement_part)
    if measurement is not None and line_measurement != measurement:
        return line

    kept_parts = [measurement_part]
    for tag_start, tag_end, separator_index in _iter_tag_ranges(
        series_key, first_tag_separator + 1
    ):
        tag = series_key[tag_start:tag_end]

        if separator_index == -1:
            kept_parts.append("," + tag)
        else:
            tag_key = _unescape_if_needed(
                series_key[tag_start:separator_index]
            )
            if tag_key != tag_key_to_drop:
                kept_parts.append("," + tag)

    return "".join(kept_parts) + remainder


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
    return _rewrite_file_in_place(
        file_path,
        lambda line: _drop_tag_from_line(
            line,
            tag_key_to_drop,
            measurement=measurement,
        ),
    )


def rename_measurement_tag_key(
    file_path: str | Path,
    tag_key_to_rename: str,
    new_tag_key: str,
    *,
    measurement: str | None = None,
) -> int:
    """Rename a tag key in an InfluxDB line protocol file in place."""
    return _rewrite_file_in_place(
        file_path,
        lambda line: _rename_tag_in_line(
            line,
            tag_key_to_rename,
            new_tag_key,
            measurement=measurement,
        ),
    )


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
