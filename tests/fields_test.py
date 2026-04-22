"""Tests for line protocol field parsing."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from sasquatch.cli import main


def test_show_fields_groups_field_keys_by_measurement(tmp_path: Path) -> None:
    """The CLI should print field keys grouped by measurement."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        "weather,region=us temp=82,humidity=41i\ncpu value=1i\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["influxdb", "show-fields", str(data_file)],
    )

    assert result.exit_code == 0
    assert result.output == "cpu: value\nweather: humidity, temp\n"


def test_show_fields_handles_quoted_string_values_with_commas_and_spaces(
    tmp_path: Path,
) -> None:
    """Quoted string field values should not break field parsing."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        'weather,region=us temp=82,summary="hot, dry day",note="clear sky"\n',
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["influxdb", "show-fields", str(data_file)],
    )

    assert result.exit_code == 0
    assert result.output == "weather: note, summary, temp\n"
