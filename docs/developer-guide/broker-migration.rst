.. _broker-migration:

#######################################
Kafka broker migration to local storage
#######################################

From time to time, you might need to expand the size of the Kafka storage because your brokers need to handle more data, or you might need to migrate the kafka brokers to a different storage that uses a different storage class.

In Strimzi, each ``kafkaNodePool`` has its own storage configuration.
The first step for the broker migration is creating a new ``KafkaNodePool`` with the new storage configuration.
Once that's done you can use the Cruise Control tool and the Strimzi ``KafkaRebalance`` resource to move the data from the old brokers to the new brokers.

The procedure is outlined in the `Kafka Node Pools Storage & Scheduling`_ post adapted here to migrate the Kafka brokers originally deployed on the cluster default storage (usually a network attached storage) to local storage.

First make sure to enable Cruise Control in your Sasquatch Phalanx environment.
Look in ``sasquatch/values-<environment>.yaml`` for:

.. code:: yaml

  strimzi-kafka:
    cruiseControl:
      enabled: true

Then, specify the storage class for local storage and its size and set ``migration.enabled: true`` to start the migration.

.. code:: yaml

  localStorage:
    storageClassName: zfs--rubin-efd
    size: 1.5Ti
    enabled: false
    migration:
      enabled: true
      rebalance: false


This will create a new ``KafkaNodePool`` resource for the brokers on local storage.
Sync the new ``KafkaNodePool`` resource in Argo CD.

At this point, the data is still in the old brokers and the new ones are empty.
Now use Cruise Control to move the data by setting ``migration.rebalance: true`` and specifying the IDs of the old brokers, the ones to be removed after the migration.

.. code:: yaml

  localStorage:
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

This will create a new ``KafkaRebalance`` resource that needs to be synced in Argo CD.

Now, we have to wait until Cruise Control executes the cluster rebalance.
You can check state of the rebalance by looking at the ``KafkaRebalance`` resource:

.. code:: bash

    $ kubectl get kafkarebalances.kafka.strimzi.io -n sasquatch
    NAME               CLUSTER     PENDINGPROPOSAL   PROPOSALREADY   REBALANCING   READY   NOTREADY   STOPPED
    broker-migration   sasquatch                                                   True

Finally, once the rebalancing state is ready, set ``localStorage.enabled: true`` and ``migration.enabled: false`` and ``migration.rebalance: false``.

Note that the PVCs of the old brokers need to be deleted manually, as they are orphan resources in Sasquatch to prevent on-cascade deletion.

Also note that Strimzi will assign new broker IDs for the recently created brokers.
Make sure to update the broker IDs whenever they are used, for example, in the Kafka external listener configuration.


.. _Kafka Node Pools Storage & Scheduling: https://strimzi.io/blog/2023/08/28/kafka-node-pools-storage-and-scheduling/
