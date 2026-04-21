"""Commands for interacting with InfluxDB."""

import click

from .tags import list_tags


@click.group()
def influxdb() -> None:
    """InfluxDB tools."""


influxdb.add_command(list_tags)
