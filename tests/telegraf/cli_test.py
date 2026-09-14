"""Tests for the Telegraf topic configuration CLI."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import structlog
from click.testing import CliRunner
from structlog.testing import capture_logs

from sasquatch.cli import main
from sasquatch.telegraf import cli
from sasquatch.telegraf.kafka import TopicDiscoveryError
from sasquatch.telegraf.topic_config import UpdateResult


class _Provider:
    """Return synthetic Kafka topics."""

    def list_topics(self, *, timeout: float) -> tuple[str, ...]:
        return ("lsst.prompt.foo", "unrelated")


def _arguments(tmp_path: Path) -> tuple[list[str], Path, Path]:
    """Create CLI input files and return common arguments."""
    include = tmp_path / "include.txt"
    include.write_text("lsst.prompt\n", encoding="utf-8")
    exclude = tmp_path / "exclude.txt"
    exclude.write_text("", encoding="utf-8")
    template = tmp_path / "template.conf"
    template.write_text(
        "[[inputs.kafka_consumer]]\ntopics = __DISCOVERED_TOPICS__\n",
        encoding="utf-8",
    )
    output = tmp_path / "dynamic" / "kafka.conf"
    ready = tmp_path / "run" / "ready"
    arguments = [
        "telegraf",
        "update-topic-config",
        "--bootstrap-server",
        "kafka:9092",
        "--include-prefixes-file",
        str(include),
        "--exclude-prefixes-file",
        str(exclude),
        "--input-template",
        str(template),
        "--output-config",
        str(output),
        "--ready-file",
        str(ready),
    ]
    return arguments, output, ready


def test_update_topic_config_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The one-shot command should discover and write topics."""
    arguments, output, ready = _arguments(tmp_path)
    captured: dict[str, str] = {}

    def make_provider(
        *, bootstrap_server: str, username: str, password: str
    ) -> _Provider:
        captured.update(
            bootstrap_server=bootstrap_server,
            username=username,
            password=password,
        )
        return _Provider()

    monkeypatch.setattr(cli, "KafkaTopicProvider", make_provider)
    runner = CliRunner()
    result = runner.invoke(
        main, arguments, env={"TELEGRAF_PASSWORD": "secret-value"}
    )

    assert result.exit_code == 0, result.output
    assert captured == {
        "bootstrap_server": "kafka:9092",
        "username": "telegraf",
        "password": "secret-value",
    }
    assert '"lsst.prompt.foo"' in output.read_text(encoding="utf-8")
    assert ready.is_file()
    assert "secret-value" not in result.output
    logs = [json.loads(line) for line in result.output.splitlines()]
    assert [log["event"] for log in logs] == [
        "telegraf_topic_discovered",
        "telegraf_topics_discovered",
        "telegraf_topics_config_reconciled",
    ]
    assert all(log["logger"] == "sasquatch.telegraf" for log in logs)
    assert all(log["severity"] == "info" for log in logs)
    assert all(datetime.fromisoformat(log["timestamp"]) for log in logs)


def test_update_topic_config_requires_password(tmp_path: Path) -> None:
    """The command should fail before connecting without a password."""
    arguments, output, ready = _arguments(tmp_path)

    result = CliRunner().invoke(main, arguments, env={})

    assert result.exit_code == 1
    assert "TELEGRAF_PASSWORD is not set" in result.output
    assert not output.exists()
    assert not ready.exists()


def test_update_topic_config_failure_stays_unready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An initial Kafka failure should not install config or readiness."""
    arguments, output, ready = _arguments(tmp_path)

    class FailingProvider:
        def list_topics(self, *, timeout: float) -> tuple[str, ...]:
            raise TopicDiscoveryError("metadata unavailable")

    monkeypatch.setattr(
        cli, "KafkaTopicProvider", lambda **_kwargs: FailingProvider()
    )
    result = CliRunner().invoke(
        main, arguments, env={"TELEGRAF_PASSWORD": "secret-value"}
    )

    assert result.exit_code == 1
    assert not output.exists()
    assert not ready.exists()
    assert "secret-value" not in result.output


def test_update_topic_config_rejects_invalid_interval(
    tmp_path: Path,
) -> None:
    """Refresh intervals should use the documented duration syntax."""
    arguments, _, _ = _arguments(tmp_path)
    arguments.extend(["--refresh-interval", "immediately"])

    result = CliRunner().invoke(
        main, arguments, env={"TELEGRAF_PASSWORD": "secret"}
    )

    assert result.exit_code == 2
    assert "positive integer followed by s, m, or h" in result.output


class _FakeUpdater:
    """Fail once and then succeed."""

    def __init__(self) -> None:
        self.calls = 0

    def update(self, *, timeout: float) -> UpdateResult:
        self.calls += 1
        if self.calls == 1:
            raise TopicDiscoveryError("metadata unavailable")
        return UpdateResult(
            changed=True, topics=("lsst.prompt.a", "lsst.prompt.b")
        )


class _FakeStopEvent:
    """Stop a watch loop after a configured number of waits."""

    def __init__(self, *, stop_after: int = 2) -> None:
        self.stop_after = stop_after
        self.waits: list[float | None] = []

    def is_set(self) -> bool:
        return len(self.waits) >= self.stop_after

    def wait(self, timeout: float | None = None) -> bool:
        self.waits.append(timeout)
        return self.is_set()


def test_watch_retries_transient_failures() -> None:
    """Watch mode should retry failures and stop successfully."""
    updater = _FakeUpdater()
    stop_event = _FakeStopEvent()

    succeeded = cli._run_updates(
        updater,
        request_timeout=15,
        refresh_interval=timedelta(seconds=30),
        watch=True,
        stop_event=stop_event,
        logger=structlog.get_logger("test"),
    )

    assert succeeded
    assert updater.calls == 2
    assert stop_event.waits == [30, 30]


class _TopicSequenceUpdater:
    """Return a sequence of successful topic discovery results."""

    def __init__(self) -> None:
        self._topics = iter(
            (
                ("lsst.prompt.a", "lsst.prompt.b"),
                ("lsst.prompt.a", "lsst.prompt.b"),
                ("lsst.prompt.b",),
                ("lsst.prompt.a", "lsst.prompt.b", "lsst.prompt.c"),
            )
        )

    def update(self, *, timeout: float) -> UpdateResult:
        return UpdateResult(changed=True, topics=next(self._topics))


def test_watch_logs_new_and_all_discovered_topics() -> None:
    """New topics should be logged before the complete current topic list."""
    updater = _TopicSequenceUpdater()
    stop_event = _FakeStopEvent(stop_after=4)

    with capture_logs() as logs:
        succeeded = cli._run_updates(
            updater,
            request_timeout=15,
            refresh_interval=timedelta(seconds=30),
            watch=True,
            stop_event=stop_event,
            logger=structlog.get_logger("test"),
        )

    assert succeeded
    discovery_logs = [
        log
        for log in logs
        if log["event"]
        in {"telegraf_topic_discovered", "telegraf_topics_discovered"}
    ]
    assert discovery_logs == [
        {
            "event": "telegraf_topic_discovered",
            "log_level": "info",
            "topic": "lsst.prompt.a",
        },
        {
            "event": "telegraf_topic_discovered",
            "log_level": "info",
            "topic": "lsst.prompt.b",
        },
        {
            "event": "telegraf_topics_discovered",
            "log_level": "info",
            "topics": ["lsst.prompt.a", "lsst.prompt.b"],
        },
        {
            "event": "telegraf_topic_discovered",
            "log_level": "info",
            "topic": "lsst.prompt.a",
        },
        {
            "event": "telegraf_topic_discovered",
            "log_level": "info",
            "topic": "lsst.prompt.c",
        },
        {
            "event": "telegraf_topics_discovered",
            "log_level": "info",
            "topics": [
                "lsst.prompt.a",
                "lsst.prompt.b",
                "lsst.prompt.c",
            ],
        },
    ]
