"""Commands for InfluxDB migration workflows."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tarfile
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import click


def _utc_now() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return datetime.now(tz=UTC).isoformat()


def _stringify_shards(shards: tuple[str, ...]) -> list[str]:
    """Normalize shard identifiers into non-empty strings."""
    normalized = [str(shard).strip() for shard in shards if str(shard).strip()]
    if not normalized:
        raise click.UsageError("Provide at least one --shard value.")
    return normalized


def _run_id(
    backup_name: str,
    database: str,
    retention: str,
    shards: list[str],
) -> str:
    """Build a deterministic migration run identifier."""
    payload = json.dumps(
        {
            "backup_name": backup_name,
            "database": database,
            "retention": retention,
            "shards": sorted(shards),
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def _slugify(value: str) -> str:
    """Create a filesystem-friendly slug."""
    return "".join(
        char if char.isalnum() or char in ".-_" else "_" for char in value
    )


def _run_dir_name(
    backup_name: str,
    database: str,
    retention: str,
    shards: list[str],
) -> str:
    """Return the per-run working directory name."""
    run_id = _run_id(backup_name, database, retention, shards)
    return f"{_slugify(database)}--{_slugify(retention)}--{run_id}"


def _manifest_path(run_dir: Path) -> Path:
    """Return the manifest path within a run directory."""
    return run_dir / "migration-manifest.json"


def _run_dir(
    work_dir: Path,
    backup_dir: Path,
    database: str,
    retention: str,
    shards: list[str],
) -> Path:
    """Return the working directory for one migration run."""
    return work_dir / _run_dir_name(
        backup_dir.name,
        database,
        retention,
        shards,
    )


@dataclass
class MigrationFileRecord:
    """Metadata for one discovered TSM file."""

    shard_id: str
    archive_path: str
    archive_member_path: str
    export_lp_path: str
    discovered_at: str
    exported_at: str | None = None
    transformed_at: str | None = None
    imported_at: str | None = None
    extracted_tsm_path: str | None = None
    export_log_path: str | None = None
    last_error: str | None = None


@dataclass
class MigrationManifest:
    """Sidecar manifest for a migration run."""

    run_id: str
    backup_dir: str
    backup_name: str
    database: str
    retention: str
    shards: list[str]
    created_at: str
    updated_at: str
    status: str
    files: list[MigrationFileRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Serialize the manifest to JSON-compatible data."""
        return asdict(self)


def _save_manifest(run_dir: Path, manifest: MigrationManifest) -> None:
    """Write the manifest to disk."""
    manifest.updated_at = _utc_now()
    _manifest_path(run_dir).write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load_manifest(
    run_dir: Path,
    backup_dir: Path,
    database: str,
    retention: str,
    shards: list[str],
) -> MigrationManifest:
    """Load an existing manifest or initialize a new one."""
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = _manifest_path(run_dir)
    if manifest_path.exists():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest = MigrationManifest(
            run_id=data["run_id"],
            backup_dir=data["backup_dir"],
            backup_name=data["backup_name"],
            database=data["database"],
            retention=data["retention"],
            shards=list(data["shards"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            status=data["status"],
            files=[
                MigrationFileRecord(**record)
                for record in data.get("files", [])
            ],
        )
        expected = {
            "backup_dir": str(backup_dir),
            "backup_name": backup_dir.name,
            "database": database,
            "retention": retention,
            "shards": sorted(shards),
        }
        actual = {
            "backup_dir": manifest.backup_dir,
            "backup_name": manifest.backup_name,
            "database": manifest.database,
            "retention": manifest.retention,
            "shards": sorted(manifest.shards),
        }
        if actual != expected:
            raise click.ClickException(
                "Existing migration manifest does not match "
                "the supplied inputs."
            )
        return manifest

    now = _utc_now()
    return MigrationManifest(
        run_id=_run_id(backup_dir.name, database, retention, shards),
        backup_dir=str(backup_dir),
        backup_name=backup_dir.name,
        database=database,
        retention=retention,
        shards=sorted(shards),
        created_at=now,
        updated_at=now,
        status="initialized",
    )


def _iter_shard_archives(backup_dir: Path, shard_id: str) -> list[Path]:
    """Return archives that match one shard ID."""
    return sorted(backup_dir.glob(f"*.s{shard_id}.tar.gz"))


def _discover_shard_files(
    backup_dir: Path,
    database: str,
    retention: str,
    shard_id: str,
) -> list[tuple[Path, str]]:
    """Discover TSM files for one shard inside shard archives."""
    discovered: list[tuple[Path, str]] = []
    expected_prefix = f"{database}/{retention}/{shard_id}/"

    for archive_path in _iter_shard_archives(backup_dir, shard_id):
        with tarfile.open(archive_path, "r:gz") as archive:
            for member in archive.getmembers():
                if not member.isfile():
                    continue
                if not member.name.endswith(".tsm"):
                    continue
                if not member.name.startswith(expected_prefix):
                    continue
                discovered.append((archive_path, member.name))

    return discovered


def _discover_files(
    run_dir: Path,
    manifest: MigrationManifest,
    backup_dir: Path,
) -> int:
    """Populate the manifest with discovered shard files."""
    files: list[MigrationFileRecord] = []
    for shard_id in manifest.shards:
        discovered = _discover_shard_files(
            backup_dir,
            manifest.database,
            manifest.retention,
            shard_id,
        )
        if not discovered:
            raise click.ClickException(
                "No TSM files found for shard "
                f"{shard_id!r} in the backup directory."
            )

        for archive_path, member_name in discovered:
            tsm_stem = Path(member_name).stem
            files.append(
                MigrationFileRecord(
                    shard_id=shard_id,
                    archive_path=str(archive_path),
                    archive_member_path=member_name,
                    export_lp_path=str(run_dir / shard_id / f"{tsm_stem}.lp"),
                    discovered_at=_utc_now(),
                )
            )

    manifest.files = sorted(
        files,
        key=lambda record: (
            record.shard_id,
            record.archive_path,
            record.archive_member_path,
        ),
    )
    manifest.status = "discovered"
    _save_manifest(run_dir, manifest)
    return len(manifest.files)


def _extract_archive_member(
    archive_path: Path,
    member_name: str,
    destination: Path,
) -> None:
    """Extract one TSM member from a shard archive."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:gz") as archive:
        extracted = archive.extractfile(member_name)
        if extracted is None:
            raise click.ClickException(
                f"Could not extract {member_name!r} from {archive_path}."
            )
        destination.write_bytes(extracted.read())


def _run_external_command(argv: list[str]) -> subprocess.CompletedProcess[str]:
    """Run an external command and capture its output."""
    try:
        return subprocess.run(
            argv,
            capture_output=True,
            check=False,
            text=True,
        )
    except FileNotFoundError as exc:
        raise click.ClickException(
            f"Required executable {argv[0]!r} was not found."
        ) from exc


def _write_export_log(
    log_path: Path,
    argv: list[str],
    result: subprocess.CompletedProcess[str],
) -> None:
    """Write an export command log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        "\n".join(
            [
                f"argv: {' '.join(argv)}",
                f"returncode: {result.returncode}",
                "",
                "stdout:",
                result.stdout,
                "",
                "stderr:",
                result.stderr,
                "",
            ]
        ),
        encoding="utf-8",
    )


def _export_files(
    run_dir: Path,
    manifest: MigrationManifest,
    *,
    force: bool,
) -> int:
    """Export discovered TSM files to line protocol."""
    if not manifest.files:
        raise click.ClickException(
            "No discovered files found in the manifest. Run discover first."
        )

    exported_count = 0
    for record in manifest.files:
        export_lp_path = Path(record.export_lp_path)
        if (
            record.exported_at is not None
            and export_lp_path.exists()
            and not force
        ):
            continue

        extracted_tsm_path = (
            run_dir
            / "extracted-tsm"
            / record.shard_id
            / Path(record.archive_member_path).name
        )
        _extract_archive_member(
            Path(record.archive_path),
            record.archive_member_path,
            extracted_tsm_path,
        )

        export_lp_path.parent.mkdir(parents=True, exist_ok=True)
        argv = [
            "influx_inspect",
            "export",
            "-database",
            manifest.database,
            "-retention",
            manifest.retention,
            "-lponly",
            "-tsmfile",
            str(extracted_tsm_path),
            "-out",
            str(export_lp_path),
        ]
        result = _run_external_command(argv)
        log_path = (
            run_dir
            / "logs"
            / "export"
            / f"{record.shard_id}-{Path(record.archive_member_path).stem}.log"
        )
        _write_export_log(log_path, argv, result)
        record.extracted_tsm_path = str(extracted_tsm_path)
        record.export_log_path = str(log_path)

        if result.returncode != 0:
            record.last_error = (
                result.stderr.strip() or "Export command failed."
            )
            _save_manifest(run_dir, manifest)
            raise click.ClickException(
                f"Failed to export {record.archive_member_path}: "
                f"{record.last_error}"
            )

        if not export_lp_path.exists():
            record.last_error = (
                "Export completed without creating the LP file."
            )
            _save_manifest(run_dir, manifest)
            raise click.ClickException(record.last_error)

        record.exported_at = _utc_now()
        record.last_error = None
        exported_count += 1

    manifest.status = "exported"
    _save_manifest(run_dir, manifest)
    return exported_count


def _common_run_options[F: Callable[..., Any]](function: F) -> F:
    """Add shared migration-run options to a Click command."""
    function = click.option(
        "--work-dir",
        type=click.Path(file_okay=False, path_type=Path),
        required=True,
        help="Directory to store per-run manifests and migration artifacts.",
    )(function)
    function = click.option(
        "--shard",
        "shards",
        multiple=True,
        required=True,
        help="Shard ID to include. Repeat for multiple shards.",
    )(function)
    function = click.option("--retention", required=True)(function)
    function = click.option("--database", required=True)(function)
    return click.option(
        "--backup-dir",
        type=click.Path(exists=True, file_okay=False, path_type=Path),
        required=True,
    )(function)


@click.command("discover")
@_common_run_options
def discover(
    backup_dir: Path,
    database: str,
    retention: str,
    shards: tuple[str, ...],
    work_dir: Path,
) -> None:
    """Discover TSM files for a migration run."""
    normalized_shards = _stringify_shards(shards)
    run_dir = _run_dir(
        work_dir,
        backup_dir,
        database,
        retention,
        normalized_shards,
    )
    manifest = _load_manifest(
        run_dir,
        backup_dir,
        database,
        retention,
        normalized_shards,
    )
    discovered_count = _discover_files(run_dir, manifest, backup_dir)
    click.echo(
        "Discovered "
        f"{discovered_count} TSM file(s) in "
        f"{len(manifest.shards)} shard(s)."
    )


@click.command("export")
@_common_run_options
@click.option(
    "--force",
    is_flag=True,
    help="Re-export files already marked exported in the manifest.",
)
def export_command(
    backup_dir: Path,
    database: str,
    retention: str,
    shards: tuple[str, ...],
    work_dir: Path,
    *,
    force: bool,
) -> None:
    """Export discovered TSM files to line protocol."""
    normalized_shards = _stringify_shards(shards)
    run_dir = _run_dir(
        work_dir,
        backup_dir,
        database,
        retention,
        normalized_shards,
    )
    manifest = _load_manifest(
        run_dir,
        backup_dir,
        database,
        retention,
        normalized_shards,
    )
    if not manifest.files:
        _discover_files(run_dir, manifest, backup_dir)
    exported_count = _export_files(
        run_dir,
        manifest,
        force=force,
    )
    click.echo(f"Exported {exported_count} file(s).")


@click.group("migrate")
def migrate() -> None:
    """Migration workflow commands for InfluxDB backups."""


migrate.add_command(discover)
migrate.add_command(export_command)
