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
import yaml

from .fields import drop_measurement_field_key, rename_measurement_field_key
from .measurements import drop_measurement, rename_measurement
from .tag_to_field import TagToFieldConflictError, convert_tag_to_field
from .tags import drop_measurement_tag_key, rename_measurement_tag_key


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
    import_log_path: str | None = None
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
    transform_plan_path: str | None = None
    transform_plan_hash: str | None = None
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
            transform_plan_path=data.get("transform_plan_path"),
            transform_plan_hash=data.get("transform_plan_hash"),
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


def _write_import_log(
    log_path: Path,
    argv: list[str],
    result: subprocess.CompletedProcess[str],
) -> None:
    """Write an import command log."""
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


def _context_header_line(prefix: str, value: str) -> str:
    """Build one DML context header line."""
    return f"# {prefix}: {value}\n"


def _find_import_context_indexes(
    lines: list[str],
) -> tuple[int | None, int | None, int | None, int | None]:
    """Locate DML/context headers and the first data line."""
    dml_index: int | None = None
    database_index: int | None = None
    retention_index: int | None = None
    first_data_index: int | None = None

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            if stripped == "# DML":
                dml_index = index
            elif stripped.startswith("# CONTEXT-DATABASE:"):
                database_index = index
            elif stripped.startswith("# CONTEXT-RETENTION-POLICY:"):
                retention_index = index
            continue
        if stripped:
            first_data_index = index
            break

    return dml_index, database_index, retention_index, first_data_index


def _replace_context_header(
    lines: list[str],
    index: int | None,
    expected: str,
) -> bool:
    """Replace one existing header line if it differs."""
    if index is None or lines[index] == expected:
        return False
    lines[index] = expected
    return True


def _insert_missing_context_headers(
    lines: list[str],
    *,
    dml_index: int | None,
    database_index: int | None,
    retention_index: int | None,
    first_data_index: int | None,
    database: str,
    retention: str,
) -> bool:
    """Insert any missing DML/context headers before the first data line."""
    if (
        dml_index is not None
        and database_index is not None
        and retention_index is not None
    ):
        return False

    insert_at = (
        first_data_index if first_data_index is not None else len(lines)
    )
    header_lines: list[str] = []
    if dml_index is None:
        header_lines.append("# DML\n")
    if database_index is None:
        header_lines.append(_context_header_line("CONTEXT-DATABASE", database))
    if retention_index is None:
        header_lines.append(
            _context_header_line(
                "CONTEXT-RETENTION-POLICY",
                retention,
            )
        )
    lines[insert_at:insert_at] = header_lines
    return True


def _required_string(operation: dict[str, Any], key: str) -> str:
    """Return a required string field from a transform operation."""
    value = operation.get(key)
    if not isinstance(value, str) or not value:
        raise click.ClickException(
            f"Transform operation {operation.get('op')!r} requires {key!r}."
        )
    return value


def _operation_keys(op_name: str) -> list[str]:
    """Return required keys for one transform operation."""
    required_keys = {
        "drop-tag": ["tag"],
        "rename-tag": ["from", "to"],
        "drop-field": ["field"],
        "rename-field": ["from", "to"],
        "drop-measurement": ["measurement"],
        "rename-measurement": ["from", "to"],
        "convert-tag-to-field": ["tag"],
    }
    try:
        return required_keys[op_name]
    except KeyError as exc:
        raise click.ClickException(
            f"Unknown transform operation {op_name!r}."
        ) from exc


def _normalize_operation(operation: dict[str, Any]) -> dict[str, Any]:
    """Normalize one transform operation for execution and hashing."""
    op_name = operation.get("op")
    if not isinstance(op_name, str):
        raise click.ClickException(
            "Each transform entry must define string 'op'."
        )

    measurement = operation.get("measurement")
    if measurement is not None and not isinstance(measurement, str):
        raise click.ClickException("Optional 'measurement' must be a string.")

    normalized: dict[str, Any] = {"op": op_name}
    if measurement is not None:
        normalized["measurement"] = measurement

    for key in _operation_keys(op_name):
        normalized[key] = _required_string(operation, key)

    return normalized


def _load_transform_plan(plan_path: Path) -> tuple[list[dict[str, Any]], str]:
    """Load and normalize a YAML transform plan."""
    if plan_path.suffix.lower() not in {".yaml", ".yml"}:
        raise click.UsageError(
            "Transform plan must use a .yaml or .yml extension."
        )

    try:
        raw_plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise click.ClickException(
            f"Failed to parse YAML transform plan {plan_path}."
        ) from exc

    if not isinstance(raw_plan, list):
        raise click.ClickException(
            "Transform plan must be a list of operations."
        )

    normalized: list[dict[str, Any]] = []
    for operation in raw_plan:
        if not isinstance(operation, dict):
            raise click.ClickException(
                "Each transform plan entry must be an object."
            )
        normalized.append(_normalize_operation(operation))

    plan_hash = hashlib.sha256(
        json.dumps(normalized, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return normalized, plan_hash


def _apply_operation(file_path: Path, operation: dict[str, Any]) -> None:
    """Apply one normalized transform operation to an LP file."""
    op_name = operation["op"]
    measurement = operation.get("measurement")

    try:
        if op_name == "drop-tag":
            drop_measurement_tag_key(
                file_path,
                operation["tag"],
                measurement=measurement,
            )
        elif op_name == "rename-tag":
            rename_measurement_tag_key(
                file_path,
                operation["from"],
                operation["to"],
                measurement=measurement,
            )
        elif op_name == "drop-field":
            drop_measurement_field_key(
                file_path,
                operation["field"],
                measurement=measurement,
            )
        elif op_name == "rename-field":
            rename_measurement_field_key(
                file_path,
                operation["from"],
                operation["to"],
                measurement=measurement,
            )
        elif op_name == "drop-measurement":
            drop_measurement(file_path, operation["measurement"])
        elif op_name == "rename-measurement":
            rename_measurement(
                file_path,
                operation["from"],
                operation["to"],
            )
        elif op_name == "convert-tag-to-field":
            convert_tag_to_field(
                file_path,
                operation["tag"],
                measurement=measurement,
            )
        else:  # pragma: no cover
            raise click.ClickException(
                f"Unsupported transform operation {op_name!r}."
            )
    except TagToFieldConflictError as exc:
        raise click.ClickException(str(exc)) from exc


def _transform_files(
    run_dir: Path,
    manifest: MigrationManifest,
    plan_path: Path,
    *,
    force: bool,
) -> int:
    """Apply a transform plan to exported line protocol files."""
    if not manifest.files:
        raise click.ClickException(
            "No discovered files found in the manifest. Run export first."
        )

    normalized_plan, plan_hash = _load_transform_plan(plan_path)
    if (
        manifest.transform_plan_hash is not None
        and manifest.transform_plan_hash != plan_hash
        and any(record.transformed_at is not None for record in manifest.files)
        and not force
    ):
        raise click.ClickException(
            "Transform plan changed for an existing run. "
            "Use --force to reapply it."
        )

    transformed_count = 0
    for record in manifest.files:
        export_lp_path = Path(record.export_lp_path)
        if not export_lp_path.exists():
            raise click.ClickException(
                f"Exported file {export_lp_path} is missing. Run export first."
            )
        if record.transformed_at is not None and not force:
            continue

        try:
            for operation in normalized_plan:
                _apply_operation(export_lp_path, operation)
        except click.ClickException as exc:
            record.last_error = str(exc)
            _save_manifest(run_dir, manifest)
            raise

        record.transformed_at = _utc_now()
        record.last_error = None
        transformed_count += 1

    manifest.transform_plan_path = str(plan_path)
    manifest.transform_plan_hash = plan_hash
    manifest.status = "transformed"
    _save_manifest(run_dir, manifest)
    return transformed_count


def _rewrite_import_context(
    file_path: Path,
    *,
    database: str,
    retention: str,
) -> str | None:
    """Rewrite or add import context headers in place."""
    lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
    (
        dml_index,
        database_index,
        retention_index,
        first_data_index,
    ) = _find_import_context_indexes(lines)

    modified = _replace_context_header(
        lines,
        database_index,
        _context_header_line("CONTEXT-DATABASE", database),
    )
    modified = (
        _replace_context_header(
            lines,
            retention_index,
            _context_header_line("CONTEXT-RETENTION-POLICY", retention),
        )
        or modified
    )
    added = _insert_missing_context_headers(
        lines,
        dml_index=dml_index,
        database_index=database_index,
        retention_index=retention_index,
        first_data_index=first_data_index,
        database=database,
        retention=retention,
    )

    if added or modified:
        file_path.write_text("".join(lines), encoding="utf-8")

    if added:
        return "added"
    if modified:
        return "modified"
    return None


def _build_import_argv(
    *,
    file_path: Path,
    host: str,
    port: int,
    username: str | None,
    password: str | None,
    precision: str,
    pps: int,
    compressed: bool,
    ssl: bool,
    unsafe_ssl: bool,
) -> list[str]:
    """Build the influx CLI argv for one file import."""
    argv = [
        "influx",
        "-host",
        host,
        "-port",
        str(port),
        "-import",
        "-path",
        str(file_path),
        "-precision",
        precision,
    ]
    if username is not None:
        argv.extend(["-username", username])
    if password is not None:
        argv.extend(["-password", password])
    if pps:
        argv.extend(["-pps", str(pps)])
    if compressed:
        argv.append("-compressed")
    if ssl:
        argv.append("-ssl")
    if unsafe_ssl:
        argv.append("-unsafeSsl")
    return argv


def _emit_import_context_message(
    status: str | None,
    *,
    file_path: Path,
    database: str,
    retention: str,
) -> None:
    """Print a per-file header update message when needed."""
    if status == "added":
        click.echo(
            f"Added import headers to {file_path} for "
            f"database={database}, retention={retention}."
        )
    elif status == "modified":
        click.echo(
            f"Updated import headers in {file_path} to "
            f"database={database}, retention={retention}."
        )


def _import_log_path(run_dir: Path, record: MigrationFileRecord) -> Path:
    """Return the import log path for one file record."""
    file_stem = Path(record.export_lp_path).stem
    return run_dir / "logs" / "import" / f"{record.shard_id}-{file_stem}.log"


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


def _import_files(
    run_dir: Path,
    manifest: MigrationManifest,
    *,
    target_database: str,
    target_retention: str,
    host: str,
    port: int,
    username: str | None,
    password: str | None,
    precision: str,
    pps: int,
    compressed: bool,
    ssl: bool,
    unsafe_ssl: bool,
    force: bool,
) -> int:
    """Import transformed line protocol files."""
    if not manifest.files:
        raise click.ClickException(
            "No discovered files found in the manifest. Run transform first."
        )

    imported_count = 0
    for record in manifest.files:
        file_path = Path(record.export_lp_path)
        if not file_path.exists():
            raise click.ClickException(
                f"Line protocol file {file_path} is missing."
            )
        if record.transformed_at is None:
            raise click.ClickException(
                f"File {file_path} has not been transformed. "
                "Run transform first."
            )
        if record.imported_at is not None and not force:
            continue

        rewrite_status = _rewrite_import_context(
            file_path,
            database=target_database,
            retention=target_retention,
        )
        _emit_import_context_message(
            rewrite_status,
            file_path=file_path,
            database=target_database,
            retention=target_retention,
        )
        argv = _build_import_argv(
            file_path=file_path,
            host=host,
            port=port,
            username=username,
            password=password,
            precision=precision,
            pps=pps,
            compressed=compressed,
            ssl=ssl,
            unsafe_ssl=unsafe_ssl,
        )

        result = _run_external_command(argv)
        log_path = _import_log_path(run_dir, record)
        _write_import_log(log_path, argv, result)
        record.import_log_path = str(log_path)

        if result.returncode != 0:
            record.last_error = (
                result.stderr.strip() or "Import command failed."
            )
            _save_manifest(run_dir, manifest)
            raise click.ClickException(
                f"Failed to import {file_path}: {record.last_error}"
            )

        record.imported_at = _utc_now()
        record.last_error = None
        imported_count += 1

    manifest.status = "imported"
    _save_manifest(run_dir, manifest)
    return imported_count


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


@click.command("transform")
@_common_run_options
@click.option(
    "--plan",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="YAML file describing ordered transform operations.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Reapply the transform plan to files already marked transformed.",
)
def transform_command(
    backup_dir: Path,
    database: str,
    retention: str,
    shards: tuple[str, ...],
    work_dir: Path,
    plan: Path,
    *,
    force: bool,
) -> None:
    """Transform exported line protocol files in place."""
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
    transformed_count = _transform_files(
        run_dir,
        manifest,
        plan,
        force=force,
    )
    click.echo(f"Transformed {transformed_count} file(s).")


@click.command("import")
@_common_run_options
@click.option("--host", required=True, help="InfluxDB host name.")
@click.option("--port", type=int, default=8086, show_default=True)
@click.option("--username", default=None, help="InfluxDB username.")
@click.option("--password", default=None, help="InfluxDB password.")
@click.option(
    "--target-database",
    default=None,
    help=(
        "Destination database for the import. Defaults to the source "
        "database recorded in the manifest."
    ),
)
@click.option(
    "--target-retention",
    default=None,
    help=(
        "Destination retention policy for the import. Defaults to the "
        "source retention recorded in the manifest."
    ),
)
@click.option(
    "--precision",
    default="ns",
    show_default=True,
    type=click.Choice(["h", "m", "s", "ms", "u", "ns"]),
)
@click.option("--pps", type=int, default=0, show_default=True)
@click.option("--compressed", is_flag=True)
@click.option("--ssl", is_flag=True, help="Use HTTPS for the import request.")
@click.option(
    "--unsafe-ssl",
    is_flag=True,
    help="Disable SSL certificate verification.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Re-import files already marked imported in the manifest.",
)
def import_command(
    backup_dir: Path,
    database: str,
    retention: str,
    shards: tuple[str, ...],
    work_dir: Path,
    host: str,
    port: int,
    username: str | None,
    password: str | None,
    target_database: str | None,
    target_retention: str | None,
    precision: str,
    pps: int,
    *,
    compressed: bool,
    ssl: bool,
    unsafe_ssl: bool,
    force: bool,
) -> None:
    """Import transformed line protocol files into InfluxDB."""
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
    resolved_target_database = target_database or manifest.database
    resolved_target_retention = target_retention or manifest.retention
    imported_count = _import_files(
        run_dir,
        manifest,
        target_database=resolved_target_database,
        target_retention=resolved_target_retention,
        host=host,
        port=port,
        username=username,
        password=password,
        precision=precision,
        pps=pps,
        compressed=compressed,
        ssl=ssl,
        unsafe_ssl=unsafe_ssl,
        force=force,
    )
    click.echo(f"Imported {imported_count} file(s).")


@click.group("migrate")
def migrate() -> None:
    """Migration workflow commands for InfluxDB backups."""


migrate.add_command(discover)
migrate.add_command(export_command)
migrate.add_command(transform_command)
migrate.add_command(import_command)
