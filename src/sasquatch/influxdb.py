"""Commands for interacting with InfluxDB."""

import click

from .fields import drop_field, rename_field, show_fields
from .measurements import drop_measurement_command
from .tags import drop_tag, rename_tag, show_tags


@click.group()
def influxdb() -> None:
    """InfluxDB tools."""


influxdb.add_command(show_tags)
influxdb.add_command(show_fields)
influxdb.add_command(drop_tag)
influxdb.add_command(drop_field)
influxdb.add_command(rename_tag)
influxdb.add_command(rename_field)
influxdb.add_command(drop_measurement_command)
