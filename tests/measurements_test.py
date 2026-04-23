"""Tests for line protocol measurement commands."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from sasquatch.cli import main


def test_drop_measurement_rewrites_line_protocol_file(tmp_path: Path) -> None:
    """The CLI should remove only matching measurement records."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        "# comment\n"
        "weather,region=us temp=82\n"
        "cpu value=1i\n"
        "weather,region=eu humidity=41\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["influxdb", "drop-measurement", str(data_file), "weather"],
    )

    assert result.exit_code == 0
    assert result.output == ""
    assert data_file.read_text(encoding="utf-8") == (
        "# comment\ncpu value=1i\n"
    )


def test_drop_measurement_matches_unescaped_measurement_name(
    tmp_path: Path,
) -> None:
    """Escaped measurement names should be matched by their unescaped form."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        "weather\\ station,region=us temp=82\ncpu value=1i\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["influxdb", "drop-measurement", str(data_file), "weather station"],
    )

    assert result.exit_code == 0
    assert data_file.read_text(encoding="utf-8") == "cpu value=1i\n"


def test_drop_measurement_verbose_reports_modified_line_count(
    tmp_path: Path,
) -> None:
    """Verbose mode should report how many lines changed."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        "weather,region=us temp=82\n"
        "cpu value=1i\n"
        "weather,region=eu humidity=41\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["influxdb", "drop-measurement", "-v", str(data_file), "weather"],
    )

    assert result.exit_code == 0
    assert result.output == "Modified 2 lines.\n"
    assert data_file.read_text(encoding="utf-8") == "cpu value=1i\n"
