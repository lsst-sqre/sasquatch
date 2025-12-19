.. _query-limits:

################################
InfluxDB Enterprise query limits
################################

This guide describes the InfluxDB Enterprise query limits configuration used in Sasquatch.

InfluxDB Enterprise supports several mechanisms to control resource consumption by user queries.
These controls are important to protect the database from excessive load caused by poorly shaped queries or unexpected query spikes.

The default query limits configuration used in Sasquatch is specified in the ``influxdb-enterprise/values.yaml`` file.

The following configuration options are set:

.. code-block:: yaml

  config:
    cluster:
        max-concurrent-queries: 50
        query-timeout: "180s"

        max-select-point: 50000000
        max-select-series: 200000
        max-select-buckets: 20000

        log-queries-after: "10s"
        log-timedout-queries: true
        termination-query-log: true


- ``max-concurrent-queries`` limits the number of concurrent queries that can be executed by the cluster.
  This is not a rate limit, but a limit on simultaneous queries. It can be monitored from the ``queriesActive`` and ``queryExecutorBusy`` InfluxDB internal metrics.
- ``query-timeout`` specifies the maximum duration a query can run before being automatically terminated by the database.

These limits kill or reject excessively expensive individual queries before they destabilize the cluster:

- ``max-select-point`` Maximum total points a single SELECT can process.
  Example: limit ``SELECT`` over very long time ranges.
- ``max-select-series`` Maximum series a single SELECT can process.
  Example: limit ``SELECT *`` on high-cardinality datasets.
- ``max-select-buckets`` Maximum number of ``GROUP BY time()`` buckets.
  Example: limit ``GROUP BY time(1s)`` over weeks of data.

In addition, the following logging options are configured to help monitor and debug long-running queries:

- ``log-queries-after`` specifies the duration after which a running query is logged to the InfluxDB logs.
- ``log-timedout-queries`` enables logging of queries that time out.
- ``termination-query-log`` enables logging of queries that are terminated due to resource limits.


