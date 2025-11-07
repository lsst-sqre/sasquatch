.. _connectors:

############################
Managing Telegraf connectors
############################

Sasquatch uses Telegraf to consume data from Kafka and to write to InfluxDB.
Telegraf is configured in the Sasquatch `telegraf`_ subchart and uses the `Kafka consumer`_ plugin with the Avro parser and the `InfluxDB v1`_ output plugin.

Configuration
=============

The Telegraf configuration is specified in each Sasquatch environment in ``sasquatch/values-<environment>.yaml``.

In this section we cover the configuration options used in the ``example`` connector.
For the complete set of configuration options see the `telegraf`_ subchart documentation.

The ``example`` connector writes data for the ``skyFluxMetric`` metric (see :ref:`avro`) to InfluxDB.
Here is the configuration for the ``example`` connector:

.. code:: yaml

  telegraf:
    enabled: true
    kafkaConsumers:
      example:
        enabled: true
        debug: true
        topicRegexps: |
          [ "lsst.example" ]
        database: "lsst.example"
        timestamp_field: "timestamp"
        timestamp_format: "unix_ms"
        tags: |
          [ "band", "instrument" ]

Kafka topics and InfluxDB database
----------------------------------

The ``skyFluxMetric`` metric is published to the ``lsst.example.skyFluxMetric`` Kafka topic, where the prefix ``lsst.example`` corresponds to the namespace.

``topicRegexps`` accepts a list of regular expressions to select the Kafka topics for this connector.
The ``database`` specify the name of the database in InfluxDB v1 to record the data to.
In this example, we select all Kafka topics from the ``lsst.example`` namespace and record the data in the ``lsst.example`` database in InfluxDB.

.. note::

  If the database doesn't exist in InfluxDB it is automatically create by Telegraf.

Timestamps
----------

InfluxDB requires a timestamp to index the data.
``timestamp_field`` specifies the name of the field that contains the timestamp we want to use, and ``timestamp_format`` specifies the timestamp format.
In this example, the ``timestamp`` field contains timestamp values in Unix milliseconds format.


Tags
----

Tags provide additional context for querying the data. In InfluxDB, tags are indexed and can be used to filter and group data efficiently.
To decide which fields to use as tags, consider the fields that you might want to filter or group by when querying the data.

In the connector configuration use ``tags`` to specify the list of fields that should be tags in InfluxDB.

From the ``lsst.example.skyFluxMetric`` metric example:

.. code:: json

    {
        "timestamp": 1681248783000000,
        "band": "y",
        "instrument": "LSSTCam-imSim",
        "meanSky": -213.75839364883444,
        "stdevSky": 2328.906118708811,
    }

``band`` and ``instrument`` are good candidates for tags, while ``meanSky`` and ``stdevSky`` are the metric values.

.. note::

  In InfluxDB tags values are always strings.
  Use fields with discrete values as tags and avoid high cardinality fields.

See `InfluxDB schema design and data layout`_ for more insights on how to design tags.

List connectors
---------------

To list the Telegraf connectors in a given Sasquatch environment run:

.. code:: bash

  kubectl -n sasquatch get deploy -l app.kubernetes.io/name=sasquatch-telegraf

To list the Telegraf connector Pods for all connector instances:

.. code:: bash

  kubectl -n sasquatch get pods -l app.kubernetes.io/name=sasquatch-telegraf

To list the Telegraf connector Pod for a given connector instance (the connection name is the key used in the configuration, e.g. ``example``):

.. code:: bash

  kubectl -n sasquatch get pods -l app.kubernetes.io/instance=sasquatch-telegraf-<connector-name>
  kubectl -n sasquatch get pods -l app.kubernetes.io/instance=sasquatch-telegraf-example

View connector logs
-------------------

To view the last few log entries from all Telegraf connectors, run:

.. code:: bash

  kubectl -n sasquatch logs -l app.kubernetes.io/name=sasquatch-telegraf

Use ``jq`` to format and filter the structured logs, for example to show only error messages:

.. code:: bash

  kubectl -n sasquatch logs -l app.kubernetes.io/name=sasquatch-telegraf | jq 'select(.level == "ERROR")'

To view the logs from a single Telegraf connector instance, using ``-f`` to stream the logs during debugging:


.. code:: bash

  kubectl -n sasquatch logs -l app.kubernetes.io/instance=sasquatch-telegraf-<connector-name> -f
  kubectl -n sasquatch logs -l app.kubernetes.io/instance=sasquatch-telegraf-example -f

Stop connectors
---------------

To stop all Telegraf connectors you can scale the deployment down to zero replicas:

.. code:: bash

  kubectl -n sasquatch scale deploy -l app.kubernetes.io/name=sasquatch-telegraf --replicas=0

To start the connectors again, scale the deployment back to one replica:

.. code:: bash

  kubectl -n sasquatch scale deploy -l app.kubernetes.io/name=sasquatch-telegraf --replicas=1

Restart connectors
------------------

To restart all Telegraf connectors, run:

.. code:: bash

  kubectl -n sasquatch rollout restart deploy -l app.kubernetes.io/name=sasquatch-telegraf

Monitoring
----------

Telegraf internal metrics are recorded under the ``telegraf`` database in Sasquatch and provide information about memory and buffer usage, throughput as well as read and write errors for each connector instance.
See the **Connectors** dashboard in Chronograf to monitor the Telegraf connectors.


.. _InfluxDB v1: https://github.com/influxdata/telegraf/blob/master/plugins/outputs/influxdb/README.md
.. _Kafka consumer: https://github.com/influxdata/telegraf/blob/master/plugins/inputs/kafka_consumer/README.md
.. _InfluxDB schema design and data layout: https://docs.influxdata.com/influxdb/v1/concepts/schema_and_data_layout
.. _telegraf: https://github.com/lsst-sqre/phalanx/tree/main/applications/sasquatch/charts/telegraf/README.md
