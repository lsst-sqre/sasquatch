"""A testcontainer for InfluxDB v1."""

from dataclasses import dataclass
from typing import Any

from influxdb import InfluxDBClient
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import HttpWaitStrategy

from sasquatch.services.influxdb import InfluxDBService

__all__ = ["InfluxDBConnection", "InfluxDBTestcontainer"]

PORT = 8086
IMAGE = "influxdb:1.12"


@dataclass
class InfluxDBConnection:
    """A service and connection info to the InfluxDB Testcontainer.

    It would be nice if we could get this from the client instance, but we
    can't.
    """

    client: InfluxDBClient
    """An InfluxDB client pointed at this instance."""

    service: InfluxDBService
    """An InfluxDBService to use in tests."""

    host: str
    """The host of this instance."""

    port: int
    """The port of this instance."""

    username: str
    """Username to access this instance."""

    password: str
    """Password to access this instance."""

    database: str
    """The database the client is configured with."""


class InfluxDBTestcontainer(DockerContainer):
    """A testcontainer for InfluxDB v1.

    There is one of these built-in to testcontainers, but the module/package
    structure is such that we'd need to install the influxdb v2 client just to
    import the v1 testcontainer, so let's just make our own.

    We're setting the container port and the docker image directly. We'll
    always let testcontainers assign the host port.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.container_port = PORT

        super().__init__(IMAGE, *args, **kwargs)

        _ = self.with_bind_ports(self.container_port, None)
        _ = self.waiting_for(HttpWaitStrategy(self.container_port, "/health"))

    def get_host_port(self) -> int:
        return self.get_exposed_port(self.container_port)

    def make_client(self, **kwargs: Any) -> InfluxDBClient:
        """Return InfluxDB Python client pointing to this container."""
        return InfluxDBClient(
            self.get_container_host_ip(),
            self.get_host_port(),
            **kwargs,
        )

    def reset(self) -> None:
        """Delete all non-internal data and create a fresh database."""
        client = self.make_client()
        with client:
            databases = [
                database
                for database in client.get_list_database()
                if database["name"] != "_internal"
            ]

            for database in databases:
                name = database["name"]
                client.drop_database(name)
