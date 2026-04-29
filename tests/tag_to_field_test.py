"""Tests for tag-to-field conversion commands."""

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


def test_convert_tag_to_field_rewrites_line_protocol_file(
    tmp_path: Path,
) -> None:
    """The CLI should convert the tag and drop it from the series key."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "weather,region=us,zone=north temp=82\ncpu,region=us value=1i\n"
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "convert-tag-to-field",
            str(data_file),
            "region",
        ],
    )

    assert result.exit_code == 0
    assert result.output == ""
    assert data_file.read_text(encoding="utf-8") == _with_header(
        'weather,zone=north temp=82,region="us"\ncpu value=1i,region="us"\n'
    )


def test_convert_tag_to_field_can_be_scoped_to_one_measurement(
    tmp_path: Path,
) -> None:
    """Measurement scoping should preserve tags on other measurements."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header("weather,region=us temp=82\ncpu,region=us value=1i\n"),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "convert-tag-to-field",
            "--measurement",
            "weather",
            str(data_file),
            "region",
        ],
    )

    assert result.exit_code == 0
    assert data_file.read_text(encoding="utf-8") == _with_header(
        'weather temp=82,region="us"\ncpu,region=us value=1i\n'
    )


def test_convert_tag_to_field_escapes_string_field_values(
    tmp_path: Path,
) -> None:
    """Converted field values should remain valid string fields."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            'weather,summary=hot\\,\\ dry\\ day,note=he\\ said\\"hi temp=82\n'
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "convert-tag-to-field",
            str(data_file),
            "note",
        ],
    )

    assert result.exit_code == 0
    assert data_file.read_text(encoding="utf-8") == _with_header(
        'weather,summary=hot\\,\\ dry\\ day temp=82,note="he said\\"hi"\n'
    )


def test_convert_tag_to_field_aborts_if_field_key_already_exists(
    tmp_path: Path,
) -> None:
    """Existing field keys should abort without changing the file."""
    data_file = tmp_path / "data.lp"
    original = 'weather,region=us temp=82,region="west"\n'
    data_file.write_text(_with_header(original), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "convert-tag-to-field",
            str(data_file),
            "region",
        ],
    )

    assert result.exit_code != 0
    assert "field already exists" in result.output
    assert data_file.read_text(encoding="utf-8") == _with_header(original)


def test_convert_tag_to_field_verbose_reports_modified_line_count(
    tmp_path: Path,
) -> None:
    """Verbose mode should report how many lines were modified."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header("weather,region=us temp=82\ncpu,region=us value=1i\n"),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "convert-tag-to-field",
            "-v",
            str(data_file),
            "region",
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Modified 2 lines.\n"
    assert data_file.read_text(encoding="utf-8") == _with_header(
        'weather temp=82,region="us"\ncpu value=1i,region="us"\n'
    )
