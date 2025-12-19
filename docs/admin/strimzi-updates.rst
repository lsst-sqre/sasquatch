.. _strimzi-updates:


###################################
Strimzi Operator and Kafka upgrades
###################################

It is recommended that you perform incremental upgrades of the `Strimzi Operator`_ as new releases become available.
In Phalanx, dependabot will detect a new version of the Strimzi Operator.
Once you merge the dependabot PR into the ``main`` branch, you can sync the Strimzi app in Argo CD.

This operation will upgrade the operator to the latest version and will trigger a Kafka rollout in the namespaces watched by Strimzi.

.. note::

    Before upgrading Strimzi, ensure that the latest version of the operator is compatible with the Kubernetes version running in your cluster.

If the currently deployed Kafka version is not supported by the latest operator, the operator will fail to initiate a Kafka rollout and will display an error.
See :ref:`kafka-upgrades` for instructions on upgrading Kafka.

.. _kafka-upgrades:

Kafka upgrades
==============

Each Strimzi release supports a range of Kafka versions.
Use the latest version of Kafka that is supported by the operator whenever possible.

Upgrading the Kafka brokers and client applications in Sasquatch (e.g., MirrorMaker2) involves updating the Kafka ``version`` in ``sasquatch/charts/strimzi-kafka/values.yaml``.

Note that you do not explicitly set the Kafka ``metadataVersion`` in Sasquatch; instead, Strimzi automatically updates it to the current default after you update the Kafka version.

.. note::

    When upgrading Kafka from an unsupported version to a supported version, an outage will occur during the upgrade of the second broker.
    This happens because, while the first broker will be running the new version supported by the operator, the third broker will still be on an unsupported version.
    Since Sasquatch requires a minimum of two in-sync replicas for each Kafka topic, this mismatch would cause an outage.

    If your current version of Kafka is not supported by the new version of the operator, to avoid an outage during the upgrades, first update Kafka to a supported version and then update the operator.

Refer to the `Strimzi documentation`_ for more details.

.. _Strimzi Operator: https://strimzi.io/downloads/

.. _Strimzi documentation: https://strimzi.io/docs/operators/in-development/deploying#proc-upgrade-kafka-kraft-str
