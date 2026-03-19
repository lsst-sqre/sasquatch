.. _kafka-shutdown:


#########################
Shutdown Kafka gracefully
#########################

This guide provides instructions to shut down Sasquatch Kafka as gracefully as possible before cluster interventions like OS or Kubernetes upgrades.
To do so, follow these steps:

1. Pause reconciliation of Strimzi resources.
   This will prevent the operator from restarting the pods after they are deleted.

   .. code:: bash

      kubectl annotate --overwrite Kafka sasquatch strimzi.io/pause-reconciliation="true" -n sasquatch

2. Terminate the Kafka Broker Pods. Ensure all brokers are stopped before proceeding.

   .. code:: bash

      kubectl delete StrimziPodSet sasquatch-kafka-local-storage -n sasquatch

3. Terminate the Kafka Controller Pods.

   .. code:: bash

      kubectl delete StrimziPodSet sasquatch-controller -n sasquatch

4. After the intervention, resume reconciliation of Strimzi resources.
   This will trigger the operator to start the Pods again.

   .. code:: bash

      kubectl annotate --overwrite Kafka sasquatch strimzi.io/pause-reconciliation="false" -n sasquatch
