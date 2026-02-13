.. _app-metrics:

###################
Application metrics
###################

Phalanx applications can use Sasquatch to publish metrics events.
See the :ref:`app-metrics-config` guide for how to configure application metrics in Sasquatch.

Application metrics are published to the ``lsst.square.metrics`` database in InfluxDB, and are tagged with the app name and any other tags specified in the configuration.
