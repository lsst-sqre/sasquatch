"""Tests for dynamic Telegraf topic configuration."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from sasquatch.telegraf.kafka import TopicDiscoveryError
from sasquatch.telegraf.topic_config import (
    TopicConfigError,
    TopicConfigUpdater,
    load_prefixes,
    load_template,
    render_topic_config,
    select_topics,
    write_config,
)


class _TopicProvider:
    """Return configured topics or a configured failure."""

    def __init__(self, topics: tuple[str, ...]) -> None:
        self.topics = topics
        self.error: TopicDiscoveryError | None = None
        self.timeout: float | None = None

    def list_topics(self, *, timeout: float) -> tuple[str, ...]:
        """Return synthetic topics."""
        self.timeout = timeout
        if self.error:
            raise self.error
        return self.topics


def test_load_prefixes(tmp_path: Path) -> None:
    """Prefix files should preserve literal prefix values."""
    include = tmp_path / "include.txt"
    include.write_text("lsst.prompt\nother+\n", encoding="utf-8")
    exclude = tmp_path / "exclude.txt"
    exclude.write_text("", encoding="utf-8")

    assert load_prefixes(include, require_nonempty=True) == (
        "lsst.prompt",
        "other+",
    )
    assert load_prefixes(exclude, require_nonempty=False) == ()


@pytest.mark.parametrize(
    "content", ["", "lsst.prompt\n\nother\n", " padded\n"]
)
def test_load_prefixes_rejects_invalid_input(
    tmp_path: Path, content: str
) -> None:
    """Required, blank, and padded prefix entries should be rejected."""
    path = tmp_path / "prefixes.txt"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(TopicConfigError):
        load_prefixes(path, require_nonempty=True)


def test_select_topics() -> None:
    """Selection should use literal OR prefixes with exclusion precedence."""
    topics = (
        "lsst.prompt.foo",
        "lsst.prompt.next-visitFoo",
        "unrelated",
        "lsst.prompt",
        "lsstXprompt",
        "lsst.prompted",
        "other",
        "lsst.prompt.foo",
    )

    assert select_topics(
        topics,
        include_prefixes=("lsst.prompt", "other+"),
        exclude_prefixes=("lsst.prompt.next-visit",),
    ) == ("lsst.prompt", "lsst.prompt.foo", "lsst.prompted")


def test_select_topics_rejects_invalid_kafka_output() -> None:
    """An invalid topic name should invalidate the complete result."""
    with pytest.raises(TopicConfigError, match="invalid topic"):
        select_topics(
            ("lsst.prompt", "invalid/topic"),
            include_prefixes=("lsst.prompt",),
            exclude_prefixes=(),
        )


def test_render_topic_config_replaces_all_inputs() -> None:
    """Normal and repair inputs should receive the same topic list."""
    template = (
        "[[inputs.kafka_consumer]]\n"
        "topics = __DISCOVERED_TOPICS__\n"
        "[[inputs.kafka_consumer]]\n"
        "topics = __DISCOVERED_TOPICS__\n"
    )

    content = render_topic_config(template, ("lsst.prompt", "lsst.prompt.foo"))

    parsed = tomllib.loads(content)
    assert parsed["inputs"]["kafka_consumer"][0]["topics"] == [
        "lsst.prompt",
        "lsst.prompt.foo",
    ]
    assert parsed["inputs"]["kafka_consumer"][1]["topics"] == [
        "lsst.prompt",
        "lsst.prompt.foo",
    ]


def test_render_topic_config_with_no_topics() -> None:
    """No selected topics should produce valid comment-only TOML."""
    content = render_topic_config(
        "[[inputs.kafka_consumer]]\ntopics = __DISCOVERED_TOPICS__\n", ()
    )

    assert content.startswith("# No Kafka topics")
    assert tomllib.loads(content) == {}


@pytest.mark.parametrize(
    "template",
    [
        "[[inputs.kafka_consumer]]\ntopics = []\n",
        "[[inputs.kafka_consumer]\ntopics = __DISCOVERED_TOPICS__\n",
    ],
)
def test_load_template_rejects_invalid_templates(
    tmp_path: Path, template: str
) -> None:
    """Templates must contain the marker and render as valid TOML."""
    path = tmp_path / "template.conf"
    path.write_text(template, encoding="utf-8")

    with pytest.raises(TopicConfigError):
        load_template(path)


def test_write_config_is_atomic_and_suppresses_unchanged_writes(
    tmp_path: Path,
) -> None:
    """Unchanged output should retain the installed file."""
    output = tmp_path / "dynamic" / "kafka.conf"

    assert write_config(output, "first\n")
    inode = output.stat().st_ino
    assert not write_config(output, "first\n")
    assert output.stat().st_ino == inode
    assert write_config(output, "second\n")
    assert output.read_text(encoding="utf-8") == "second\n"


def test_updater_retains_last_good_configuration(tmp_path: Path) -> None:
    """Discovery failures must not alter output or readiness."""
    provider = _TopicProvider(("lsst.prompt.foo",))
    output = tmp_path / "dynamic" / "kafka.conf"
    ready = tmp_path / "run" / "ready"
    updater = TopicConfigUpdater(
        provider=provider,
        include_prefixes=("lsst.prompt",),
        exclude_prefixes=(),
        template=(
            "[[inputs.kafka_consumer]]\ntopics = __DISCOVERED_TOPICS__\n"
        ),
        output_path=output,
        ready_path=ready,
    )

    result = updater.update(timeout=11)
    expected = output.read_text(encoding="utf-8")
    assert result.changed
    assert result.topic_count == 1
    assert provider.timeout == 11
    assert ready.is_file()

    provider.error = TopicDiscoveryError("metadata unavailable")
    with pytest.raises(TopicDiscoveryError):
        updater.update(timeout=11)
    assert output.read_text(encoding="utf-8") == expected
    assert ready.is_file()


def test_updater_marks_successful_empty_result_ready(tmp_path: Path) -> None:
    """An empty selected set is successful and should mark readiness."""
    provider = _TopicProvider(("unrelated",))
    output = tmp_path / "dynamic" / "kafka.conf"
    ready = tmp_path / "run" / "ready"
    updater = TopicConfigUpdater(
        provider=provider,
        include_prefixes=("lsst.prompt",),
        exclude_prefixes=(),
        template=(
            "[[inputs.kafka_consumer]]\ntopics = __DISCOVERED_TOPICS__\n"
        ),
        output_path=output,
        ready_path=ready,
    )

    result = updater.update(timeout=15)

    assert result.topic_count == 0
    assert output.read_text(encoding="utf-8").startswith("# No Kafka topics")
    assert ready.is_file()
