"""Discover Kafka topics and update a Telegraf input configuration."""

from __future__ import annotations

import os
import re
import tempfile
import tomllib
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from pathlib import Path

from .kafka import TopicProvider

__all__ = [
    "TopicConfigError",
    "TopicConfigUpdater",
    "UpdateResult",
    "load_prefixes",
    "load_template",
    "render_topic_config",
    "select_topics",
    "write_config",
]

_TOPIC_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
_TOPICS_PLACEHOLDER = "__DISCOVERED_TOPICS__"
_EMPTY_CONFIG = "# No Kafka topics currently match the configured prefixes.\n"


class TopicConfigError(Exception):
    """Raised when topic configuration cannot be generated or installed."""


@dataclass(frozen=True)
class UpdateResult:
    """Result of one topic configuration reconciliation."""

    changed: bool
    topics: tuple[str, ...]

    @property
    def topic_count(self) -> int:
        """Number of selected topics."""
        return len(self.topics)


def load_prefixes(path: Path, *, require_nonempty: bool) -> tuple[str, ...]:
    """Read and validate literal prefixes from a newline-delimited file."""
    try:
        prefixes = tuple(path.read_text(encoding="utf-8").splitlines())
    except OSError as exc:
        raise TopicConfigError(f"Cannot read prefix file {path}") from exc

    for prefix in prefixes:
        if not prefix or prefix != prefix.strip():
            raise TopicConfigError(
                f"Prefix file {path} contains an empty or padded prefix"
            )
    if require_nonempty and not prefixes:
        raise TopicConfigError(
            f"Include-prefix file {path} must contain at least one prefix"
        )
    return prefixes


def select_topics(
    topics: Collection[str],
    *,
    include_prefixes: Sequence[str],
    exclude_prefixes: Sequence[str],
) -> tuple[str, ...]:
    """Select sorted topics using literal include and exclude prefixes."""
    selected: set[str] = set()
    for topic in topics:
        if not _TOPIC_PATTERN.fullmatch(topic):
            raise TopicConfigError("Kafka returned an invalid topic name")
        if any(
            topic.startswith(prefix) for prefix in include_prefixes
        ) and not (
            any(topic.startswith(prefix) for prefix in exclude_prefixes)
        ):
            selected.add(topic)
    return tuple(sorted(selected))


def _topics_array(topics: Sequence[str]) -> str:
    """Render a Telegraf TOML string array for validated topic names."""
    return "[ " + ", ".join(f'"{topic}"' for topic in topics) + " ]"


def render_topic_config(template: str, topics: Sequence[str]) -> str:
    """Render and validate a complete Telegraf dynamic configuration."""
    if _TOPICS_PLACEHOLDER not in template:
        raise TopicConfigError(
            f"Telegraf input template is missing {_TOPICS_PLACEHOLDER}"
        )
    content = (
        template.replace(_TOPICS_PLACEHOLDER, _topics_array(topics))
        if topics
        else _EMPTY_CONFIG
    )
    try:
        tomllib.loads(content)
    except tomllib.TOMLDecodeError as exc:
        raise TopicConfigError(
            "Rendered Telegraf input configuration is invalid TOML"
        ) from exc
    return content


def load_template(path: Path) -> str:
    """Read and validate a Telegraf input template at startup."""
    try:
        template = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TopicConfigError(
            f"Cannot read Telegraf template {path}"
        ) from exc
    render_topic_config(template, ("validation-topic",))
    return template


def write_config(path: Path, content: str) -> bool:
    """Atomically install content, returning whether the file changed."""
    try:
        if path.exists() and path.read_text(encoding="utf-8") == content:
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as temporary:
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
            temporary_path.replace(path)
        finally:
            temporary_path.unlink(missing_ok=True)
    except OSError as exc:
        raise TopicConfigError(
            f"Cannot install Telegraf configuration {path}"
        ) from exc
    return True


class TopicConfigUpdater:
    """Reconcile Kafka metadata into a watched Telegraf config file."""

    def __init__(
        self,
        *,
        provider: TopicProvider,
        include_prefixes: Sequence[str],
        exclude_prefixes: Sequence[str],
        template: str,
        output_path: Path,
        ready_path: Path,
    ) -> None:
        self._provider = provider
        self._include_prefixes = tuple(include_prefixes)
        self._exclude_prefixes = tuple(exclude_prefixes)
        self._template = template
        self._output_path = output_path
        self._ready_path = ready_path

    def update(self, *, timeout: float) -> UpdateResult:
        """Perform one discovery and configuration update."""
        topics = select_topics(
            self._provider.list_topics(timeout=timeout),
            include_prefixes=self._include_prefixes,
            exclude_prefixes=self._exclude_prefixes,
        )
        content = render_topic_config(self._template, topics)
        changed = write_config(self._output_path, content)
        try:
            self._ready_path.parent.mkdir(parents=True, exist_ok=True)
            self._ready_path.touch()
        except OSError as exc:
            raise TopicConfigError(
                f"Cannot update readiness file {self._ready_path}"
            ) from exc
        return UpdateResult(changed=changed, topics=topics)
