"""Kafka topic metadata access for Telegraf configuration."""

from __future__ import annotations

from collections.abc import Collection
from typing import Protocol

from confluent_kafka.admin import AdminClient

__all__ = ["KafkaTopicProvider", "TopicDiscoveryError", "TopicProvider"]


class TopicDiscoveryError(Exception):
    """Raised when Kafka topic metadata cannot be discovered."""


class TopicProvider(Protocol):
    """Provide the topic names visible to a Kafka client."""

    def list_topics(self, *, timeout: float) -> Collection[str]:
        """Return all visible Kafka topic names."""


class KafkaTopicProvider:
    """Retrieve topic names with the Confluent Kafka admin client."""

    def __init__(
        self,
        *,
        bootstrap_server: str,
        username: str,
        password: str,
    ) -> None:
        try:
            self._client = AdminClient(
                {
                    "bootstrap.servers": bootstrap_server,
                    "security.protocol": "SASL_PLAINTEXT",
                    "sasl.mechanism": "SCRAM-SHA-512",
                    "sasl.username": username,
                    "sasl.password": password,
                }
            )
        except Exception as exc:
            raise TopicDiscoveryError(
                "Kafka client initialization failed"
            ) from exc

    def list_topics(self, *, timeout: float) -> Collection[str]:
        """Return Kafka topic names from cluster metadata."""
        try:
            metadata = self._client.list_topics(timeout=timeout)
        except Exception as exc:
            raise TopicDiscoveryError(
                "Kafka topic metadata request failed"
            ) from exc

        if any(topic.error is not None for topic in metadata.topics.values()):
            raise TopicDiscoveryError("Kafka returned topic metadata errors")
        return tuple(metadata.topics)
