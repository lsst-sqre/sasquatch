"""Commands for working with InfluxDB line protocol measurements."""

import fileinput
from pathlib import Path

import click

from .tags import _find_unescaped_separator, _split_unescaped, _unescape


def _drop_measurement_from_line(line: str, measurement_to_drop: str) -> str:
    """Drop a measurement from a single line of InfluxDB line protocol."""
    line_ending = "\n" if line.endswith("\n") else ""
    content = line.removesuffix(line_ending)
    stripped_line = content.strip()
    if not stripped_line or stripped_line.startswith("#"):
        return line

    field_separator = _find_unescaped_separator(content, " ")
    if field_separator == -1:
        return line

    series_key = content[:field_separator]
    parts = _split_unescaped(series_key, ",")
    if not parts:
        return line

    line_measurement = _unescape(parts[0])
    if line_measurement == measurement_to_drop:
        return ""

    return line


def drop_measurement(file_path: str | Path, measurement_name: str) -> int:
    """Remove a measurement from an InfluxDB line protocol file in place."""
    modified_line_count = 0
    with fileinput.input(
        files=(str(file_path),),
        inplace=True,
        encoding="utf-8",
    ) as lines:
        for line in lines:
            updated_line = _drop_measurement_from_line(line, measurement_name)
            if updated_line != line:
                modified_line_count += 1
            click.echo(updated_line, nl=False)
    return modified_line_count


@click.command("drop-measurement")
@click.argument(
    "filename", type=click.Path(exists=True, dir_okay=False, path_type=str)
)
@click.argument("measurement_name", nargs=1)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show how many lines were modified.",
)
def drop_measurement_command(
    filename: str,
    measurement_name: str,
    *,
    verbose: bool,
) -> None:
    """Drop a measurement from a line protocol file."""
    modified_line_count = drop_measurement(filename, measurement_name)
    if verbose:
        click.echo(f"Modified {modified_line_count} lines.")
