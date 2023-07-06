.. _namespaces:

##########
Namespaces
##########

Namespaces are used to organize and differentiate data within different systems or components in Sasquatch.

Use the ``lsst.{system}.{topic}`` convention for the full qualified name of your metrics or topics in Sasquatch.

You can add more hierarquical levels as needed, for exampple ``lsst.{system}.{component}.{topic}``.

Here are the namespaces already configured:

- ``lsst.example``: This namespace is used for example metrics in the Sasquatch documentation. It contains metrics that serve as examples for users.
- ``lsst.sal``: This namespace is used by SAL (the Software Abstraction Layer) for the observatory telemetry, events, and commands topics. It is associated with data related to observatory operations and control.
- ``lsst.dm``: This namespace is used for metrics computed by DM (Data Management) Science Pipelines.
- ``lsst.rubintv``: This namespace is used for RubinTV data.
- ``lsst.camera``: This namespace is used for the Camera diagnostic metrics.
- ``lsst.verify.ap``: This namespace is used for ``ap_verify`` metrics, which are related to backward compatibility with the ``lsst.verify`` package.
- ``lsst.verify.drp``: This namespace is used for ``verify_drp`` metrics, which are related to backward compatibility with the ``lsst.verify`` package.
- ``lsst.debug``: This namespace is used for testing and is available only in the USDF development environment.

By using these namespaces, Sasquatch enables better organization, management, and identification of data within different systems or components, preventing naming conflicts and allowing users to locate and relate data more easily.
