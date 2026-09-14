"""Constants used in sasquatch tests."""

__all__ = [
    "INFLUXDB_CUSTOM_RETENTION_POLICY",
    "INFLUXDB_DATABASE",
    "INFLUXDB_INFINITE_RETENTION_DURATION",
]

INFLUXDB_DATABASE = "sasquatchtest"
"""The database name to use for InfluxDB tests."""

INFLUXDB_CUSTOM_RETENTION_POLICY = "custom_rp"

INFLUXDB_INFINITE_RETENTION_DURATION = "INF"
