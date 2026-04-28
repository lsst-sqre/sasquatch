"""Commands for interacting with InfluxDB."""

import click

from .fields import drop_field, rename_field, show_fields
from .measurements import (
    drop_measurement_command,
    rename_measurement_command,
    show_measurements,
)
from .migration import migrate
from .tag_to_field import convert_tag_to_field_command
from .tags import drop_tag, rename_tag, show_tags


@click.group()
def influxdb() -> None:
    """InfluxDB tools."""


@click.group("line-protocol")
def line_protocol() -> None:
    """Line protocol inspection and rewrite tools."""


line_protocol.add_command(show_tags)
line_protocol.add_command(show_fields)
line_protocol.add_command(drop_tag)
line_protocol.add_command(drop_field)
line_protocol.add_command(rename_tag)
line_protocol.add_command(rename_field)
line_protocol.add_command(show_measurements)
line_protocol.add_command(drop_measurement_command)
line_protocol.add_command(rename_measurement_command)
line_protocol.add_command(convert_tag_to_field_command)


influxdb.add_command(line_protocol)
influxdb.add_command(migrate)
