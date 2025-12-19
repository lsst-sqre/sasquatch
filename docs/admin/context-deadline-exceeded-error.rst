.. context-deadline-exceeded-error:


“Context deadline exceeded” error when Telegraf writes to InfluxDB
==================================================================

In Sasquatch, you might see the ``context deadline exceeded`` error in Telegraf when writing to InfluxDB.
This means the write took longer than the Telegraf HTTP client timeout.

.. code::

  2025-10-21T22:04:06Z E! [outputs.influxdb] When writing to
  [http://sasquatch-influxdb-enterprise-active-data.sasquatch:8086]:
  failed doing req: Post
  "http://sasquatch-influxdb-enterprise-active-data.sasquatch:8086/write?db=efd":
  context deadline exceeded (Client.Timeout exceeded while awaiting headers)

Mitigations
-----------

Send smaller batches
^^^^^^^^^^^^^^^^^^^^^

Reduce ``metric_batch_size`` so Telegraf sends smaller payloads more frequently.
This can be set per Telegraf Kafka consumer in the environment ``values.yaml`` file and may vary depending on data volume being handled.

Example:

.. code:: yaml

  telegraf:
    kafkaConsumers:
      m1m3ts:
        enabled: true
        metric_batch_size: 500  # reduce to send smaller payloads, default is 1000
        database: "efd"
        topicRegexps: |
          [ "lsst.sal.MTM1M3TS" ]


Increase Telegraf timeout
^^^^^^^^^^^^^^^^^^^^^^^^^

Increase the InfluxDB output plugin timeout in the Telegraf configuration.
In the Sasquatch Telegraf subchart, you can do this by increasing the ``timeout`` value under the InfluxDB output configuration in the ``_helpers.tpl`` template file.

.. code:: toml

  [[outputs.influxdb]]
    urls    = ["http://sasquatch-influxdb-enterprise-active-data.sasquatch:8086"]
    database = "efd"
    timeout = "30s"  # increase to tolerate slow responses, default is 15s

If errors persist, check:

- Server health/latency: InfluxDB CPU, disk I/O, compactions, network/DNS issues.
- Write pressure: If ingestion bursts, consider reducing ``flush_interval`` (more frequent flushes) or increasing InfluxDB resources.
- Telegraf resource limits: Ensure Telegraf has enough CPU/memory to handle load.
