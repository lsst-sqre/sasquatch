"""Command-line interface for managing Telegraf configuration."""

from __future__ import annotations

import os
import re
import signal
from datetime import timedelta
from pathlib import Path
from threading import Event
from typing import Protocol

import click
import structlog
from safir.logging import Profile, configure_logging
from structlog.stdlib import BoundLogger

from .kafka import KafkaTopicProvider, TopicDiscoveryError
from .topic_config import (
    TopicConfigError,
    TopicConfigUpdater,
    UpdateResult,
    load_prefixes,
    load_template,
)

_DURATION_PATTERN = re.compile(r"^([1-9][0-9]*)([smh])$")
_DURATION_FACTORS = {"s": 1, "m": 60, "h": 3600}


class _Updater(Protocol):
    """Update a Telegraf topic configuration."""

    def update(self, *, timeout: float) -> UpdateResult:
        """Perform one update."""


class _StopEvent(Protocol):
    """Control the topic discovery watch loop."""

    def is_set(self) -> bool:
        """Return whether shutdown was requested."""

    def wait(self, timeout: float | None = None) -> bool:
        """Wait for shutdown or a timeout."""


@click.group()
def telegraf() -> None:
    """Telegraf configuration tools."""


def _duration(
    _ctx: click.Context, _param: click.Parameter, value: str
) -> timedelta:
    """Parse a positive duration with an s, m, or h suffix."""
    match = _DURATION_PATTERN.fullmatch(value)
    if not match:
        raise click.BadParameter(
            "must be a positive integer followed by s, m, or h"
        )
    return timedelta(
        seconds=int(match.group(1)) * _DURATION_FACTORS[match.group(2)]
    )


def _run_updates(
    updater: _Updater,
    *,
    request_timeout: float,
    refresh_interval: timedelta,
    watch: bool,
    stop_event: _StopEvent,
    logger: BoundLogger,
) -> bool:
    """Run one update or watch until interrupted."""
    known_topics: frozenset[str] = frozenset()
    while not stop_event.is_set():
        try:
            result = updater.update(timeout=request_timeout)
            new_topics = tuple(
                topic for topic in result.topics if topic not in known_topics
            )
            for topic in new_topics:
                logger.info("telegraf_topic_discovered", topic=topic)
            if new_topics:
                logger.info(
                    "telegraf_topics_discovered", topics=list(result.topics)
                )
            known_topics = frozenset(result.topics)
            logger.info(
                "telegraf_topics_config_reconciled",
                changed=result.changed,
                topic_count=result.topic_count,
            )
            succeeded = True
        except (TopicConfigError, TopicDiscoveryError) as exc:
            logger.exception(
                "telegraf_topics_config_reconciliation_failed",
                error=str(exc),
            )
            succeeded = False

        if not watch:
            return succeeded
        stop_event.wait(refresh_interval.total_seconds())
    return True


@telegraf.command("update-topic-config")
@click.option("--bootstrap-server", required=True)
@click.option("--username", default="telegraf", show_default=True)
@click.option(
    "--include-prefixes-file",
    type=click.Path(
        exists=True, dir_okay=False, readable=True, path_type=Path
    ),
    required=True,
)
@click.option(
    "--exclude-prefixes-file",
    type=click.Path(
        exists=True, dir_okay=False, readable=True, path_type=Path
    ),
    required=True,
)
@click.option(
    "--input-template",
    type=click.Path(
        exists=True, dir_okay=False, readable=True, path_type=Path
    ),
    required=True,
)
@click.option(
    "--output-config",
    type=click.Path(dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--ready-file",
    type=click.Path(dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--request-timeout",
    default=15.0,
    show_default=True,
    type=click.FloatRange(min=0.0, min_open=True),
)
@click.option(
    "--refresh-interval",
    callback=_duration,
    default="30s",
    show_default=True,
)
@click.option("--watch", is_flag=True)
def update_topic_config(
    *,
    bootstrap_server: str,
    username: str,
    include_prefixes_file: Path,
    exclude_prefixes_file: Path,
    input_template: Path,
    output_config: Path,
    ready_file: Path,
    request_timeout: float,
    refresh_interval: timedelta,
    watch: bool,
) -> None:
    """Discover Kafka topics and update a Telegraf input configuration."""
    configure_logging(
        name="sasquatch", profile=Profile.production, add_timestamp=True
    )

    password = os.getenv("TELEGRAF_PASSWORD")
    if not password:
        raise click.ClickException("TELEGRAF_PASSWORD is not set")

    try:
        include_prefixes = load_prefixes(
            include_prefixes_file, require_nonempty=True
        )
        exclude_prefixes = load_prefixes(
            exclude_prefixes_file, require_nonempty=False
        )
        template = load_template(input_template)
        provider = KafkaTopicProvider(
            bootstrap_server=bootstrap_server,
            username=username,
            password=password,
        )
    except (TopicConfigError, TopicDiscoveryError) as exc:
        raise click.ClickException(str(exc)) from exc

    updater = TopicConfigUpdater(
        provider=provider,
        include_prefixes=include_prefixes,
        exclude_prefixes=exclude_prefixes,
        template=template,
        output_path=output_config,
        ready_path=ready_file,
    )
    stop_event = Event()

    def stop(_signum: int, _frame: object) -> None:
        stop_event.set()

    previous_sigterm = signal.signal(signal.SIGTERM, stop)
    previous_sigint = signal.signal(signal.SIGINT, stop)
    try:
        succeeded = _run_updates(
            updater,
            request_timeout=request_timeout,
            refresh_interval=refresh_interval,
            watch=watch,
            stop_event=stop_event,
            logger=structlog.get_logger("sasquatch.telegraf"),
        )
    finally:
        signal.signal(signal.SIGTERM, previous_sigterm)
        signal.signal(signal.SIGINT, previous_sigint)

    if not succeeded:
        raise click.ClickException("Kafka topic discovery failed")
