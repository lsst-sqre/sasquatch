.. _namespaces:

##########
Namespaces
##########

Sasquatch uses namespaces to organize data and prevent naming conflicts between different systems.

In Kafka, namespaces are implemented using topic prefixes.
Use the ``lsst.{system}.{topic}`` convention for the full qualified name of your Kafka topics, where the ``lsst.{system}`` prefix specifies the namespace.
You can add more hierarquical levels as needed, for exampple ``lsst.{system}.{component}.{topic}``.

In InfluxDB, the database name is based on the namespace so that users can more easily find and relate data.

The following namespaces are configured in Sasquatch:

- ``lsst.example`` used for example metrics in the Sasquatch documentation.
- ``lsst.sal`` used by SAL for the observatory telemetry, events and commands topics.
- ``lsst.dm`` used for metrics computed by DM Science Pipelines.
- ``lsst.rubintv`` used for RubinTV data.