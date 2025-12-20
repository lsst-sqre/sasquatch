.. _namespaces:

##########
Namespaces
##########

Namespaces are used to organize data from various sources in Sasquatch.

Use the ``lsst.{system}.{topic}`` convention for the full qualified name of your metrics or telemetry topics in Sasquatch.

You can add more hierarchical levels as needed, for example ``lsst.{system}.{component}.{topic}``.

Here are some examples of namespaces already used in Sasquatch.
Their availability may vary depending on the environment:

- ``lsst.example``: This namespace is used for example metrics in the Sasquatch documentation. It contains metrics that serve as examples for users.
- ``lsst.sal``: This namespace is used by SAL (the Software Abstraction Layer) for the observatory telemetry, events, and commands topics. It is associated with data related to observatory operations and control.
- ``lsst.dm``: This namespace is used for metrics computed by DM (Data Management) Science Pipelines.
- ``lsst.verify.ap``: This namespace is used for ``ap_verify`` metrics, which are related to backward compatibility with the ``lsst.verify`` package.
- ``lsst.verify.drp``: This namespace is used for ``verify_drp`` metrics, which are related to backward compatibility with the ``lsst.verify`` package.

By using namespaces, Sasquatch enables better organization of the data from multiple systems and components, preventing name conflict and enabling users to find data more easily.

Namespaces in Sasquatch remote context
--------------------------------------

In a Sasquatch deployment with remote context enabled, namespaces play a crucial role in ensuring data consistency across replicated environments.

When data is replicated from a source Sasquatch environment to a target environment using MirrorMaker2, the topic names are prefixed with the source cluster alias.
For example, the ``lsst.example`` namespace in the source cluster will be replicated to the target cluster as ``<source>.lsst.example``, where ``source`` is the source cluster alias.
See :ref:`remote-context` for more details.
