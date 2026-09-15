"""Tests for Kafka topic metadata access."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from sasquatch.telegraf import kafka
from sasquatch.telegraf.kafka import KafkaTopicProvider, TopicDiscoveryError


class _FakeAdminClient:
    """Record Kafka client configuration and return configurable metadata."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.timeout: float | None = None
        self.error: Exception | None = None
        self.topics = {
            "lsst.prompt": SimpleNamespace(error=None),
            "lsst.prompt.foo": SimpleNamespace(error=None),
        }

    def list_topics(self, *, timeout: float) -> SimpleNamespace:
        """Return synthetic Kafka metadata."""
        self.timeout = timeout
        if self.error:
            raise self.error
        return SimpleNamespace(topics=self.topics)


def test_kafka_topic_provider_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The provider should use SCRAM and pass the metadata timeout."""
    client: _FakeAdminClient | None = None

    def make_client(config: dict[str, Any]) -> _FakeAdminClient:
        nonlocal client
        client = _FakeAdminClient(config)
        return client

    monkeypatch.setattr(kafka, "AdminClient", make_client)
    provider = KafkaTopicProvider(
        bootstrap_server="kafka:9092",
        username="telegraf",
        password="secret",
    )

    assert set(provider.list_topics(timeout=12.5)) == {
        "lsst.prompt",
        "lsst.prompt.foo",
    }
    assert client is not None
    assert client.timeout == 12.5
    assert client.config == {
        "bootstrap.servers": "kafka:9092",
        "security.protocol": "SASL_PLAINTEXT",
        "sasl.mechanism": "SCRAM-SHA-512",
        "sasl.username": "telegraf",
        "sasl.password": "secret",
    }


@pytest.mark.parametrize("metadata_error", [False, True])
def test_kafka_topic_provider_errors(
    monkeypatch: pytest.MonkeyPatch, *, metadata_error: bool
) -> None:
    """Kafka request and per-topic errors should fail discovery."""
    client = _FakeAdminClient({})
    if metadata_error:
        client.topics["broken"] = SimpleNamespace(error=RuntimeError())
    else:
        client.error = RuntimeError("password=do-not-log")
    monkeypatch.setattr(kafka, "AdminClient", lambda _config: client)
    provider = KafkaTopicProvider(
        bootstrap_server="kafka:9092",
        username="telegraf",
        password="secret",
    )

    with pytest.raises(TopicDiscoveryError) as excinfo:
        provider.list_topics(timeout=15)

    assert "do-not-log" not in str(excinfo.value)


def test_kafka_topic_provider_hides_initialization_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Client initialization errors should not expose configuration."""

    def fail(_config: dict[str, Any]) -> None:
        raise ValueError("secret-value")

    monkeypatch.setattr(kafka, "AdminClient", fail)

    with pytest.raises(TopicDiscoveryError) as excinfo:
        KafkaTopicProvider(
            bootstrap_server="kafka:9092",
            username="telegraf",
            password="secret-value",
        )

    assert "secret-value" not in str(excinfo.value)
