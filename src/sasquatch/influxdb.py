"""Commands for interacting with InfluxDB."""

import click

from .fields import drop_field, show_fields
from .tags import drop_tag, show_tags


@click.group()
def influxdb() -> None:
    """InfluxDB tools."""


influxdb.add_command(show_tags)
influxdb.add_command(show_fields)
influxdb.add_command(drop_tag)
influxdb.add_command(drop_field)
