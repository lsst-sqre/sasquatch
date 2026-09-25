"""Pytest configuration and fixtures."""

from collections.abc import Generator

import pytest

from sasquatch.services.influxdb import InfluxDBService
from sasquatch.storage.influxdb import InfluxDBStorage

from .constants import (
    INFLUXDB_CUSTOM_RETENTION_POLICY,
    INFLUXDB_DATABASE,
    INFLUXDB_INFINITE_RETENTION_DURATION,
)
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
def influxdb_connection_single_retention_policy(
    influxdb_container: InfluxDBTestcontainer,
) -> Generator[InfluxDBConnection]:
    """Give an InfluxDB service and info pointed at prepped instance.

    Only the default retention policy exists in this db.
    """
    database = INFLUXDB_DATABASE
    influxdb_container.reset()
    client = influxdb_container.make_client(database=database)
    client.create_database(INFLUXDB_DATABASE)

    storage = InfluxDBStorage(client=client, database=database)
    service = InfluxDBService(storage=storage)

    connection = InfluxDBConnection(
        client=client,
        service=service,
        host=influxdb_container.get_container_host_ip(),
        port=influxdb_container.get_host_port(),
        username="root",
        password="root",
        database=INFLUXDB_DATABASE,
    )

    with client:
        yield connection


@pytest.fixture
def influxdb_connection(
    influxdb_connection_single_retention_policy: InfluxDBConnection,
) -> InfluxDBConnection:
    """Give an InfluxDB service and info pointed at prepped instance.

    An addition retention policy is created in this db.
    """
    client = influxdb_connection_single_retention_policy.client
    client.create_retention_policy(
        name=INFLUXDB_CUSTOM_RETENTION_POLICY,
        duration=INFLUXDB_INFINITE_RETENTION_DURATION,
        replication="1",
    )
    return influxdb_connection_single_retention_policy
