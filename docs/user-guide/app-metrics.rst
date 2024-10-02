===================
Application metrics
===================

Applications can use Sasquatch infrastructure to publish metrics events to `InfluxDB`_ via `Kafka`_.
Setting certain Sasquatch values in Phalanx will create Kafka user and topic, and configure a Telegraf consumer to put messages from that topic into the ``telegraf-kafka-app-metrics-consumer`` database in the Sasquatch InfluxDB instance.

The messages are expected to be in :ref:`Avro <avro>` format, and schemas are expected to be in the `Schema Registry`_ for any messages that are encoded with a schema ID.

.. _InfluxDB: https://docs.influxdata.com/enterprise_influxdb/v1/
.. _Kafka: https://kafka.apache.org
.. _Schema Registry: https://docs.confluent.io/platform/current/schema-registry/
.. _Safir: https://safir.lsst.io


Configuration
=============

Apps that want to publish metrics events need to:

* Set ``app-metrics.enabled`` to ``true`` in every Sasquatch **environment** values files where app metrics should be enabled
* Add the app name to the  ``app-metrics.apps`` list in the Sasquatch **environment** values file
* Add an entry to the ``globalAppConfig`` dict in the **app-metrics** ``values.yaml`` file in Phalanx.

This entry should be structured like this:

.. code-block:: yaml
   :caption: applications/sasquatch/charts/app-metrics/values.yaml

   globalAppConfig:
     # App name
     some-app:  # App name
       # An array of events keys that will be tags (vs. fields) in InfluxDB
       influxTags: [ "foo", "bar" ]
     some-other-app:
       influxTags: [ "foo", "bar", "baz" ]

This will:

* Provision a Kafka topic to which the app can publish events
* Provision a Kafka user with access to publish messages to that topic
* Update the ``sasquatch-telegraf-app-metrics`` `Telegraf`_ instance to:

  * Start consuming from the ``lsst.square.metrics.events.<your app's name>`` Kafka topic.
  * Push metrics to InfluxDB with the all of the ``influxTags`` keys in all events ending up as `tags`_, and all other keys ending up as `fields`_.

Then in your app, you can :ref:`connect to kafka<directconnection>` and publish events manually, or if you have a `Safir`_ app, you can use the Safir metrics helpers to streamline this integration.

.. _Telegraf: https://www.influxdata.com/time-series-platform/telegraf/
.. _tags: https://docs.influxdata.com/influxdb/v1/concepts/glossary/#tag
.. _fields: https://docs.influxdata.com/influxdb/v1/concepts/glossary/#field

InfluxDB tags vs. fields
========================

.. hint::

   If the value is likely to be used in a "WHERE" clause in queries, and if it has fewer than 10,000 possible values, it should be a tag.

Any value in an event that is not in the ``influxTags`` list be be field in InfluxDB.
Tags are indexed, which means you can use them as filters efficiently in InfluxDB queries.

It can be difficult to decide what should be a tag and what should be a field, but here are some guidelines:

* If it's a value that will be aggregated and graphed over time, like the duration of a query, then it should be a field, because you'll never be filtering on it.
* If it's metadata like which app generated the event, then it should be a tag.

One thing to keep in mind is that tags shouldn't have a large number of distinct values.
That could lead to a `high-cardinality`_ dataset in InfluxDB, especially when combined with other tags with many distinct values.
A high-cardinality dataset could greatly increase the memory usage of the InfluxDB instance and decrease query performance across the board.

How many values is too many?
There's not a lot of concrete advice on that, and it depends a lot on other tags and the composition of the entire dataset, so let's say **10,000** for now. This means if you have a username on an event, it can be a tag.

.. _high-cardinality: https://www.influxdata.com/blog/red-flags-of-high-cardinality-in-databases/
