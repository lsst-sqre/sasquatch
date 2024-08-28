.. _broker-migration:

######################
Kafka broker migration
######################

From time to time, you may need to expand the size of your Kafka storage because your brokers need to handle more data, or you might need to migrate your Kafka brokers to a different storage that uses a new storage class.

In Strimzi, each ``kafkaNodePool`` has its own storage configuration.
The first step in the broker migration process is to create a new ``KafkaNodePool`` with the updated storage configuration.
Once you’ve done this, you can use the Cruise Control tool along with the Strimzi ``KafkaRebalance`` resource to transfer data from the old brokers to the new ones.

This guide documents the procedure for migrating Kafka brokers that were originally deployed using the cluster's default storage class to a new storage class.
This procedure is adapted from the `Kafka Node Pools Storage & Scheduling`_ Strimzi blog post.

Before you begin the broker migration, ensure that Cruise Control is enabled in your Sasquatch Phalanx environment.
Check your ``sasquatch/values-<environment>.yaml`` file for the following:

.. code:: yaml

  strimzi-kafka:
    cruiseControl:
      enabled: true

To migrate your Kafka brokers to a new storage class, you need to specify the storage class name and the size, then set ``brokerStorage.migration.enabled: true`` to initiate the migration.

.. code:: yaml

  brokerStorage:
    storageClassName: zfs--rubin-efd
    size: 1.5Ti
    enabled: false
    migration:
      enabled: true
      rebalance: false


This configuration creates a new ``KafkaNodePool`` resource for the brokers using the new storage class.
Sync the new ``KafkaNodePool`` resource in Argo CD.

At this point, your data will still reside on the old brokers, and the new ones will be empty.
To move the data, use Cruise Control by setting ``brokerStorage.migration.rebalance: true`` and specifying the IDs of the old brokers — the ones you plan to remove after the migration.

.. code:: yaml

  brokerStorage:
    storageClassName: zfs--rubin-efd
    size: 1.5Ti
    enabled: false
    migration:
      enabled: true
      rebalance: true
      brokers:
        - 3
        - 4
        - 5

This action will create a new ``KafkaRebalance`` resource, which you’ll need to sync in Argo CD.

Next, wait for Cruise Control to execute the cluster rebalance.
You can check the state of the rebalance by inspecting the ``KafkaRebalance`` resource:

.. code:: bash

    $ kubectl get kafkarebalances.kafka.strimzi.io -n sasquatch
    NAME               CLUSTER     PENDINGPROPOSAL   PROPOSALREADY   REBALANCING   READY   NOTREADY   STOPPED
    broker-migration   sasquatch                                                   True

Finally, once the rebalancing state is ready, set ``brokerStorage.enabled: true`` and ``brokerStorage.migration.enabled: false`` and ``brokerStorage.migration.rebalance: false``.

Note that the PVCs of the old brokers need to be deleted manually, as they are orphan resources in Sasquatch.

Also, keep in mind that Strimzi will assign new broker IDs to the newly created brokers.
Ensure that you update the broker IDs wherever they are used, such as in the Kafka external listener configuration.


.. _Kafka Node Pools Storage & Scheduling: https://strimzi.io/blog/2023/08/28/kafka-node-pools-storage-and-scheduling/
