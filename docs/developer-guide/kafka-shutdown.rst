.. _kafka-shutdown:


#########################
Shutdown Kafka gracefully
#########################

This guide provides instructions to shut down Sasquatch Kafka gracefully before cluster interventions like OS or Kubernetes upgrades.
To shut down Kafka gracefully, follow these steps:

1. Pause reconciliation of Strimzi resources.
   This will prevent the operator from restarting the pods after they are deleted.

   .. code:: bash

      kubectl annotate --overwrite Kafka sasquatch strimzi.io/pause-reconciliation="true" -n sasquatch

2. Terminate the Kafka Controller and Broker Pods.

   .. code:: bash

      kubectl delete StrimziPodSet sasquatch-controller sasquatch-kafka-local-storage -n sasquatch

3. After the intervention, resume reconciliation of Strimzi resources.
   This will trigger the operator to start the Pods again.

   .. code:: bash

      kubectl annotate --overwrite Kafka sasquatch strimzi.io/pause-reconciliation="false" -n sasquatch
