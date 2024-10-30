################################
Deploying into a new environment
################################

Deploying Sasquatch into a new environment requires multiple ArgoCD syncs with some manual information gathering and updating in between.


Enable Sasquatch in Phalanx
===========================

#. Cut a `Phalanx`_ development branch.
#. Ensure the ``strimzi`` and ``strimzi-access-operator`` Phalanx applications are enabled and synced in the new environment by adding them to the :samp:`environments/values-{environment}.yaml` file, and adding a blank :samp:`values-{environment}.yaml` file to their ``applications/`` directories.
   `These docs <https://phalanx.lsst.io/developers/switch-environment-to-branch.html>`_ can help you enable them from your development branch.
#. Enable the ``sasquatch`` app in the environment.
   For the :samp:`applications/sasquatch/values-{environment}.yaml` file, copy one from an existing environment that has the same enabled services that you want in the new environment.
   Change all of the environment references to the new environment, and change or add anything else you need for the new environment.
#. Comment out any ``loadBalancerIP`` entries in the :samp:`applications/sasquatch/values-{environment}.yaml` file.
   We'll fill these in later.
#. In the new environment's ArgoCD, point the ``sasquatch`` app at your Phalanx development branch, and sync it.

This first sync will not be successful.
The `cert-manager`_ ``Certificate`` resource will be stuck in a progressing state until we update some values and provision some DNS.

.. _Phalanx: https://phalanx.lsst.io
.. _cert-manager: https://cert-manager.io/

Gather IP addresses and update Phalanx config
=============================================

.. note::

   The public IP address gathering and modification described here only applies to environments deployed on `GCP`_.
   This process will be different for other types of environments.

#. Get the broker ids, which are the node ids of the the kafka brokers.
   In this example, the broker ids are ``0``, ``1``, and ``2``:

   .. code::

      ❯ kubectl get kafkanodepool -n sasquatch
      NAME         DESIRED REPLICAS   ROLES            NODEIDS
      controller   3                  ["controller"]   [3,4,5]
      kafka        3                  ["broker"]       [0,1,2]

#. A GCP public IP address will be provisioned for each of these broker nodes.
   Another IP address will be provisioned for the external `kafka bootstrap servers`_ endpoint.
   You can see all of the provisioned ip addresses in your GCP project here: :samp:`https://console.cloud.google.com/networking/addresses/list?authuser=1&hl=en&project={project name}`:

   .. figure:: /_static/gcp_ip_addresses.png
      :name: GCP IP addresses

#. One by one, click on the ``Forwarding rule`` links in each row until you find the ones annotated with :samp:`\{"kubernetes.io/service-name":"sasquatch/sasquatch-kafka-{broker node id}"\}` for each broker node.
   Note the ip address and node number.

   .. figure:: /_static/forwarding_rule_details.png
      :name: Forwarding rule details

#. Find and note the IP address that is annotated with ``{"kubernetes.io/service-name":"sasquatch/sasquatch-kafka-external-bootstrap"}``:

   .. figure:: /_static/bootstrap_forwarding_rule.png
      :name: Bootstrap forwarding rule

#. Promote all of these IP addresses to GCP Static IP Addresses by choosing the option in the three-vertical-dots menu for each IP address (you may have to scroll horrizontally).
   This makes sure that we won't lose these IP addresses and have to update DNS later:

   .. figure:: /_static/promote_ip_address.png
      :name: Promote IP address

#. Update the :samp:`applications/sasquatch/values-{environment}.yaml` ``strimzi-kafka.kafka`` config with ``loadBalancerIP`` and ``host`` entries that correspond with the node ids that you found.
   Here is an example from ``idfint``.
   Note that the broker node ids are in the ``broker`` entries, and that the ``host`` entries have numbers in them that match the those ids.

   .. code:: yaml

      strimzi-kafka:
        kafka:
          externalListener:
            tls:
              enabled: true
            bootstrap:
              loadBalancerIP: "35.188.187.82"
              host: sasquatch-int-kafka-bootstrap.lsst.cloud

            brokers:
              - broker: 0
                loadBalancerIP: "34.171.69.125"
                host: sasquatch-int-kafka-0.lsst.cloud
              - broker: 1
                loadBalancerIP: "34.72.50.204"
                host: sasquatch-int-kafka-1.lsst.cloud
              - broker: 2
                loadBalancerIP: "34.173.225.150"
                host: sasquatch-int-kafka-2.lsst.cloud

#. Push these changes to your Phalanx branch and sync ``sasquatch`` in ArgoCD.

.. _GCP: https://cloud.google.com
.. _kafka bootstrap servers: https://kafka.apache.org/documentation/#producerconfigs_bootstrap.servers

Provision DNS for TLS certificate
=================================

#. Provision ``CNAME`` records (probably in AWS Route53) for `LetsEncrypt`_ verification for each of the ``host`` entries in the ``strimzi-kafka.kafka`` values.
   Continuing with the ``idfint`` example:

   .. code:: text

      _acme-challenge.sasquatch-int-kafka-0.lsst.cloud (_acme-challenge.tls.lsst.cloud)
      _acme-challenge.sasquatch-int-kafka-1.lsst.cloud (_acme-challenge.tls.lsst.cloud)
      _acme-challenge.sasquatch-int-kafka-2.lsst.cloud (_acme-challenge.tls.lsst.cloud)
      _acme-challenge.sasquatch-int-kafka-bootstrap.lsst.cloud (_acme-challenge.tls.lsst.cloud)

#. Provision ``A`` records for each of the ``host`` entries with their matching IP address values:

   .. code:: text

      sasquatch-int-kafka-0.lsst.cloud (34.171.69.125)
      sasquatch-int-kafka-1.lsst.cloud (34.72.50.204)
      sasquatch-int-kafka-2.lsst.cloud (34.173.225.150)
      sasquatch-int-kafka-bootstrap.lsst.cloud (35.188.187.82)

#. Wait for the ``Certificate`` Kubernetes resource to provision in ArgoCD! This might take several minutes

.. _LetsEncrypt: https://letsencrypt.org

Configure Gafaelfawr OIDC authentication
========================================

Sasquatch assumes that Chronograf will use OIDC authentication.
Follow `these instructions <https://gafaelfawr.lsst.io/user-guide/openid-connect.html#chronograf>`_ to set it up.

.. warning::

   This requires a Gafaelfawr restart.
   It could also affect all of the apps in an environment if done incorrectly.
   If your new environment is a production environment, you should probably wait for a maintenance window to do this step!

Merge your Phalanx branch!
==========================

If all is well, of course.
