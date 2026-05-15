"""Tests for line protocol measurement commands."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

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
) -> None:
    """The CLI should print measurements with tag and field keys."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "weather,region=us,zone=north temp=82,humidity=41i\ncpu value=1i\n"
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["influxdb", "line-protocol", "show-measurements", str(data_file)],
    )

    assert result.exit_code == 0
    assert result.output == (
        "cpu: tags=(no tags); fields=value\n"
        "weather: tags=region, zone; fields=humidity, temp\n"
    )


def test_show_measurements_handles_escaped_names_and_quoted_field_values(
    tmp_path: Path,
) -> None:
    """Escaped tag names and quoted field values should parse cleanly."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "weather\\ station,tag\\,key=value "
            'summary="hot, dry day",temp=82\n'
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["influxdb", "line-protocol", "show-measurements", str(data_file)],
    )

    assert result.exit_code == 0
    assert result.output == (
        "weather station: tags=tag,key; fields=summary, temp\n"
    )


def test_drop_measurement_rewrites_line_protocol_file(tmp_path: Path) -> None:
    """The CLI should remove only matching measurement records."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "# comment\n"
            "weather,region=us temp=82\n"
            "cpu value=1i\n"
            "weather,region=eu humidity=41\n"
        ),
        encoding="utf-8",
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
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "# comment\ncpu value=1i\n"
    )


def test_drop_measurement_matches_unescaped_measurement_name(
    tmp_path: Path,
) -> None:
    """Escaped measurement names should be matched by their unescaped form."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header("weather\\ station,region=us temp=82\ncpu value=1i\n"),
        encoding="utf-8",
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
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "cpu value=1i\n"
    )


def test_drop_measurement_verbose_reports_modified_line_count(
    tmp_path: Path,
) -> None:
    """Verbose mode should report how many lines changed."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "weather,region=us temp=82\n"
            "cpu value=1i\n"
            "weather,region=eu humidity=41\n"
        ),
        encoding="utf-8",
    )

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
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "cpu value=1i\n"
    )


def test_rename_measurement_rewrites_line_protocol_file(
    tmp_path: Path,
) -> None:
    """The CLI should rename only matching measurement records."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "# comment\n"
            "weather,region=us temp=82\n"
            "cpu value=1i\n"
            "weather,region=eu humidity=41\n"
        ),
        encoding="utf-8",
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
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "# comment\n"
        "forecast,region=us temp=82\n"
        "cpu value=1i\n"
        "forecast,region=eu humidity=41\n"
    )


def test_rename_measurement_matches_unescaped_measurement_name(
    tmp_path: Path,
) -> None:
    """Escaped measurement names should be matched by their unescaped form."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header("weather\\ station,region=us temp=82\ncpu value=1i\n"),
        encoding="utf-8",
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
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "station\\ forecast,region=us temp=82\ncpu value=1i\n"
    )


def test_rename_measurement_verbose_reports_modified_line_count(
    tmp_path: Path,
) -> None:
    """Verbose mode should report how many lines changed."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "weather,region=us temp=82\n"
            "cpu value=1i\n"
            "weather,region=eu humidity=41\n"
        ),
        encoding="utf-8",
    )

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
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "forecast,region=us temp=82\n"
        "cpu value=1i\n"
        "forecast,region=eu humidity=41\n"
    )
