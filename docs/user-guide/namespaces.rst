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
- ``lsst.debug`` used by developers when debugging Sasquatch.
- ``lsst.sal`` used by SAL for the observatory telemetry, events and commands topics.
- ``lsst.rubintv`` used by RubinTV data.
- ``lsst.ci`` used for metrics computed by the CI system.
- ``lsst.ap`` used for metrics computed by the Alert Production pipeline.
- ``lsst.drp`` used for metrics computed by the Data Release Production pipeline.
