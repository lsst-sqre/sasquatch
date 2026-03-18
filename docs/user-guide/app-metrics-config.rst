.. _app-metrics-config:

#################################
Application metrics configuration
#################################

Phalanx applications can use Sasquatch to publish metrics events.

This guide describes how to configure application metrics in Sasquatch to create a Kafka user and topic, and a Telegraf connector to write to the ``lsst.square.metrics`` database in Sasquatch.

The messages are expected to be in :ref:`Avro <avro-schemas>` format, and schemas are expected to be in the `Schema Registry`_ for any messages that are encoded with a schema ID.

See :ref:`connect to kafka<direct-connection>` to publish metrics to Sasquatch, or if you have a `Safir`_ app, you can use the Safir metrics helpers to streamline this integration.


Phalanx applications that want to publish metrics events need to:

* Set ``app-metrics.enabled`` to ``true`` in every Sasquatch **environment** values files where app metrics should be enabled
* Set the app name to the  ``app-metrics.apps`` list in the Sasquatch **environment** values file
* Set an entry to the ``globalAppConfig`` dict in the **app-metrics** ``values.yaml`` file in Phalanx.

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

  * Start consuming from the ``lsst.square.metrics.events.<app name>`` Kafka topic.
  * Push metrics to InfluxDB with the all of the ``influxTags`` keys in all events ending up as `tags`_, and all other keys ending up as `fields`_.
