# Typings from: https://github.com/influxdata/influxdb-python/
# Some of these may not be exactly right, modify as needed the more we use
# this.
from collections.abc import Generator
from datetime import datetime
from typing import Self, TypedDict

from requests import Session

__all__ = ["InfluxDBClient", "ResultSet"]

type ValidValue = str | int | float | bool

class _DatabaseDict(TypedDict):
    name: str

class _MeasurementDict(TypedDict):
    name: str

class _RetentionPolicyDict(TypedDict):
    name: str

class _ClientDict(TypedDict):
    measurement: str
    """The measurement name."""

    tags: dict[str, ValidValue]
    """Tags on this point."""

    fields: dict[str, ValidValue]
    """Fields on this point."""

    time: str | datetime
    """The timestamp of this point."""

class ResultSet:
    def get_points(
        self,
        measurement: str | None = None,
        tags: dict[str, ValidValue] | None = None,
    ) -> Generator[dict[str, str]]: ...

class InfluxDBClient:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8086,
        username: str = "root",
        password: str = "root",
        database: str | None = None,
        ssl: bool = False,
        verify_ssl: bool = False,
        timeout: float | None = None,
        retries: int = 3,
        use_udp: bool = False,
        udp_port: int = 4444,
        proxies: dict[str, str] | None = None,
        pool_size: int = 10,
        path: str = "",
        cert: str | None = None,
        gzip: bool = False,
        session: Session | None = None,
        headers: dict[str, str] | None = None,
        socket_options: list[str] | None = None,
    ) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(self, *args: object, **kwargs: dict) -> None: ...
    def close(self) -> None: ...
    def create_database(self, dbname: str) -> None: ...
    def create_retention_policy(
        self,
        name: str,
        duration: str,
        replication: str,
        database: str | None = None,
        default: bool = False,
        shard_duration: str = "0s",
    ) -> None: ...
    def drop_database(self, dbname: str) -> None: ...
    def get_list_database(self) -> list[_DatabaseDict]: ...
    def get_list_measurements(self) -> list[_MeasurementDict]: ...
    def get_list_retention_policies(self) -> list[_RetentionPolicyDict]: ...
    def switch_database(self, database: str) -> None: ...
    def query(
        self,
        query: str,
        params: dict[str, str] | None = None,
        bind_params: dict[str, str] | None = None,
        epoch: str | None = None,
        expected_response_code: int = 200,
        database: str | None = None,
        raise_errors: bool = True,
        chunked: bool = False,
        chunk_size: int = 0,
        method: str = "GET",
    ) -> ResultSet: ...
    def write_points(
        self,
        points: list[_ClientDict],
        batch_size: int | None = None,
        retention_policy: str | None = None,
    ) -> bool: ...
