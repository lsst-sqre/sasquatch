"""Tests for line protocol measurement commands."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner
from safir.testing.data import Data

from sasquatch.cli import main

EXPORT_HEADER = (
    "# INFLUXDB EXPORT: 1677-09-21T00:12:43Z - 2262-04-11T23:47:16Z\n"
    "# DDL\n"
    'CREATE DATABASE "target.metrics"\n'
    "# DML\n"
    "# CONTEXT-DATABASE:target.metrics\n"
    "# CONTEXT-RETENTION-POLICY:forever\n"
    "# writing tsm data\n"
)


def _with_header(content: str) -> str:
    """Prefix synthetic line protocol with a realistic export header."""
    return EXPORT_HEADER + content


def test_show_measurements_lists_tag_keys_and_field_keys(
    tmp_path: Path,
    data: Data,
) -> None:
    """The CLI should print measurements with tag and field keys."""
    data_file = tmp_path / "data.lp"
    _ = data_file.write_text(data.read_text("input/single-weather.lp"))

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["influxdb", "line-protocol", "show-measurements", str(data_file)],
    )

    assert result.exit_code == 0
    data.assert_text_matches(result.output, "measurements.txt")


def test_show_measurements_handles_escaped_names_and_quoted_field_values(
    tmp_path: Path, data: Data
) -> None:
    """Escaped tag names and quoted field values should parse cleanly."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(data.read_text("input/weather-station.lp"))

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["influxdb", "line-protocol", "show-measurements", str(data_file)],
    )

    assert result.exit_code == 0
    data.assert_text_matches(result.output, "weather-station-measurements.txt")


def test_drop_measurement_rewrites_line_protocol_file(
    tmp_path: Path, data: Data
) -> None:
    """The CLI should remove only matching measurement records."""
    data_file = tmp_path / "data.lp"
    _ = data_file.write_text(
        data.read_text("input/weather-and-cpu-with-comment.lp")
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "drop-measurement",
            str(data_file),
            "weather",
        ],
    )

    assert result.exit_code == 0
    assert result.output == ""
    expected = data_file.read_text()
    data.assert_text_matches(expected, "only-cpu-with-comment.lp")


def test_keep_measurements_rewrites_line_protocol_file(
    tmp_path: Path, data: Data
) -> None:
    """The CLI should keep only matching measurement records."""
    data_file = tmp_path / "data.lp"
    _ = data_file.write_text(data.read_text("input/weather.lp"))

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "keep-measurements",
            str(data_file),
            "weather",
        ],
    )

    assert result.exit_code == 0
    assert result.output == ""
    expected = data_file.read_text()
    data.assert_text_matches(expected, "only-weather.lp")


def test_keep_measurements_keeps_multiple(tmp_path: Path, data: Data) -> None:
    """The CLI should keep only matching measurement records."""
    data_file = tmp_path / "data.lp"
    _ = data_file.write_text(data.read_text("input/weather.lp"))

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "keep-measurements",
            str(data_file),
            "weather",
            "weather2",
        ],
    )

    assert result.exit_code == 0
    assert result.output == ""
    expected = data_file.read_text()
    data.assert_text_matches(expected, "some-weather.lp")


def test_keep_measurements_verbose_reports_modified_line_count(
    tmp_path: Path, data: Data
) -> None:
    """Verbose mode should report how many lines changed."""
    data_file = tmp_path / "data.lp"
    _ = data_file.write_text(data.read_text("input/weather.lp"))

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "keep-measurements",
            str(data_file),
            "weather",
            "-v",
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Modified 3 lines.\n"
    expected = data_file.read_text()
    data.assert_text_matches(expected, "only-weather.lp")


def test_drop_measurement_matches_unescaped_measurement_name(
    tmp_path: Path, data: Data
) -> None:
    """Escaped measurement names should be matched by their unescaped form."""
    data_file = tmp_path / "data.lp"
    _ = data_file.write_text(
        data.read_text("input/weather-station-and-cpu.lp")
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "drop-measurement",
            str(data_file),
            "weather station",
        ],
    )

    assert result.exit_code == 0
    expected = data_file.read_text()
    data.assert_text_matches(expected, "only-cpu.lp")


def test_drop_measurement_verbose_reports_modified_line_count(
    tmp_path: Path, data: Data
) -> None:
    """Verbose mode should report how many lines changed."""
    data_file = tmp_path / "data.lp"
    _ = data_file.write_text(data.read_text("input/weather-and-cpu.lp"))

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "drop-measurement",
            "-v",
            str(data_file),
            "weather",
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Modified 2 lines.\n"
    expected = data_file.read_text()
    data.assert_text_matches(expected, "only-cpu.lp")


def test_rename_measurement_rewrites_line_protocol_file(
    tmp_path: Path, data: Data
) -> None:
    """The CLI should rename only matching measurement records."""
    data_file = tmp_path / "data.lp"
    _ = data_file.write_text(
        data.read_text("input/weather-and-cpu-with-comment.lp")
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "rename-measurement",
            str(data_file),
            "weather",
            "forecast",
        ],
    )

    assert result.exit_code == 0
    assert result.output == ""
    expected = data_file.read_text()
    data.assert_text_matches(expected, "forecast-and-cpu.lp")


def test_rename_measurement_matches_unescaped_measurement_name(
    tmp_path: Path, data: Data
) -> None:
    """Escaped measurement names should be matched by their unescaped form."""
    data_file = tmp_path / "data.lp"
    _ = data_file.write_text(
        data.read_text("input/weather-station-and-cpu.lp")
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "rename-measurement",
            str(data_file),
            "weather station",
            "station forecast",
        ],
    )

    assert result.exit_code == 0
    expected = data_file.read_text()
    data.assert_text_matches(expected, "station-forecast.lp")


def test_rename_measurement_verbose_reports_modified_line_count(
    tmp_path: Path, data: Data
) -> None:
    """Verbose mode should report how many lines changed."""
    data_file = tmp_path / "data.lp"
    _ = data_file.write_text(data.read_text("input/weather-and-cpu.lp"))

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "rename-measurement",
            "-v",
            str(data_file),
            "weather",
            "forecast",
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Modified 2 lines.\n"
    expected = data_file.read_text()
    data.assert_text_matches(expected, "forecast-weather-and-cpu.lp")
