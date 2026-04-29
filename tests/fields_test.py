"""Tests for line protocol field parsing."""

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


def test_show_fields_groups_field_keys_by_measurement(tmp_path: Path) -> None:
    """The CLI should print field keys grouped by measurement."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header("weather,region=us temp=82,humidity=41i\ncpu value=1i\n"),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["influxdb", "line-protocol", "show-fields", str(data_file)],
    )

    assert result.exit_code == 0
    assert result.output == "cpu: value\nweather: humidity, temp\n"


def test_show_fields_handles_quoted_string_values_with_commas_and_spaces(
    tmp_path: Path,
) -> None:
    """Quoted string field values should not break field parsing."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            'weather,region=us temp=82,summary="hot, dry day",'
            'note="clear sky"\n'
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["influxdb", "line-protocol", "show-fields", str(data_file)],
    )

    assert result.exit_code == 0
    assert result.output == "weather: note, summary, temp\n"


def test_drop_field_rewrites_line_protocol_file(tmp_path: Path) -> None:
    """The CLI should remove matching fields and keep the rest unchanged."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "# comment\n"
            'weather,region=us temp=82,summary="hot, dry day"\n'
            "weather,region=us humidity=41i,status=1i\n"
            "cpu value=1i\n"
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["influxdb", "line-protocol", "drop-field", str(data_file), "summary"],
    )

    assert result.exit_code == 0
    assert result.output == ""
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "# comment\n"
        "weather,region=us temp=82\n"
        "weather,region=us humidity=41i,status=1i\n"
        "cpu value=1i\n"
    )


def test_drop_field_drops_lines_with_no_remaining_fields(
    tmp_path: Path,
) -> None:
    """Dropping the only field should remove the whole record line."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "weather,region=us temp=82\n"
            "weather,region=us humidity=41i,temp=83\n"
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["influxdb", "line-protocol", "drop-field", str(data_file), "temp"],
    )

    assert result.exit_code == 0
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "weather,region=us humidity=41i\n"
    )


def test_drop_field_verbose_reports_modified_line_count(
    tmp_path: Path,
) -> None:
    """Verbose mode should report how many lines changed."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "weather temp=82,humidity=41i\n"
            'weather summary="hot, dry day",status=1i\n'
            "cpu value=1i\n"
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "drop-field",
            "-v",
            str(data_file),
            "summary",
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Modified 1 lines.\n"
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "weather temp=82,humidity=41i\nweather status=1i\ncpu value=1i\n"
    )


def test_drop_field_can_be_scoped_to_one_measurement(tmp_path: Path) -> None:
    """Measurement scoping should preserve matching fields elsewhere."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "weather temp=82,humidity=41i\n"
            "cpu temp=55i,value=1i\n"
            'weather summary="hot, dry day",status=1i\n'
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "drop-field",
            "--measurement",
            "weather",
            str(data_file),
            "temp",
        ],
    )

    assert result.exit_code == 0
    assert result.output == ""
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "weather humidity=41i\n"
        "cpu temp=55i,value=1i\n"
        'weather summary="hot, dry day",status=1i\n'
    )


def test_drop_field_verbose_reports_scoped_line_count(
    tmp_path: Path,
) -> None:
    """Count only modified lines in the target measurement."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "weather temp=82,humidity=41i\n"
            "cpu temp=55i,value=1i\n"
            "weather temp=83,status=1i\n"
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "drop-field",
            "-v",
            "-m",
            "weather",
            str(data_file),
            "temp",
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Modified 2 lines.\n"
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "weather humidity=41i\ncpu temp=55i,value=1i\nweather status=1i\n"
    )


def test_rename_field_rewrites_line_protocol_file(tmp_path: Path) -> None:
    """The CLI should rename matching fields and keep the rest unchanged."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "# comment\n"
            'weather temp=82,summary="hot, dry day"\n'
            "cpu temp=55i,value=1i\n"
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "rename-field",
            str(data_file),
            "temp",
            "temperature",
        ],
    )

    assert result.exit_code == 0
    assert result.output == ""
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "# comment\n"
        'weather temperature=82,summary="hot, dry day"\n'
        "cpu temperature=55i,value=1i\n"
    )


def test_rename_field_can_be_scoped_to_one_measurement(tmp_path: Path) -> None:
    """Measurement scoping should preserve matching fields elsewhere."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "weather temp=82,humidity=41i\n"
            "cpu temp=55i,value=1i\n"
            "weather temp=83,status=1i\n"
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "rename-field",
            "--measurement",
            "weather",
            str(data_file),
            "temp",
            "temperature",
        ],
    )

    assert result.exit_code == 0
    assert result.output == ""
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "weather temperature=82,humidity=41i\n"
        "cpu temp=55i,value=1i\n"
        "weather temperature=83,status=1i\n"
    )


def test_rename_field_escapes_new_key_and_reports_verbose_count(
    tmp_path: Path,
) -> None:
    """Verbose mode should report changes and escaped new keys stay valid."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header("weather temp=82,humidity=41i\ncpu temp=55i,value=1i\n"),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "rename-field",
            "-v",
            "-m",
            "weather",
            str(data_file),
            "temp",
            "temperature zone",
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Modified 1 lines.\n"
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "weather temperature\\ zone=82,humidity=41i\ncpu temp=55i,value=1i\n"
    )
