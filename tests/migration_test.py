"""Tests for migration CLI commands."""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

from click.testing import CliRunner

from sasquatch.cli import main


def _create_backup_tree(tmp_path: Path) -> Path:
    """Create a synthetic backup directory with shard archives."""
    backup_dir = tmp_path / "sasquatch-influxdb-oss-full-20260424T050007Z"
    backup_dir.mkdir()

    archive_path = backup_dir / "20260424T050008Z.s997.tar.gz"
    source_dir = tmp_path / "source"
    shard_dir = source_dir / "lsst.square.metrics" / "autogen" / "997"
    shard_dir.mkdir(parents=True)
    tsm_path = shard_dir / "000000009-000000002.tsm"
    tsm_path.write_text("placeholder", encoding="utf-8")

    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(
            tsm_path,
            arcname="lsst.square.metrics/autogen/997/000000009-000000002.tsm",
        )

    return backup_dir


def _read_manifest(work_dir: Path) -> dict[str, object]:
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
            "997",
            "--work-dir",
            str(work_dir),
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Discovered 1 TSM file(s) in 1 shard(s).\n"

    manifest = _read_manifest(work_dir)
    assert manifest["database"] == "lsst.square.metrics"
    assert manifest["retention"] == "autogen"
    assert manifest["shards"] == ["997"]
    assert manifest["status"] == "discovered"
    assert len(manifest["files"]) == 1
    assert _read_manifest(
        work_dir
    )  # manifest exists under the shortened run dir
    run_dir = next(work_dir.iterdir())
    assert run_dir.name.startswith("lsst.square.metrics--autogen--")
    assert run_dir.name.count("--") == 2


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
    """Discover should find the three sample shards shipped in the repo."""
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
            "--shard",
            "986",
            "--shard",
            "997",
            "--work-dir",
            str(work_dir),
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Discovered 3 TSM file(s) in 3 shard(s).\n"

    manifest = _read_manifest(work_dir)
    assert manifest["shards"] == ["975", "986", "997"]
    member_paths = [
        record["archive_member_path"] for record in manifest["files"]
    ]
    assert member_paths == [
        "lsst.square.metrics/autogen/975/000000008-000000002.tsm",
        "lsst.square.metrics/autogen/986/000000009-000000002.tsm",
        "lsst.square.metrics/autogen/997/000000009-000000002.tsm",
    ]
