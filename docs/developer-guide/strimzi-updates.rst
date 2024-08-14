.. _strimzi-updates:


################
Strimzi upgrades
################

It is recommended that you perform incremental upgrades of the Strimzi operator as soon as new versions become available. 
In Phalanx, dependabot will detect a new version of Strimzi. 
Once you merge the dependabot PR into the ``main`` branch, you can sync the Strimzi app in Argo CD.

This operation will upgrade the operator to the latest version and will trigger a Kafka rollout in the namespaces watched by Strimzi.

.. note::

    Before upgrading Strimzi, ensure that the `latest version of the operator`_ is compatible with the Kubernetes version running in your cluster.

If the currently deployed Kafka version is not supported by the latest operator, the operator will fail to initiate a Kafka rollout and will display an error.
See :ref:`kafka-upgrades` for instructions on upgrading Kafka.

.. _kafka-upgrades:

Kafka upgrades
==============

Each Strimzi release supports a range of Kafka versions. 
It is recommended that you always use the latest version of Kafka that is supported by the operator.

Sasquatch deploys Kafka in KRaft mode.

Upgrading the Kafka brokers and client applications in Sasquatch (Kafka Connect and Mirror Maker 2) involves updating the Kafka ``version`` in ``sasquatch/charts/strimzi-kafka/values.yaml``.

Note that you do not explicitly set the Kafka ``metadataVersion`` in Sasquatch; instead, Strimzi automatically updates it to the current default after you update the Kafka version.

Refer to the `Strimzi documentation`_ for more details.

.. _latest version of the operator: https://strimzi.io/downloads/

.. _Strimzi documentation: https://strimzi.io/docs/operators/in-development/deploying#proc-upgrade-kafka-kraft-str
