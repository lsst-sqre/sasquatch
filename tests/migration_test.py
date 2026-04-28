"""Tests for migration CLI commands."""

from __future__ import annotations

import json
import subprocess
import tarfile
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from sasquatch.cli import main


def _create_backup_tree(tmp_path: Path) -> Path:
    """Create a synthetic backup directory with shard archives."""
    backup_dir = tmp_path / "sasquatch-influxdb-oss-full-20260424T050007Z"
    backup_dir.mkdir()

    archive_path = backup_dir / "20260424T050008Z.s975.tar.gz"
    source_dir = tmp_path / "source"
    shard_dir = source_dir / "lsst.square.metrics" / "autogen" / "975"
    shard_dir.mkdir(parents=True)
    tsm_path = shard_dir / "000000008-000000002.tsm"
    tsm_path.write_text("placeholder", encoding="utf-8")

    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(
            tsm_path,
            arcname="lsst.square.metrics/autogen/975/000000008-000000002.tsm",
        )

    return backup_dir


def _read_manifest(work_dir: Path) -> dict[str, Any]:
    """Load the discover manifest from a work directory."""
    manifests = list(work_dir.rglob("migration-manifest.json"))
    assert len(manifests) == 1
    return json.loads(manifests[0].read_text(encoding="utf-8"))


def test_migrate_discover_creates_manifest(tmp_path: Path) -> None:
    """Discover should create a manifest from shard archives."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "discover",
            "--backup-dir",
            str(backup_dir),
            "--database",
            "lsst.square.metrics",
            "--retention",
            "autogen",
            "--shard",
            "975",
            "--work-dir",
            str(work_dir),
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Discovered 1 TSM file(s) in 1 shard(s).\n"

    manifest = _read_manifest(work_dir)
    assert manifest["database"] == "lsst.square.metrics"
    assert manifest["retention"] == "autogen"
    assert manifest["shards"] == ["975"]
    assert manifest["status"] == "discovered"
    assert len(manifest["files"]) == 1
    assert _read_manifest(
        work_dir
    )  # manifest exists under the shortened run dir
    run_dir = next(work_dir.iterdir())
    assert run_dir.name.startswith("lsst.square.metrics--autogen--")
    assert run_dir.name.count("--") == 2


def test_influxdb_help_shows_line_protocol_and_migrate_groups() -> None:
    """The InfluxDB CLI should separate line protocol and migration tools."""
    runner = CliRunner()
    result = runner.invoke(main, ["influxdb", "--help"])

    assert result.exit_code == 0
    assert "line-protocol" in result.output
    assert "migrate" in result.output
    assert "drop-tag" not in result.output


def test_migrate_discover_rejects_missing_shard(tmp_path: Path) -> None:
    """Discover should fail when a requested shard is not present."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "discover",
            "--backup-dir",
            str(backup_dir),
            "--database",
            "lsst.square.metrics",
            "--retention",
            "autogen",
            "--shard",
            "998",
            "--work-dir",
            str(work_dir),
        ],
    )

    assert result.exit_code != 0
    assert "No TSM files found for shard '998'" in result.output


def test_migrate_discover_real_sample_data(tmp_path: Path) -> None:
    """Discover should find the sample shard shipped in the repo."""
    backup_dir = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "sasquatch-influxdb-oss-full-20260421T050014Z"
    )
    work_dir = tmp_path / "work"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "discover",
            "--backup-dir",
            str(backup_dir),
            "--database",
            "lsst.square.metrics",
            "--retention",
            "autogen",
            "--shard",
            "975",
            "--work-dir",
            str(work_dir),
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Discovered 1 TSM file(s) in 1 shard(s).\n"

    manifest = _read_manifest(work_dir)
    assert manifest["shards"] == ["975"]
    member_paths = [
        record["archive_member_path"] for record in manifest["files"]
    ]
    assert member_paths == [
        "lsst.square.metrics/autogen/975/000000008-000000002.tsm",
    ]


def test_migrate_export_updates_manifest_and_writes_lp(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Export should stage TSM files and write LP output."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"

    def fake_run(
        argv: list[str],
        *,
        capture_output: bool,
        check: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        assert capture_output is True
        assert check is False
        assert text is True
        assert argv[0] == "influx_inspect"
        out_path = Path(argv[argv.index("-out") + 1])
        tsm_path = Path(argv[argv.index("-tsmfile") + 1])
        assert tsm_path.exists()
        out_path.write_text(
            "weather,region=us temp=82\n",
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(argv, 0, "exported", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    runner = CliRunner()

    discover_result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "discover",
            "--backup-dir",
            str(backup_dir),
            "--database",
            "lsst.square.metrics",
            "--retention",
            "autogen",
            "--shard",
            "975",
            "--work-dir",
            str(work_dir),
        ],
    )
    assert discover_result.exit_code == 0

    export_result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "export",
            "--backup-dir",
            str(backup_dir),
            "--database",
            "lsst.square.metrics",
            "--retention",
            "autogen",
            "--shard",
            "975",
            "--work-dir",
            str(work_dir),
        ],
    )

    assert export_result.exit_code == 0
    assert export_result.output == "Exported 1 file(s).\n"

    manifest = _read_manifest(work_dir)
    assert manifest["status"] == "exported"
    file_record = manifest["files"][0]
    assert file_record["exported_at"] is not None
    assert file_record["extracted_tsm_path"] is not None
    assert file_record["export_log_path"] is not None
    export_lp_path = Path(file_record["export_lp_path"])
    assert export_lp_path.read_text(encoding="utf-8") == (
        "weather,region=us temp=82\n"
    )


def test_migrate_export_discovers_when_manifest_is_empty(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Export should perform discovery first when no manifest exists yet."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"

    def fake_run(
        argv: list[str],
        *,
        capture_output: bool,
        check: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        out_path = Path(argv[argv.index("-out") + 1])
        out_path.write_text("cpu value=1i\n", encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0, "exported", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "export",
            "--backup-dir",
            str(backup_dir),
            "--database",
            "lsst.square.metrics",
            "--retention",
            "autogen",
            "--shard",
            "975",
            "--work-dir",
            str(work_dir),
        ],
    )

    assert result.exit_code == 0
    manifest = _read_manifest(work_dir)
    assert manifest["status"] == "exported"
    assert len(manifest["files"]) == 1
