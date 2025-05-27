.. _directconnection:

############################
Connecting directly to Kafka
############################

In some cases, you need to connect directly to Kafka to produce and consume messages (vs. going through the :ref:`rest-proxy`), like when publishing app metrics events, or when developing a `FastStream`_ app.
This requires generating Kafka client credentials for the Sasquatch Kafka cluster and providing them to your app.

Kafka provides `many different authentication options <https://docs.confluent.io/platform/current/security/authentication/overview.html>`__.
This guide describes the the most secure and straightforward option, assuming that your app is running in the same Kubernetes cluster as the Sasquatch Kafka cluster.

.. _FastStream: https://faststream.airt.ai/latest/

Generating Kafka credentials
============================

.. note::

   The ``strimzi-access-operator`` `Phalanx`_ app must be enabled.
   It provides the ``KafkaAccess`` CRD that is used in this guide.

You can generate Kafka credentials by creating a couple of `Strimzi`_ resources:

* A `KafkaUser`_ resource, in the ``sasquatch`` namespace, to configure a user in the Kafka cluster and provision a Kubernetes Secret with that user's credentials
* A `KafkaAccess`_ resource, in your app's namespace, to make those credentials and other Kafka connection information available to your app

.. _Phalanx: https://phalanx.lsst.io
.. _Strimzi: https://strimzi.io
.. _KafkaUser: https://strimzi.io/docs/operators/latest/configuring.html#type-KafkaUser-reference
.. _KafkaAccess: https://github.com/strimzi/kafka-access-operator

Strimzi KafkaUser resource
--------------------------

Here's an example of a ``KafkaUser``, placed in the ``sasquatch`` namespace, with some of the common ACL rules you may want (more details about ACLs `here <https://docs.confluent.io/platform/current/security/authorization/acls/overview.html>`__):

.. code-block:: yaml

   apiVersion: kafka.strimzi.io/v1beta2
   kind: KafkaUser
   metadata:
     name: myapp
     labels:
       # The name of the Strimzi ``Kafka`` resource, probably "sasquatch"
       strimzi.io/cluster: sasquatch
   spec:
     authentication:
       # This should always be "tls"
       type: tls

     authorization:
       type: simple
       acls:

         # If your app consumes messages, this gives permission to consume as
         # part of any consumer group that starts with the named prefix.
         - resource:
             type: group
             name: "lsst.square-events.myapp"
             patternType: prefix
           operations:
             - "Read"
           host: "*"

         # If you app needs to create/delete topics, you can scope the
         # operations to a prefix.
         - resource:
             type: topic
             name: "lsst.square.metrics.myapp"
             patternType: prefix
           host: "*"
           operations:
             - All

         # If you just need to read and/or write to an existing topic, you
         # just need "Describe", and "Read" and/or "Write" operations.
         - resource:
             type: topic
             name: "lsst.square-events.myapp.ingest"
             patternType: literal
           operations:
             - "Describe"
             - "Read"
             - "Write"

Strimzi KafkaAccess resource
----------------------------

Next, you need a ``KafkaAccess`` resource in your app's namespace, which will automatically generate a ``Secret`` in your app's namespace with credentials from the user that you just created.
That will look something like this:

.. code-block:: yaml

   apiVersion: access.strimzi.io/v1alpha1
   kind: KafkaAccess
   metadata:
     name: myapp-kafka
   spec:
     kafka:
       # The name and namespace of the Strimzi ``Kafka`` resource, probably
       # "sasquatch"
       name: sasquatch
       namespace: sasquatch
       # This should always be "tls"
       listener: tls
     user:
       kind: KafkaUser
       apiGroup: kafka.strimzi.io
       # This is the name of the ``KafkaUser`` that you created
       name: myapp
       # This is the namespace of the ``KafkaUser``, NOT your app's namespace,
       # probably "sasquatch"
       namespace: sasquatch

Providing Kafka credentials to your app
=======================================

Once you have a ``Secret`` with auth TLS credentials in your app's namespace, you can mount that secret into your app's container, and provide connection and auth info as environment variables.
If your app is a `Safir`_ app, you can use the `Safir Kafka helpers <https://safir.lsst.io/user-guide/kafka.html>`__ to construct a Kafka client.

.. code-block:: yaml

   apiVersion: apps/v1
   kind: Deployment
   metadata:
    ...
     name: myapp
     namespace: myapp
   spec:
     ...
     template:
       ...
       spec:
         containers:
         - env:
           - name: KAFKA_SECURITY_PROTOCOL
               secretKeyRef:
                 key: securityProtocol
                 name: myapp-kafka
           - name: KAFKA_BOOTSTRAP_SERVERS
             valueFrom:
               secretKeyRef:
                 key: bootstrapServers
                 name: myapp-kafka
           - name: KAFKA_CLUSTER_CA_PATH
             value: /etc/kafkacluster/ca.crt
           - name: KAFKA_CLIENT_CERT_PATH
             value: /etc/kafkauser/user.crt
           - name: KAFKA_CLIENT_KEY_PATH
             value: /etc/kafkauser/user.key

           ...

           volumeMounts:
           - mountPath: /etc/kafkacluster/ca.crt
             name: kafka
             subPath: ssl.truststore.crt
           - mountPath: /etc/kafkauser/user.crt
             name: kafka
             subPath: ssl.keystore.crt
           - mountPath: /etc/kafkauser/user.key
             name: kafka
             subPath: ssl.keystore.key

         ...

         volumes:
         - name: kafka
           secret:
             defaultMode: 420
             # The ``metadata.name`` value from the ``KafkaAccess`` resource in
             # your app's namespace
             secretName: myapp-kafka

.. _Safir: https://safir.lsst.io
