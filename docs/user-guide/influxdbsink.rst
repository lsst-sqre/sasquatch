.. _influxdbsink:

#############
InfluxDB Sink
#############

The InfluxDB Sink connector is a Kafka connector that allows data to be written from Kafka topics to InfluxDB.

Tags
====

In InfluxDB, tags are a type of metadata used to organize and filter data.
Tags are optional but they provide additional context when querying data.

From the ``lsst.example.skyFluxMetric`` metric payload:

.. code:: json

    {
        "timestamp": 1681248783000000,
        "band": "y",
        "instrument": "LSSTCam-imSim",
        "meanSky": -213.75839364883444,
        "stdevSky": 2328.906118708811,
    }

``band`` and ``instrument`` are good candidates for tags.

When you query data from InfluxDB, you can use tags to filter the data and aggregate it in different ways.

For example, you might query the ``lsst.example.skyFluxMetric`` metric and group the results by the ``band`` tag to see ``meanSky`` and ``stdevSky`` in each band.
Or you might filter the data to only show values for a specific band or instrument.

.. note::

    In InfluxDB tags values are always strings.
    Use an empty string when a tag value is missing.
    Avoid tagging high cardinality fields such as IDs.


Configuration
=============

To configure an InfluxDB Sink connector in Sasquatch, add the connector configuration to the corresponding environment in Phalanx.

For example, in ``values-usdfdev.yaml`` the connector configuration to write topics in the ``lsst.example`` namespace to InfluxDB looks like:

.. code:: yaml

    kafka-connect-manager:
      influxdbSink:
        connectors:
          example:
            enabled: true
            timestamp: "timestamp"
            connectInfluxDb: "lsst.example"
            topicsRegex: "lsst.example.*"
            tags: band,instrument

``timestamp`` specify the field in the payload to be used as the InfluxDB time.
``connectInfluxDb`` is the name of the InfluxDB database to write to.
``topicsRegex`` specify the regex to select topics from Kafka.
``tag`` specify the fields in the payload to be used as InfluxDB tags.

See the `kafka-connect-manager subchart`_ for additional configuration options.

.. _kafka-connect-manager subchart: https://github.com/lsst-sqre/phalanx/tree/main/applications/sasquatch/charts/kafka-connect-manager