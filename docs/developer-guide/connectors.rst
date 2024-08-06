.. _connectors:

######################################
Configuring an InfluxDB Sink connector
######################################

An InfluxDB Sink connector consumes data from Kafka and writes to InfluxDB.
Sasquatch uses the Telegraf `Kafka consumer input`_ and the `InfluxDB v1 output`_ plugins for that.

The connector configuration is specified per Sasquatch environment in ``sasquatch/values-<environment>.yaml``.

Here's what the connector configuration for writing data from the ``lsst.example.skyFluxMetric`` kafka topic to InfluxDB looks like:

.. code:: yaml

  telegraf-kafka-consumer:
    enabled: true
    kafkaConsumers:
      example:
        enabled: true
        topicRegexps: |
          [ "lsst.example" ]
        database: "lsst.example"
        timestamp_field: "timestamp"
        timestamp_format: "unix_ms"
        tags: |
          [ "band", "instrument" ]
        replicaCount: 1

Selecting Kafka topics
======================

``kafkaConsumers.example.topicRegexps`` is a list of regular expressions used to specify the Kafka topics consumed by this connector, and ``KafkaConsumers.example.database`` is the name of the InfluxDB v1 database to write to. 
In this example, all Kafka topics prefixed by ``lsst.example`` are recorded in the ``lsst.example`` database in InfluxDB.

.. note::

  If the database doesn't exist in InfluxDB it is automatically create by Telegraf.
  Telegraf also records internal metrics from its input and output plugins in the same database.

Timestamp
=========

InfluxDB, being a time-series database, requires a timestamp to index the data.
The name of the field that contains the timestamp value and the timestamp format are specified by the ``kafkaConsumers.example.timestamp_field`` and 
``kafkaConsumers.timestamp_format`` keys.

Tags
====

InfluxDB tags provide additional context when querying data. 

From the ``lsst.example.skyFluxMetric`` metric example:

.. code:: json

    {
        "timestamp": 1681248783000000,
        "band": "y",
        "instrument": "LSSTCam-imSim",
        "meanSky": -213.75839364883444,
        "stdevSky": 2328.906118708811,
    }

``band`` and ``instrument`` are good candidates for tags, while ``meanSky`` and ``stdevSky`` are the fields associated to the ``lsst.example.skyFluxMetric`` metric. 
Tags are specified in the ``kafkaConsumers.example.tags`` list which is the superset of the tags from all the Kafka topics consumed by this connector.

In InfluxDB tags are indexed, you can use tags to efficiently aggregate and filter data in different ways. 
For example, you might query the ``lsst.example.skyFluxMetric`` metric and group the results by ``band``, or you might filter the data to only return values for a specific band or instrument.

.. note::

    In InfluxDB tags values are always strings.
    Use an empty string when a tag value is missing.
    Avoid tagging high cardinality fields such as IDs.

See `InfluxDB schema design and data layout`_ for more insights on how to design tags.

See the `telegraf-kafka-consumer subchart`_ for additional configuration options.

.. _InfluxDB v1 output: https://github.com/influxdata/telegraf/blob/master/plugins/outputs/influxdb/README.md
.. _Kafka consumer input: https://github.com/influxdata/telegraf/blob/master/plugins/inputs/kafka_consumer/README.md
.. _InfluxDB schema design and data layout: https://docs.influxdata.com/influxdb/v1/concepts/schema_and_data_layout
.. _telegraf-kafka-consumer subchart: https://github.com/lsst-sqre/phalanx/tree/main/applications/sasquatch/charts/telegraf-kafka-consumer/README.md
