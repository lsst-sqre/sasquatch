.. _kafka-shutdown:


#########################
Shutdown Kafka gracefully
#########################

This guide provides instructions to shut down Sasquatch Kafka as gracefully as possible before cluster interventions like OS or Kubernetes upgrades.
To do so, follow these steps:

1. Scale sasquatch-schema-registry replicas to 0.

   .. code:: bash

      kubectl scale deployment sasquatch-schema-registry --replicas=0 -n sasquatch

2. Scale telegraf connectors to 0.

   .. code:: bash

      kubectl scale deploy -n sasquatch --selector app.kubernetes.io/name=sasquatch-telegraf --replicas=0

3. Pause reconciliation of Strimzi resources.
   This will prevent the operator from restarting the pods after they are deleted.

   .. code:: bash

      kubectl annotate --overwrite Kafka sasquatch strimzi.io/pause-reconciliation="true" -n sasquatch

4. Terminate the Kafka Broker Pods. Ensure all brokers are stopped before proceeding.

   .. code:: bash

      kubectl delete StrimziPodSet sasquatch-kafka-local-storage -n sasquatch

5. Terminate the Kafka Controller Pods.

   .. code:: bash

      kubectl delete StrimziPodSet sasquatch-controller -n sasquatch

6. After the intervention, resume reconciliation of Strimzi resources.
   This will trigger the operator to start the Pods again.

   .. code:: bash

      kubectl annotate --overwrite Kafka sasquatch strimzi.io/pause-reconciliation="false" -n sasquatch

7. Wait for the brokers to be up and healthy, then scale up the schema registry.

   .. code:: bash

      kubectl scale deployment sasquatch-schema-registry --replicas=3 -n sasquatch

8. Finally, scale up the telegraf connectors to get data back into the EFD.

   .. code:: bash

      kubectl scale deploy -n sasquatch --selector app.kubernetes.io/name=sasquatch-telegraf --replicas=1

