.. _connectors:

###################
Telegraf connectors
###################

Sasquatch uses Telegraf to consume data from Kafka and write it to InfluxDB.
This guide describes how to configure and deploy Telegraf connectors, manage their lifecycle (list, debug, stop, restart) and monitor their status.

Configuration
=============

Telegraf is deployed by the `telegraf subchart`_ and uses the `Kafka consumer`_ plugin with the Avro parser and the `InfluxDB v1`_ output plugin.

The configuration is specified in each Sasquatch environment in ``sasquatch/values-<environment>.yaml``.

In this section we cover the configuration options used in the ``example`` connector.
For the complete set of configuration options see the `telegraf subchart`_ documentation.

The ``example`` connector writes data for the ``skyFluxMetric`` metric (see :ref:`avro-schemas`) to InfluxDB.
Here is the ``example`` connector configuration:

.. code:: yaml

  telegraf:
    enabled: true
    kafkaConsumers:
      example:
        enabled: true
        debug: true
        topicRegexps:
          - "lsst.example"
        database: "lsst.example"
        timestamp_field: "timestamp"
        timestamp_format: "unix_ms"
        tags: |
          [ "band", "instrument" ]

Selecting Kafka topics
----------------------

Use ``topicRegexps`` to specify a list of regular expressions to select Kafka topics consumed by the connector.
This list is additive and uses `Go's standard regexp package`_ which implements regular expressions using RE2 syntax.

``database`` specifies the name of the database in InfluxDB and Sasquatch convention is to use the same namespace as the Kafka topics.

In the example above we select all Kafka topics with the ``lsst.example`` prefix and write the data into the ``lsst.example`` database in InfluxDB.

.. note::

  If the database doesn't exist in InfluxDB, it is automatically created by
  Telegraf.

Discovering topics dynamically
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``topicDiscovery`` when the set of Kafka topics changes over time and
cannot be maintained as a static ``topicRegexps`` list. Topic discovery is
configured independently for each connector. For example:

.. code:: yaml

  telegraf:
    kafkaConsumers:
      example:
        enabled: true
        database: "lsst.example"
        topicDiscovery:
          enabled: true
          includePrefixes:
            - "lsst.example"
          excludePrefixes:
            - "lsst.example.private"
          refreshInterval: "30s"

``includePrefixes`` and ``excludePrefixes`` contain literal, case-sensitive
topic prefixes. A topic is selected when it starts with any include prefix
and no exclude prefix. Exclusions take precedence. The example therefore
includes ``lsst.example``, ``lsst.example.skyFluxMetric``, and
``lsst.examples``, but excludes ``lsst.example.private`` and
``lsst.example.private.metric``.

At least one non-empty include prefix is required. Prefixes cannot contain
leading or trailing whitespace or newlines. If ``topicDiscovery.enabled`` is
true, ``topicRegexps`` is ignored. To require a namespace separator, include
it in the prefix; for example, ``lsst.example.`` does not match
``lsst.examples``.

Each Telegraf Pod runs a topic-discovery sidecar. The sidecar queries Kafka
immediately at startup and then every ``refreshInterval``, using the existing
``telegraf`` Kafka credentials. It writes an explicit, sorted topic list to a
dynamic Telegraf configuration file. Telegraf watches that file and reloads
the configuration when the selected topic set changes, without restarting
the Pod or resetting consumer-group offsets.

A successful query that selects no topics installs an empty dynamic
configuration, stopping Kafka consumption until a later query finds matching
topics. A failed Kafka query or invalid result preserves the last known-good
configuration. The sidecar becomes ready only after its first successful
query, including a successful query with no matches. Inspect discovery logs
for one connector with:

.. code:: bash

  kubectl logs \
    --namespace sasquatch \
    --selector app.kubernetes.io/instance=sasquatch-telegraf-<connector-name> \
    --container topic-discovery

The sidecar runs the following Sasquatch command in watch mode:

.. code:: bash

  sasquatch telegraf update-topic-config \
    --watch \
    --bootstrap-server sasquatch-kafka-brokers.sasquatch:9092 \
    --include-prefixes-file /etc/telegraf-static/include-prefixes.txt \
    --exclude-prefixes-file /etc/telegraf-static/exclude-prefixes.txt \
    --input-template /etc/telegraf-static/kafka-consumer.conf.tmpl \
    --output-config /etc/telegraf-dynamic/kafka-consumer.conf \
    --ready-file /var/run/topic-discovery/ready \
    --refresh-interval 30s

The command performs one reconciliation and exits when ``--watch`` is
omitted. ``TELEGRAF_PASSWORD`` must be present in its environment. See
:ref:`cli` for the complete command reference.

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

Deployment
==========

Telegraf connectors are deployed as Kubernetes Deployments in the ``sasquatch`` namespace.
Each connector instance has a separate ConfigMap and Deployment.

To deploy a new connector instance, sync the Sasquatch application in Argo CD for the given environment.

Managing connectors
===================

List connectors
---------------

To list the Telegraf connectors in a given Sasquatch environment, run:

.. code:: bash

  kubectl get deploy \
  --namespace sasquatch \
  --selector app.kubernetes.io/name=sasquatch-telegraf

To list the Telegraf connector Pods for all connector instances, run:

.. code:: bash

  kubectl get pods \
  --namespace sasquatch \
  --selector app.kubernetes.io/name=sasquatch-telegraf

To list the Telegraf connector Pod for a given connector instance:

.. code:: bash

  kubectl get pods \
  --namespace sasquatch \
  --selector app.kubernetes.io/instance=sasquatch-telegraf-<connector-name>

For example, to list the Pods for the ``example`` connector:

.. code:: bash

  kubectl get pods \
  --namespace sasquatch \
  --selector app.kubernetes.io/instance=sasquatch-telegraf-example


View connector logs
-------------------

To view the most recent log entries from all Telegraf connectors:

.. code:: bash

  kubectl logs \
  --namespace sasquatch \
  --selector app.kubernetes.io/name=sasquatch-telegraf

You can use ``jq`` to format and filter structured logs.
For example, to show only error messages, run:

.. code:: bash

  kubectl logs \
  --namespace sasquatch \
  --selector app.kubernetes.io/name=sasquatch-telegraf \
  | jq 'select(.level == "ERROR")'

To view the logs for a specific connector instance:

.. code:: bash

  kubectl logs \
  --namespace sasquatch \
  --selector app.kubernetes.io/instance=sasquatch-telegraf-<connector-name> \
  --timestamps \
  --tail=100

For example, to view the logs for the ``example`` connector:

.. code:: bash

  kubectl logs \
  --namespace sasquatch \
  --selector app.kubernetes.io/instance=sasquatch-telegraf-example \
  --timestamps \
  --tail=100

Stop connectors
---------------

To stop all Telegraf connectors you can scale the deployment down to zero replicas:

.. code:: bash

  kubectl scale deploy \
    --namespace sasquatch \
    --selector app.kubernetes.io/name=sasquatch-telegraf \
    --replicas=0

To start the connectors again, scale the deployment back to one replica:

.. code:: bash

  kubectl scale deploy \
    --namespace sasquatch \
    --selector app.kubernetes.io/name=sasquatch-telegraf \
    --replicas=1

Restart connectors
------------------

To restart all Telegraf connectors, run:

.. code:: bash

  kubectl rollout restart deploy \
  --namespace sasquatch \
  --selector app.kubernetes.io/name=sasquatch-telegraf

Monitoring
==========

Telegraf internal metrics are recorded in the ``telegraf`` database in Sasquatch and provide information about memory and buffer usage, throughput as well as read and write errors for each connector instance.
See the **Connectors** dashboard in Chronograf to monitor the Telegraf connectors.


.. _InfluxDB v1: https://github.com/influxdata/telegraf/blob/master/plugins/outputs/influxdb/README.md
.. _Kafka consumer: https://github.com/influxdata/telegraf/blob/master/plugins/inputs/kafka_consumer/README.md
.. _InfluxDB schema design and data layout: https://docs.influxdata.com/influxdb/v1/concepts/schema_and_data_layout
.. _telegraf subchart: https://github.com/lsst-sqre/phalanx/tree/main/applications/sasquatch/charts/telegraf/README.md
.. _Go's standard regexp package: https://pkg.go.dev/regexp
