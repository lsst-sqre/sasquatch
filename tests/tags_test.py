"""Tests for line protocol tag parsing."""

from __future__ import annotations

from pathlib import Path

from sasquatch.tags import extract_measurement_tag_keys


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
    data_file.write_text(line_protocol, encoding="utf-8")

    assert extract_measurement_tag_keys(data_file) == {
        "weather station": ["region", "tag,key"],
    }


def test_extract_measurement_tag_keys_keeps_measurements_without_tags(
    tmp_path: Path,
) -> None:
    """Measurements without tags should still be reported."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        "cpu value=1i\ndisk,device=sda1 used_percent=73.2",
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
        "\n# this is a comment\nsystem,host=foo load=1\n   \n"
        "# another comment",
        encoding="utf-8",
    )

    assert extract_measurement_tag_keys(data_file) == {"system": ["host"]}


def test_extract_measurement_tag_keys_allows_escaped_equals_in_tag_values(
    tmp_path: Path,
) -> None:
    """An escaped equals sign in a tag value should not split the tag."""
    data_file = tmp_path / "data.lp"
    data_file.write_text(
        (
            "requests,path=/api/v1,label=build\\=stable,status=200 "
            "duration_ms=12"
        ),
        encoding="utf-8",
    )

    assert extract_measurement_tag_keys(data_file) == {
        "requests": ["label", "path", "status"],
    }
