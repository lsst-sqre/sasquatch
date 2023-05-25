.. _namespaces:

##########
Namespaces
##########

Sasquatch uses namespaces to organize data and prevent naming conflicts between different systems.

In Kafka, namespaces are implemented using topic prefixes.
Use the ``lsst.{system}.{topic}`` convention for the full qualified name of your Kafka topics.
You can add more hierarquical levels as needed, for exampple ``lsst.{system}.{component}.{topic}``.

In Sasquatch, the first part of the namespace ``lsst.{system}`` is used to name the InfluxDB connector and database, so that users can more easily find and relate data.

The following namespaces are configured in Sasquatch:

- ``lsst.example`` used for example metrics in the Sasquatch documentation.
- ``lsst.sal`` used by SAL for the observatory telemetry, events and commands topics.
- ``lsst.dm`` used for metrics computed by DM Science Pipelines.
- ``lsst.rubintv`` used for RubinTV data.
- ``lsst.camera`` used for the Camera diagnostic metrics.
- ``lsst.verify.ap`` used for ``ap_verify`` metrics for backward compatibility with the ``lsst.verify`` package.
- ``lsst.verify.drp`` used for ``verify_drp`` metrics for backward compatibility with the ``lsst.verify`` package.
- ``lsst.debug`` used for testing (available at USDF dev environment only).
