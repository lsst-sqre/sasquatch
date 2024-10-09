.. _kafka-shutdown:


#########################
Shutdown Kafka gracefully
#########################

It is recommended that you shut down Kafka gracefully before cluster interventions like OS or Kubernetes upgrades.
To shut down Kafka gracefully, follow these steps:

1. Pause reconciliation of Strimzi resources.
   This will prevent the operator from restarting the pods after they are deleted.

   .. code:: bash

      kubectl annotate --overwrite Kafka sasquatch strimzi.io/pause-reconciliation="true" -n sasquatch
      kubectl annotate --overwrite KafkaConnect sasquatch strimzi.io/pause-reconciliation="true" -n sasquatch

2. Shut down Kafka and KafkaConnect pods.

   .. code:: bash

      kubectl delete StrimziPodSet sasquatch-connect sasquatch-controller sasquatch-kafka -n sasquatch

3. After the intervention, resume reconciliation of Strimzi resources.
   This will allow the operator to restart the pods.

   .. code:: bash

      kubectl annotate --overwrite Kafka sasquatch strimzi.io/pause-reconciliation="false" -n sasquatch
      kubectl annotate --overwrite KafkaConnect sasquatch strimzi.io/pause-reconciliation="false" -n sasquatch
