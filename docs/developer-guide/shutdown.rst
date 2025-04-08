.. _shutdown:

############################
Sasquatch shutdown procedure
############################

It is recommended that you shut down Sasquatch gracefully before cluster interventions like OS or Kubernetes upgrades.
The procedure in this guide assumes that you are Shutting down Sasquatch at the Summit, but it also applies to other environments with minor modifications.

Stop Clients
============

Before shutting down Kafka, you should stop all clients (producers and consumers) to prevent errors and potential data loss.

Stop the Control System producers and consumers at the Summit.

At the USDF environment, stop data replication from the Summit:

.. code:: bash

   kubectl delete kafkamirrormaker2 sasquatch -n sasquatch

this will remove the ``KafkaMirrorMaker2`` resources.


Stop the Telegraf connectors
----------------------------

At the Summit environment, use the following command to stop the Telegraf connectors, this will stop writes to InfluxDB.

.. code:: bash

  kubectl scale deploy -l app.kubernetes.io/name=sasquatch-telegraf --replicas=0 -n sasquatch

Stop the Schema Registry and Kafdrop
------------------------------------

To stop the Schema Registry and Kafdrop, scale down the respective deployments:

.. code:: bash

   kubectl scale deploy strimzi-registry-operator --replicas=0 -n sasquatch
   kubectl scale deploy sasquatch-schema-registry --replicas=0 -n sasquatch
   kubectl scale deploy sasquatch-kafdrop --replicas=0 -n sasquatch


Ensure that all clients are stopped before proceeding.
One way to do that is looking into the following kafka metrics:

- ``kafka_server_socket_server_metrics_connection_count`` The current number of active connections
- ``kafka_server_brokertopicmetrics_bytesin_total`` The total number of bytes received (produced)
- ``kafka_server_brokertopicmetrics_bytesout_total`` The total number of bytes sent (consumed)

If the metrics are not zero, it means that there are still active connections and data being consumed/produced to Kafka.

Stop Strimzi Kafka
==================

To stop Kafka gracefully, follow these steps:

1. Pause reconciliation of the Strimzi resources.

   This will prevent the Strimzi operator from reconcile its resources after they are deleted.

   .. code:: bash

      kubectl annotate --overwrite Kafka sasquatch strimzi.io/pause-reconciliation="true" -n sasquatch
      kubectl annotate --overwrite KafkaConnect sasquatch strimzi.io/pause-reconciliation="true" -n sasquatch

2. Scale down Cruise Control and the Entity Operator Deployments

   .. code:: bash

      kubectl scale deploy sasquatch-cruise-control --replicas=0 -n sasquatch
      kubectl scale deploy sasquatch-entity-operator --replicas=0 -n sasquatch

3. Delete Kafka Connect, Controller and Broker Pods

   At the Summit environment Kafka runs on local storage, so use the following command:

   .. code:: bash

      kubectl delete StrimziPodSet sasquatch-connect sasquatch-controller sasquatch-kafka-local-storage -n sasquatch

   Otherwise, use this command instead:

   .. code:: bash

      kubectl delete StrimziPodSet sasquatch-connect sasquatch-controller sasquatch-kafka -n sasquatch


After the intervention, remember to resume reconciliation of Strimzi resources.
This will allow the Strimzi operator to create the Pods again.

.. code:: bash

   kubectl annotate --overwrite Kafka sasquatch strimzi.io/pause-reconciliation="false" -n sasquatch
   kubectl annotate --overwrite KafkaConnect sasquatch strimzi.io/pause-reconciliation="false" -n sasquatch


Stop Chronograf and kapacitor
=============================

To stop Chronograf and Kapacitor, scale down the respective deployments:

.. code:: bash

   kubectl scale deploy sasquatch-chronograf --replicas=0 -n sasquatch
   kubectl scale deploy sasquatch-kapacitor --replicas=0 -n sasquatch


Stop InfluxDB
=============

The Summit environment runs InfluxDB Enterprise and OSS, scale down the corresponding stateful sets:

For InfluxDB Enterprise:

.. code:: bash

   kubectl scale sts sasquatch-influxdb-enterprise-data --replicas=0 -n sasquatch
   kubectl scale sts sasquatch-influxdb-enterprise-meta --replicas=0 -n sasquatch


For InfluxDB OSS:

.. code:: bash

   kubectl scale sts sasquatch-influxdb --replicas=0 -n sasquatch


