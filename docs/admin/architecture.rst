.. _architecture:

######################
Sasquatch Architecture
######################

A typical Sasquatch deployment consists of the following main components:

.. figure:: /_static/sasquatch_architecture_single.png
   :name: Sasquatch architecture
   :alt: Sasquatch architecture diagram
   :align: center

Apache Kafka
------------

In Sasquatch, `Kafka`_ is used as a message queue to InfluxDB and for data replication between Sasquatch :ref:`environments`.

Kafka is managed by the `Strimzi`_ operator.
In addition to the Strimzi components, Sasquatch uses the Confluent Schema Registry to manage Avro schemas for kafka topics, and the Confluent Kafka REST proxy to connect HTTP-based clients with Kafka.

.. _Kafka: https://kafka.apache.org
.. _Strimzi: https://strimzi.io


Telegraf connectors
-------------------

Telegraf connectors are used to read data from Kafka topics and write to InfluxDB.

Data is organized by :ref:`namespaces` which map to databases in InfluxDB.


MirrorMaker2
------------

MirrorMaker2 is used for data replication between Sasquatch :ref:`environments`.
Two-way replication is supported.


InfluxDB Enterprise
-------------------

InfluxDB is a `time series database`_ optimized for efficient storage and querying time-series data.
Sasquatch uses InfluxDB Enterprise v1 to support high-availability and clustering.

InfluxDB provides an SQL-like query language called `InfluxQL`_ and a data scripting language called `Flux`_.
Both languages can be used in Chronograf for data exploration and visualization.
Kapacitor is used for alerting and data processing.

Read more about the Sasquatch architecture in `SQR-068`_.

.. _kafka-connect-manager: https://kafka-connect-manager.lsst.io/
.. _time series database: https://www.influxdata.com/time-series-database/
.. _InfluxQL: https://docs.influxdata.com/influxdb/v1.8/query_language/
.. _Flux: https://docs.influxdata.com/influxdb/v1.8/flux/
.. _SQR-068: https://sqr-068.lsst.io


