.. _broker-migration:

######################
Kafka broker migration
######################

In Strimzi, the broker storage is configured in the ``kafkaNodePool`` resource.
From time to time, you may need to expand broker storage capacity, migrate the brokers to a new storage system or even migrate the brokers to different physical nodes, if they use local storage.
These operations involve creating a new ``KafkaNodePool`` with the updated storage configuration and then transferring data from the old brokers to the new ones using Cruise Control.
With Cruise Control, you can rebalance the data across the brokers without downtime, ensuring a smooth migration.

.. note::

  This broker migration procedure is based on the `Kafka Node Pools Storage & Scheduling`_ Strimzi blog post.

Before you begin, ensure that Cruise Control is enabled in your Sasquatch Phalanx environment.
Check your ``sasquatch/values-<environment>.yaml`` file for the following:

.. code:: yaml

  strimzi-kafka:
    cruiseControl:
      enabled: true

Here we illustrate the procedure to migrate the Kafka brokers to a different storage system,
assuming the new storage class is called ``localdrive`` and is available in your Kubernetes cluster.

To create a new ``KafkaNodePool`` with this storage class, enable the ``brokerMigration`` section in your ``sasquatch/values-<environment>.yaml`` file and specify the new pool name, the node IDs of the new brokers (usually use sequential numbers from the existing brokers), the size of the new storage, and the new storage class name, ``localdrive``.

For now, set ``rebalance.enabled: false`` to avoid rebalancing the data immediately after creating the new ``KafkaNodePool`` resource.

.. code:: yaml

  brokerMigration:
    enabled: true
    name: kafka-local-storage
    nodeIDs: "[6,7,8]"
    size: 1.5Ti
    storageClassName: "localdrive"

    rebalance:
      enabled: false

.. note::

  You can also specify other configuration like affinity, tolerations and Kubernetes resources for the brokers, omitted here for simplicity.

To apply this configuration sync the new ``KafkaNodePool`` resource in Argo CD.

At this point, your data still resides on the old brokers, and the new ones will be empty.
To move the data, use Cruise Control by setting ``rebalance.enabled: true`` and the IDs of the brokers to avoid — the ones you plan to remove after the migration.


.. code:: yaml

  brokerMigration:
    enabled: true
    name: kafka-local-storage
    nodeIDs: "[6,7,8]"
    size: 1.5Ti
    storageClassName: "localdrive"

    rebalance:
      enabled: true
      avoidBrokers:
        - 3
        - 4
        - 5

This configuration will create a new ``KafkaRebalance`` resource that will instruct Cruise Control to migrate the data from the old brokers (3, 4, 5) to the new ones (6, 7, 8).

Next, wait for Cruise Control to execute the cluster rebalance.
You can check the state of the rebalance by inspecting the ``KafkaRebalance`` resource in the ``sasquatch`` namespace and monitoring the status of the rebalance.

.. code:: bash

    $ kubectl get kafkarebalances.kafka.strimzi.io -n sasquatch
    NAME               CLUSTER     PENDINGPROPOSAL   PROPOSALREADY   REBALANCING   READY   NOTREADY   STOPPED
    broker-migration   sasquatch                                                   True

During rebalance you can also verify the data being moved to the new brokers by checking the topic partitions in :ref:`kafdrop-ui`.


Once the rebalance is complete, you can swap the new ``KafkaNodePool`` configuration with the old ``KafkaNodePool`` configuration, by updating the ``broker:`` section and disabling (or just removing) the ``brokerMigration:`` section.

.. code:: yaml

  broker:
    enabled: true
    name: kafka-local-storage
    nodeIDs: "[6,7,8]"
    size: 1.5Ti
    storageClassName: "localdrive"

  brokerMigration:
    enabled: false

Also, ensure that you update the Kafka external listener configuration to match the new broker IDs.

.. code:: yaml

  externalListener:
    brokers:
      - broker: 6
        loadBalancerIP: "139.229.180.92"
        host: sasquatch-kafka-6.lsst.codes
      - broker: 7
        loadBalancerIP: "139.229.180.93"
        host: sasquatch-kafka-7.lsst.codes
      - broker: 8
        loadBalancerIP: "139.229.180.94"
        host: sasquatch-kafka-8.lsst.codes

After applying this configuration, you can delete the old brokers by removing the old ``KafkaNodePool`` resource from Argo CD.
Note that the PVCs of the old brokers need to be deleted manually, as they are orphan resources in Sasquatch.


.. _Kafka Node Pools Storage & Scheduling: https://strimzi.io/blog/2023/08/28/kafka-node-pools-storage-and-scheduling/
