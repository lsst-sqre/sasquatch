"""Pytest configuration and fixtures."""

from collections.abc import Generator

import pytest

from .constants import INFLUXDB_DATABASE
from .support.influxdb_testcontainer import (
    InfluxDBConnection,
    InfluxDBTestcontainer,
)


@pytest.fixture(scope="session")
def influxdb_container() -> Generator[InfluxDBTestcontainer]:
    """InfluxDB v1 in a container, scoped to the session."""
    with InfluxDBTestcontainer() as container:
        yield container


@pytest.fixture
def influxdb_connection(
    influxdb_container: InfluxDBTestcontainer,
) -> Generator[InfluxDBConnection]:
    """Give an InfluxDB client and info pointed at clean database instance."""
    influxdb_container.reset()
    client = influxdb_container.make_client(database=INFLUXDB_DATABASE)
    client.create_database(INFLUXDB_DATABASE)
    connection = InfluxDBConnection(
        client=client,
        host=influxdb_container.get_container_host_ip(),
        port=influxdb_container.get_host_port(),
        username="root",
        password="root",
        database=INFLUXDB_DATABASE,
    )

    with client:
        yield connection
