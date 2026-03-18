.. _namespaces:

##########
Namespaces
##########

This guide describes the use of namespaces in Sasquatch. Namespaces help users to organize data from various sources.

Kafka topic names
-----------------

Kafka topic names in Sasquatch are prefixed with a namespace that identifies the data source and the context of the data.

Use ``lsst.{system}.{topic}`` convention for the fully qualified name of your Kafka topic.
You can add more levels as needed, for example ``lsst.{system}.{component}.{topic}``.

Existing namespaces
--------------------

Some of the existing namespaces in Sasquatch:

- ``lsst.example``: Example metrics used in the Sasquatch documentation.
- ``lsst.sal``: Observatory telemetry published by the Observatory Control System, with schemas defined by `SAL interfaces`_.
- ``lsst.dm``: Metrics computed by Data Management (DM) Pipelines.
- ``lsst.verify``:  CI metrics for both AP and DRP processing.
- ``lsst.prompt``: Metrics for Prompt Processing.
- ``lsst.square.metrics``: Metrics for the SQuaRE services.

.. note::

    Namespaces depend on the data sources available in each Sasquatch environment.

Namespaces and Sasquatch remote context
---------------------------------------

Namespaces play an important role in ensuring data consistency across Sasquatch environments when data replication is enabled.

When data replication is enabled between two Sasquatch environments, the namespace includes the name of the source (remote) cluster to help identifying the origin of the data and to avoid name conflicts with existing topics in the target (local) cluster.

The corresponding kafka topics are also called remote Kafka topics and they are prefixed with the source cluster alias, for example ``<source>.lsst.example``.

See :ref:`remote-context` for more details.
