.. _architecture:

#####################
Architecture Overview
#####################


.. figure:: /_static/sasquatch_architecture_single.png
   :name: Sasquatch architecture overviewpng

Kafka
-----

In Sasquatch, `Kafka`_ is used as a message queue to InfluxDB and for data replication between Sasquatch :ref:`environments`.

Kafka is managed by `Strimzi`_.
In addition to the Strimzi components, Sasquatch uses the Confluent Schema Registry and the Confluent Kafka REST proxy to connect HTTP-based clients with Kafka.

.. _Kafka: https://kafka.apache.org
.. _Strimzi: https://strimzi.io

Kafka Connect
-------------

In Sasquatch, Kafka connectors are managed by the `kafka-connect-manager`_ tool.

The InfluxDB Sink connector consumes Kafka topics, converts the records to the InfluxDB line protocol, and writes them to an InfluxDB database.
Sasquatch :ref:`namespaces` map to InfluxDB databases.

The MirrorMaker 2 source connector is used for data replication.


InfluxDB Enterprise
-------------------

InfluxDB is a `time series database`_ optimized for efficient storage and analysis of time series data.

InfluxDB organizes the data in measurements, fields, and tags.
In Sasquatch, Kafka topics (telemetry topics and metrics) map to InfluxDB measurements.

InfluxDB provides an SQL-like query language called `InfluxQL`_ and a more powerful data scripting language called `Flux`_.
Both languages can be used in Chronograf for data exploration and visualization.

Read more about the Sasquatch architecture in `SQR-068`_.

.. _kafka-connect-manager: https://kafka-connect-manager.lsst.io/
.. _time series database: https://www.influxdata.com/time-series-database/
.. _InfluxQL: https://docs.influxdata.com/influxdb/v1.8/query_language/
.. _Flux: https://docs.influxdata.com/influxdb/v1.8/flux/
.. _SQR-068: https://sqr-068.lsst.io


