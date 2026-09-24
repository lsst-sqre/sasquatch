"""Exceptions in the Sasquatch app."""

__all__ = ["RetentionPolicyNotFoundError"]

from typing import final

from click import ClickException


@final
class RetentionPolicyNotFoundError(ClickException):
    """Thrown when a retention policy is not found in an InfluxDB db."""

    exit_code = 1
