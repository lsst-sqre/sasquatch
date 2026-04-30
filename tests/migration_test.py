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
    source_dir = tmp_path / "source"
    matching_shards = {
        "975": "000000008-000000002.tsm",
        "986": "000000010-000000001.tsm",
    }
    for shard_id, file_name in matching_shards.items():
        archive_path = backup_dir / f"20260424T050008Z.s{shard_id}.tar.gz"
        shard_dir = source_dir / "lsst.square.metrics" / "autogen" / shard_id
        shard_dir.mkdir(parents=True, exist_ok=True)
        tsm_path = shard_dir / file_name
        tsm_path.write_text("placeholder", encoding="utf-8")
        with tarfile.open(archive_path, "w:gz") as archive:
            archive.add(
                tsm_path,
                arcname=(
                    f"lsst.square.metrics/autogen/{shard_id}/{file_name}"
                ),
            )

    other_archive = backup_dir / "20260424T050008Z.s999.tar.gz"
    other_shard_dir = source_dir / "other.metrics" / "autogen" / "999"
    other_shard_dir.mkdir(parents=True, exist_ok=True)
    other_tsm_path = other_shard_dir / "000000001-000000001.tsm"
    other_tsm_path.write_text("placeholder", encoding="utf-8")
    with tarfile.open(other_archive, "w:gz") as archive:
        archive.add(
            other_tsm_path,
            arcname="other.metrics/autogen/999/000000001-000000001.tsm",
        )

    manifest_path = backup_dir / "20260424T050007Z.manifest"
    manifest_path.write_text(
        json.dumps(
            {
                "meta": {
                    "fileName": "20260424T050007Z.meta",
                    "size": 12111,
                },
                "limited": False,
                "files": [
                    {
                        "database": "lsst.square.metrics",
                        "policy": "autogen",
                        "shardID": 975,
                        "fileName": "20260424T050008Z.s975.tar.gz",
                        "size": 1024,
                        "lastModified": 0,
                    },
                    {
                        "database": "lsst.square.metrics",
                        "policy": "autogen",
                        "shardID": 986,
                        "fileName": "20260424T050008Z.s986.tar.gz",
                        "size": 1024,
                        "lastModified": 0,
                    },
                    {
                        "database": "other.metrics",
                        "policy": "autogen",
                        "shardID": 999,
                        "fileName": "20260424T050008Z.s999.tar.gz",
                        "size": 1024,
                        "lastModified": 0,
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return backup_dir


def _create_backup_tree_without_manifest(tmp_path: Path) -> Path:
    """Create a synthetic backup directory without a backup manifest."""
    backup_dir = _create_backup_tree(tmp_path)
    for manifest_path in backup_dir.glob("*.manifest"):
        manifest_path.unlink()
    return backup_dir


def _read_manifest(work_dir: Path) -> dict[str, Any]:
    """Load the discover manifest from a work directory."""
    manifests = list(work_dir.rglob("migration-manifest.json"))
    assert len(manifests) == 1
    return json.loads(manifests[0].read_text(encoding="utf-8"))


def _write_exported_lp(work_dir: Path, content: str) -> Path:
    """Write exported line protocol content for the current manifest."""
    manifest = _read_manifest(work_dir)
    export_lp_path = Path(manifest["files"][0]["export_lp_path"])
    export_lp_path.parent.mkdir(parents=True, exist_ok=True)
    export_lp_path.write_text(content, encoding="utf-8")
    return export_lp_path


def _write_all_exported_lp(
    work_dir: Path,
    content_by_shard: dict[str, str],
) -> dict[str, Path]:
    """Write exported line protocol content for all manifest files."""
    manifest = _read_manifest(work_dir)
    written: dict[str, Path] = {}
    for record in manifest["files"]:
        shard_id = record["shard_id"]
        export_lp_path = Path(record["export_lp_path"])
        export_lp_path.parent.mkdir(parents=True, exist_ok=True)
        export_lp_path.write_text(content_by_shard[shard_id], encoding="utf-8")
        written[shard_id] = export_lp_path
    return written


def _mark_transformed(work_dir: Path) -> None:
    """Mark the manifest file as transformed for import tests."""
    manifest_path = next(work_dir.rglob("migration-manifest.json"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "transformed"
    for record in manifest["files"]:
        record["transformed_at"] = "2026-04-29T00:00:00+00:00"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _discover_source_run(
    runner: CliRunner,
    backup_dir: Path,
    work_dir: Path,
) -> None:
    """Create a manifest using the source database and retention."""
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


def test_migrate_discover_all_shards_uses_backup_manifest(
    tmp_path: Path,
) -> None:
    """Discover all-shards should use the backup manifest as its source."""
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
            "--all-shards",
            "--work-dir",
            str(work_dir),
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Discovered 2 TSM file(s) in 2 shard(s).\n"
    manifest = _read_manifest(work_dir)
    assert manifest["all_shards"] is True
    assert manifest["shards"] == ["975", "986"]
    assert {record["shard_id"] for record in manifest["files"]} == {
        "975",
        "986",
    }


def test_migrate_discover_all_shards_requires_backup_manifest(
    tmp_path: Path,
) -> None:
    """Discover all-shards should fail without a backup manifest."""
    backup_dir = _create_backup_tree_without_manifest(tmp_path)
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
            "--all-shards",
            "--work-dir",
            str(work_dir),
        ],
    )

    assert result.exit_code != 0
    assert "No backup manifest file found" in result.output


def test_migrate_discover_all_shards_rejects_multiple_manifests(
    tmp_path: Path,
) -> None:
    """Discover all-shards should fail when multiple backup manifests exist."""
    backup_dir = _create_backup_tree(tmp_path)
    extra_manifest = backup_dir / "extra.manifest"
    extra_manifest.write_text('{"files": []}\n', encoding="utf-8")
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
            "--all-shards",
            "--work-dir",
            str(work_dir),
        ],
    )

    assert result.exit_code != 0
    assert "Multiple backup manifest files found" in result.output


def test_migrate_discover_all_shards_rejects_no_matching_manifest_entries(
    tmp_path: Path,
) -> None:
    """Discover all-shards should fail when the manifest has no matches."""
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
            "missing.metrics",
            "--retention",
            "autogen",
            "--all-shards",
            "--work-dir",
            str(work_dir),
        ],
    )

    assert result.exit_code != 0
    assert "No shard entries found in the backup manifest" in result.output


def test_migrate_discover_all_shards_rejects_missing_archive(
    tmp_path: Path,
) -> None:
    """Discover all-shards should fail when a manifest archive is missing."""
    backup_dir = _create_backup_tree(tmp_path)
    (backup_dir / "20260424T050008Z.s986.tar.gz").unlink()
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
            "--all-shards",
            "--work-dir",
            str(work_dir),
        ],
    )

    assert result.exit_code != 0
    assert "Backup shard archive" in result.output
    assert "is missing." in result.output


def test_migrate_discover_all_shards_rejects_archive_without_matching_tsm(
    tmp_path: Path,
) -> None:
    """Discover all-shards should fail when a shard has no matching TSM."""
    backup_dir = _create_backup_tree(tmp_path)
    broken_archive = backup_dir / "20260424T050008Z.s986.tar.gz"
    source_dir = tmp_path / "broken"
    wrong_dir = source_dir / "wrong.metrics" / "autogen" / "986"
    wrong_dir.mkdir(parents=True)
    wrong_tsm_path = wrong_dir / "000000010-000000001.tsm"
    wrong_tsm_path.write_text("placeholder", encoding="utf-8")
    with tarfile.open(broken_archive, "w:gz") as archive:
        archive.add(
            wrong_tsm_path,
            arcname="wrong.metrics/autogen/986/000000010-000000001.tsm",
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
            "--all-shards",
            "--work-dir",
            str(work_dir),
        ],
    )

    assert result.exit_code != 0
    assert "does not contain matching TSM files" in result.output


@pytest.mark.parametrize(
    ("command", "extra_args"),
    [
        ("discover", []),
        ("export", []),
        ("transform", ["--plan", "PLACEHOLDER"]),
        ("import", ["--host", "influxdb.example.org"]),
    ],
)
def test_migrate_commands_reject_mixed_shard_selection(
    command: str,
    extra_args: list[str],
    tmp_path: Path,
) -> None:
    """Commands should reject mixing --shard with --all-shards."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text("- op: drop-tag\n  tag: region\n", encoding="utf-8")
    resolved_extra_args = [
        str(plan_path) if arg == "PLACEHOLDER" else arg for arg in extra_args
    ]

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            command,
            "--backup-dir",
            str(backup_dir),
            "--database",
            "lsst.square.metrics",
            "--retention",
            "autogen",
            "--shard",
            "975",
            "--all-shards",
            "--work-dir",
            str(work_dir),
            *resolved_extra_args,
        ],
    )

    assert result.exit_code != 0
    assert "Use either --shard or --all-shards, not both." in result.output


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
        assert "-lponly" in argv
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


def test_migrate_export_all_shards_bootstraps_manifest_discovery(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Export all-shards should discover through the backup manifest."""
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
            "--all-shards",
            "--work-dir",
            str(work_dir),
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Exported 2 file(s).\n"
    manifest = _read_manifest(work_dir)
    assert manifest["all_shards"] is True
    assert manifest["shards"] == ["975", "986"]
    assert len(manifest["files"]) == 2


def test_migrate_export_all_shards_requires_manifest_when_bootstrapping(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Export all-shards should fail without a backup manifest."""
    backup_dir = _create_backup_tree_without_manifest(tmp_path)
    work_dir = tmp_path / "work"

    def fake_run(
        argv: list[str],
        *,
        capture_output: bool,
        check: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
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
            "--all-shards",
            "--work-dir",
            str(work_dir),
        ],
    )

    assert result.exit_code != 0
    assert "No backup manifest file found" in result.output


def test_migrate_transform_updates_manifest_and_rewrites_lp(
    tmp_path: Path,
) -> None:
    """Transform should apply a YAML plan and update manifest state."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        "- op: drop-tag\n  tag: region\n",
        encoding="utf-8",
    )

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

    export_lp_path = _write_exported_lp(
        work_dir,
        "weather,region=us temp=82\n",
    )

    transform_result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "transform",
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
            "--plan",
            str(plan_path),
        ],
    )

    assert transform_result.exit_code == 0
    assert transform_result.output == "Transformed 1 file(s).\n"
    assert export_lp_path.read_text(encoding="utf-8") == "weather temp=82\n"

    manifest = _read_manifest(work_dir)
    assert manifest["status"] == "transformed"
    assert manifest["transform_plan_path"] == str(plan_path)
    assert manifest["transform_plan_hash"] is not None
    assert manifest["files"][0]["transformed_at"] is not None


def test_migrate_transform_skips_already_transformed_files(
    tmp_path: Path,
) -> None:
    """Transform should skip files already marked transformed."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        "- op: drop-tag\n  tag: region\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    runner.invoke(
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
    export_lp_path = _write_exported_lp(
        work_dir,
        "weather,region=us temp=82\n",
    )

    first_result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "transform",
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
            "--plan",
            str(plan_path),
        ],
    )
    assert first_result.exit_code == 0

    export_lp_path.write_text("weather temp=82\n", encoding="utf-8")
    second_result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "transform",
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
            "--plan",
            str(plan_path),
        ],
    )

    assert second_result.exit_code == 0
    assert second_result.output == "Transformed 0 file(s).\n"
    assert export_lp_path.read_text(encoding="utf-8") == "weather temp=82\n"


def test_migrate_transform_reapplies_with_force(tmp_path: Path) -> None:
    """Transform should rerun a plan when --force is supplied."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"
    first_plan = tmp_path / "drop-tag.yaml"
    first_plan.write_text(
        "- op: drop-tag\n  tag: region\n",
        encoding="utf-8",
    )
    second_plan = tmp_path / "rename-measurement.yaml"
    second_plan.write_text(
        "- op: rename-measurement\n  from: weather\n  to: climate\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    runner.invoke(
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
    export_lp_path = _write_exported_lp(
        work_dir,
        "weather,region=us temp=82\n",
    )

    first_result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "transform",
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
            "--plan",
            str(first_plan),
        ],
    )
    assert first_result.exit_code == 0

    second_result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "transform",
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
            "--plan",
            str(second_plan),
            "--force",
        ],
    )

    assert second_result.exit_code == 0
    assert export_lp_path.read_text(encoding="utf-8") == "climate temp=82\n"


def test_migrate_transform_rejects_invalid_plan_extension(
    tmp_path: Path,
) -> None:
    """Transform should require a YAML extension."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"
    plan_path = tmp_path / "plan.json"
    plan_path.write_text("[]", encoding="utf-8")

    runner = CliRunner()
    runner.invoke(
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
    _write_exported_lp(work_dir, "weather,region=us temp=82\n")

    result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "transform",
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
            "--plan",
            str(plan_path),
        ],
    )

    assert result.exit_code != 0
    assert (
        "Transform plan must use a .yaml or .yml extension." in result.output
    )


def test_migrate_transform_rejects_unknown_operation(tmp_path: Path) -> None:
    """Transform should reject unknown operations in the YAML plan."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        "- op: surprise\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    runner.invoke(
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
    _write_exported_lp(work_dir, "weather,region=us temp=82\n")

    result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "transform",
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
            "--plan",
            str(plan_path),
        ],
    )

    assert result.exit_code != 0
    assert "Unknown transform operation 'surprise'." in result.output


def test_migrate_transform_requires_exported_file(tmp_path: Path) -> None:
    """Transform should fail when the exported LP file is missing."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        "- op: drop-tag\n  tag: region\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    runner.invoke(
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

    result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "transform",
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
            "--plan",
            str(plan_path),
        ],
    )

    assert result.exit_code != 0
    assert "is missing. Run export first." in result.output


def test_migrate_transform_rejects_changed_plan_without_force(
    tmp_path: Path,
) -> None:
    """Transform should reject a changed plan hash unless forced."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"
    first_plan = tmp_path / "first.yaml"
    first_plan.write_text(
        "- op: drop-tag\n  tag: region\n",
        encoding="utf-8",
    )
    second_plan = tmp_path / "second.yaml"
    second_plan.write_text(
        "- op: rename-measurement\n  from: weather\n  to: climate\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    runner.invoke(
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
    _write_exported_lp(work_dir, "weather,region=us temp=82\n")

    first_result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "transform",
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
            "--plan",
            str(first_plan),
        ],
    )
    assert first_result.exit_code == 0

    second_result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "transform",
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
            "--plan",
            str(second_plan),
        ],
    )

    assert second_result.exit_code != 0
    assert (
        "Transform plan changed for an existing run." in second_result.output
    )


def test_migrate_transform_reports_tag_to_field_conflicts(
    tmp_path: Path,
) -> None:
    """Transform should surface tag-to-field conflicts."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        "- op: convert-tag-to-field\n  tag: region\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    runner.invoke(
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
    _write_exported_lp(work_dir, 'weather,region=us region="west"\n')

    result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "transform",
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
            "--plan",
            str(plan_path),
        ],
    )

    assert result.exit_code != 0
    manifest = _read_manifest(work_dir)
    assert manifest["files"][0]["last_error"] is not None


def test_migrate_transform_defaults_to_all_shards(
    tmp_path: Path,
) -> None:
    """Transform should default to the all-shards run."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text("- op: drop-tag\n  tag: region\n", encoding="utf-8")

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
            "--all-shards",
            "--work-dir",
            str(work_dir),
        ],
    )
    assert discover_result.exit_code == 0
    file_paths = _write_all_exported_lp(
        work_dir,
        {
            "975": "weather,region=us temp=82\n",
            "986": "cpu,region=us value=1i\n",
        },
    )

    result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "transform",
            "--backup-dir",
            str(backup_dir),
            "--database",
            "lsst.square.metrics",
            "--retention",
            "autogen",
            "--work-dir",
            str(work_dir),
            "--plan",
            str(plan_path),
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Transformed 2 file(s).\n"
    assert file_paths["975"].read_text(encoding="utf-8") == "weather temp=82\n"
    assert file_paths["986"].read_text(encoding="utf-8") == "cpu value=1i\n"


def test_migrate_import_updates_manifest_and_rewrites_headers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Import should rewrite headers and update import state."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"
    runner = CliRunner()
    _discover_source_run(runner, backup_dir, work_dir)
    file_path = _write_exported_lp(
        work_dir,
        "# DML\n"
        "# CONTEXT-DATABASE: lsst.square.metrics\n"
        "# CONTEXT-RETENTION-POLICY: autogen\n"
        "weather temp=82\n",
    )
    _mark_transformed(work_dir)

    def fake_run(
        argv: list[str],
        *,
        capture_output: bool,
        check: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        assert argv[0] == "influx"
        assert "-host" in argv
        assert "-import" in argv
        return subprocess.CompletedProcess(argv, 0, "imported", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "import",
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
            "--host",
            "influxdb.example.org",
            "--target-database",
            "target.metrics",
            "--target-retention",
            "forever",
        ],
    )

    assert result.exit_code == 0
    assert "Updated import headers in" in result.output
    assert "Imported 1 file(s)." in result.output
    content = file_path.read_text(encoding="utf-8")
    assert "# CONTEXT-DATABASE: target.metrics\n" in content
    assert "# CONTEXT-RETENTION-POLICY: forever\n" in content
    manifest = _read_manifest(work_dir)
    assert manifest["status"] == "imported"
    assert manifest["files"][0]["imported_at"] is not None
    assert manifest["files"][0]["import_log_path"] is not None


def test_migrate_import_adds_missing_headers_and_reports_it(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Import should add missing DML headers."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"
    runner = CliRunner()
    _discover_source_run(runner, backup_dir, work_dir)
    file_path = _write_exported_lp(work_dir, "weather temp=82\n")
    _mark_transformed(work_dir)

    def fake_run(
        argv: list[str],
        *,
        capture_output: bool,
        check: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 0, "imported", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "import",
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
            "--host",
            "influxdb.example.org",
            "--target-database",
            "target.metrics",
            "--target-retention",
            "forever",
        ],
    )

    assert result.exit_code == 0
    assert "Added import headers to" in result.output
    content = file_path.read_text(encoding="utf-8")
    assert content.startswith(
        "# DML\n"
        "# CONTEXT-DATABASE: target.metrics\n"
        "# CONTEXT-RETENTION-POLICY: forever\n"
    )


def test_migrate_import_is_quiet_when_headers_already_match(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Import should not print per-file header output when unchanged."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"
    runner = CliRunner()
    _discover_source_run(runner, backup_dir, work_dir)
    _write_exported_lp(
        work_dir,
        "# DML\n"
        "# CONTEXT-DATABASE: target.metrics\n"
        "# CONTEXT-RETENTION-POLICY: forever\n"
        "weather temp=82\n",
    )
    _mark_transformed(work_dir)

    def fake_run(
        argv: list[str],
        *,
        capture_output: bool,
        check: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 0, "imported", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "import",
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
            "--host",
            "influxdb.example.org",
            "--target-database",
            "target.metrics",
            "--target-retention",
            "forever",
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Imported 1 file(s).\n"


def test_migrate_import_skips_already_imported_without_force(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Import should skip files already marked imported."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"
    runner = CliRunner()
    _discover_source_run(runner, backup_dir, work_dir)
    _write_exported_lp(work_dir, "weather temp=82\n")
    _mark_transformed(work_dir)
    manifest_path = next(work_dir.rglob("migration-manifest.json"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["imported_at"] = "2026-04-29T00:00:00+00:00"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    calls = 0

    def fake_run(
        argv: list[str],
        *,
        capture_output: bool,
        check: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        nonlocal calls
        calls += 1
        return subprocess.CompletedProcess(argv, 0, "imported", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "import",
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
            "--host",
            "influxdb.example.org",
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Imported 0 file(s).\n"
    assert calls == 0


def test_migrate_import_requires_transformed_file(tmp_path: Path) -> None:
    """Import should fail when transformed_at is missing."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"
    runner = CliRunner()
    _discover_source_run(runner, backup_dir, work_dir)
    _write_exported_lp(work_dir, "weather temp=82\n")

    result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "import",
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
            "--host",
            "influxdb.example.org",
        ],
    )

    assert result.exit_code != 0
    assert "has not been transformed. Run transform first." in result.output


def test_migrate_import_records_subprocess_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Import should record CLI failures in the manifest."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"
    runner = CliRunner()
    _discover_source_run(runner, backup_dir, work_dir)
    _write_exported_lp(work_dir, "weather temp=82\n")
    _mark_transformed(work_dir)

    def fake_run(
        argv: list[str],
        *,
        capture_output: bool,
        check: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 1, "", "boom")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "import",
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
            "--host",
            "influxdb.example.org",
        ],
    )

    assert result.exit_code != 0
    manifest = _read_manifest(work_dir)
    assert manifest["files"][0]["last_error"] == "boom"


def test_migrate_import_defaults_to_all_shards(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Import should default to the all-shards run."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"
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
            "--all-shards",
            "--work-dir",
            str(work_dir),
        ],
    )
    assert discover_result.exit_code == 0
    file_paths = _write_all_exported_lp(
        work_dir,
        {
            "975": "weather temp=82\n",
            "986": "# DML\n# CONTEXT-DATABASE: lsst.square.metrics\n"
            "# CONTEXT-RETENTION-POLICY: autogen\ncpu value=1i\n",
        },
    )
    _mark_transformed(work_dir)

    calls: list[list[str]] = []

    def fake_run(
        argv: list[str],
        *,
        capture_output: bool,
        check: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, "imported", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "import",
            "--backup-dir",
            str(backup_dir),
            "--database",
            "lsst.square.metrics",
            "--retention",
            "autogen",
            "--work-dir",
            str(work_dir),
            "--host",
            "influxdb.example.org",
        ],
    )

    assert result.exit_code == 0
    assert result.output == (
        f"Added import headers to {file_paths['975']} for "
        "database=lsst.square.metrics, retention=autogen.\n"
        "Imported 2 file(s).\n"
    )
    assert len(calls) == 2


def test_explicit_shard_runs_remain_isolated_from_all_shards(
    tmp_path: Path,
) -> None:
    """Explicit shard runs should stay isolated from implicit all-shards."""
    backup_dir = _create_backup_tree(tmp_path)
    work_dir = tmp_path / "work"
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text("- op: drop-tag\n  tag: region\n", encoding="utf-8")

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
    _write_exported_lp(work_dir, "weather,region=us temp=82\n")

    result = runner.invoke(
        main,
        [
            "influxdb",
            "migrate",
            "transform",
            "--backup-dir",
            str(backup_dir),
            "--database",
            "lsst.square.metrics",
            "--retention",
            "autogen",
            "--work-dir",
            str(work_dir),
            "--plan",
            str(plan_path),
        ],
    )

    assert result.exit_code != 0
    assert (
        "No discovered files found in the manifest. Run export first."
        in result.output
    )
