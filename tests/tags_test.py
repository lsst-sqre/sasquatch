"""Tests for line protocol tag parsing."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from sasquatch.cli import main
from sasquatch.tags import extract_measurement_tag_keys

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


def test_extract_measurement_tag_keys_with_escaped_separators(
    tmp_path: Path,
) -> None:
    """Escaped spaces and commas should stay inside identifiers."""
    line_protocol = (
        "weather\\ station,region=us\\ west,tag\\,key=value\\,one "
        "temperature=82\n"
        "weather\\ station,region=us\\ west,tag\\,key=another\\ value "
        "humidity=41"
    )
    data_file = tmp_path / "data.lp"
    data_file.write_text(_with_header(line_protocol), encoding="utf-8")

    assert extract_measurement_tag_keys(data_file) == {
        "weather station": ["region", "tag,key"],
    }


def test_extract_measurement_tag_keys_keeps_measurements_without_tags(
    tmp_path: Path,
) -> None:
    """Measurements without tags should still be reported."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header("cpu value=1i\ndisk,device=sda1 used_percent=73.2"),
        encoding="utf-8",
    )

    assert extract_measurement_tag_keys(data_file) == {
        "cpu": [],
        "disk": ["device"],
    }


def test_extract_measurement_tag_keys_ignores_comments_and_blank_lines(
    tmp_path: Path,
) -> None:
    """Comments and blank lines should not affect parsing."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "\n# this is a comment\nsystem,host=foo load=1\n   \n"
            "# another comment"
        ),
        encoding="utf-8",
    )

    assert extract_measurement_tag_keys(data_file) == {"system": ["host"]}


def test_extract_measurement_tag_keys_allows_escaped_equals_in_tag_values(
    tmp_path: Path,
) -> None:
    """An escaped equals sign in a tag value should not split the tag."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "requests,path=/api/v1,label=build\\=stable,status=200 "
            "duration_ms=12"
        ),
        encoding="utf-8",
    )

    assert extract_measurement_tag_keys(data_file) == {
        "requests": ["label", "path", "status"],
    }


def test_drop_measurement_tag_key_rewrites_line_protocol_file(
    tmp_path: Path,
) -> None:
    """The CLI should remove matching tags and keep the rest unchanged."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "# comment\n"
            "weather\\ station,region=us\\ west,"
            "tag\\,key=value\\,one temp=82\n"
            "weather\\ station,region=us\\ west,zone=north humidity=41\n"
            "cpu value=1i\n"
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["influxdb", "line-protocol", "drop-tag", str(data_file), "region"],
    )

    assert result.exit_code == 0
    assert result.output == ""
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "# comment\n"
        "weather\\ station,tag\\,key=value\\,one temp=82\n"
        "weather\\ station,zone=north humidity=41\n"
        "cpu value=1i\n"
    )


def test_drop_measurement_tag_key_matches_unescaped_tag_keys(
    tmp_path: Path,
) -> None:
    """Dropping a tag should work even when the key is escaped in the file."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header("measurement,tag\\,key=value,region=us field=1\n"),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["influxdb", "line-protocol", "drop-tag", str(data_file), "tag,key"],
    )

    assert result.exit_code == 0
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "measurement,region=us field=1\n"
    )


def test_drop_measurement_tag_key_verbose_reports_modified_line_count(
    tmp_path: Path,
) -> None:
    """Verbose mode should report how many lines changed."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "weather,region=us temp=82\n"
            "weather,region=us,zone=north humidity=41\n"
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
            "drop-tag",
            "-v",
            str(data_file),
            "region",
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Modified 2 lines.\n"
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "weather temp=82\nweather,zone=north humidity=41\ncpu value=1i\n"
    )


def test_drop_measurement_tag_key_can_be_scoped_to_one_measurement(
    tmp_path: Path,
) -> None:
    """Measurement scoping should preserve matching tags elsewhere."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "weather,region=us,zone=north temp=82\n"
            "cpu,region=us host=worker-1 value=1i\n"
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
            "drop-tag",
            "--measurement",
            "weather",
            str(data_file),
            "region",
        ],
    )

    assert result.exit_code == 0
    assert result.output == ""
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "weather,zone=north temp=82\n"
        "cpu,region=us host=worker-1 value=1i\n"
        "weather humidity=41\n"
    )


def test_drop_measurement_tag_key_verbose_reports_scoped_line_count(
    tmp_path: Path,
) -> None:
    """Count only modified lines in the target measurement."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "weather,region=us temp=82\n"
            "cpu,region=us value=1i\n"
            "weather,region=eu,zone=north humidity=41\n"
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "drop-tag",
            "-v",
            "-m",
            "weather",
            str(data_file),
            "region",
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Modified 2 lines.\n"
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "weather temp=82\n"
        "cpu,region=us value=1i\n"
        "weather,zone=north humidity=41\n"
    )


def test_rename_tag_rewrites_line_protocol_file(tmp_path: Path) -> None:
    """The CLI should rename matching tags and keep the rest unchanged."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "# comment\n"
            "weather,region=us,zone=north temp=82\n"
            "cpu,region=us value=1i\n"
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "line-protocol",
            "rename-tag",
            str(data_file),
            "region",
            "site",
        ],
    )

    assert result.exit_code == 0
    assert result.output == ""
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "# comment\nweather,site=us,zone=north temp=82\ncpu,site=us value=1i\n"
    )


def test_rename_tag_can_be_scoped_to_one_measurement(tmp_path: Path) -> None:
    """Measurement scoping should preserve matching tags elsewhere."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        _with_header(
            "weather,region=us,zone=north temp=82\n"
            "cpu,region=us value=1i\n"
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
            "rename-tag",
            "--measurement",
            "weather",
            str(data_file),
            "region",
            "site",
        ],
    )

    assert result.exit_code == 0
    assert result.output == ""
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "weather,site=us,zone=north temp=82\n"
        "cpu,region=us value=1i\n"
        "weather,site=eu humidity=41\n"
    )


def test_rename_tag_escapes_new_tag_key_and_reports_verbose_count(
    tmp_path: Path,
) -> None:
    """Verbose mode should report changes and escaped new keys stay valid."""
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
            "rename-tag",
            "-v",
            "-m",
            "weather",
            str(data_file),
            "region",
            "site area",
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Modified 1 lines.\n"
    assert data_file.read_text(encoding="utf-8") == _with_header(
        "weather,site\\ area=us temp=82\ncpu,region=us value=1i\n"
    )
