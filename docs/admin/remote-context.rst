
.. _remote-context:

##############
Remote Context
##############

The remote context feature introduces a clean separation between local and replicated Kafka topics, together with their associated Avro schemas.
It eliminates schema ID conflicts that previously prevented reliable two-way replication between Sasquatch environments, and enables Telegraf to consume replicated data safely.

To illustrate the concept, consider the Summit (source) → USDF (target) replication flow and the remote context components deployed at USDF.
The same principles apply in the reverse direction USDF (source) → Summit (target).

Remote topics
-------------

Remote context adopts the ``DefaultReplicationPolicy`` in MirrorMaker2, in which replicated topics are automatically prefixed with the source cluster name (e.g., ``summit`` for topics replicated from Summit).
This naming convention prevents topic name collision between local and replicated topics.
It also enables two-way replication avoiding infinite loops.

The topic prefix corresponds to the source cluster alias configured in MirrorMaker2 in the target cluster:

.. code:: yaml

  mirrormaker2:
    enabled: true
    source:
      alias: "summit"
      bootstrapServer: sasquatch-summit-kafka-bootstrap.lsst.codes:9094
      topicsPattern: "registry-schemas, foo.bar"
    replication:
      policy:
        separator: "."
        class: "org.apache.kafka.connect.mirror.DefaultReplicationPolicy"


Remote topics can be accessed in Kafdrop using a dedicated instance (Kafdrop Remote on ``/kafdrop-remote``) that restricts browsing to remote topics only.

Schema Isolation with a Remote Schema Registry
----------------------------------------------

Remote schemas are also replicated by MirrorMaker2, and stored in a separate schema topic prefixed with the source cluster name (e.g, ``summit.registry-schemas`` for schemas replicated from Summit).
This prevents schema ID conflicts between local and remote topic schemas.

Remote schemas are accessed using a dedicated Schema Registry instance (Schema Registry Remote on ``/schema-registry-remote``) configured to use the remote schema topic.

Telegraf configuration for remote topics
----------------------------------------

Telegraf connectors can be configured explicitly to consume remote topics using the remote Schema Registry.
For example, for the remote topic ``summit.foo.bar`` the Telegraf connector configuration would be as follows:

.. code:: yaml

  telegraf:
    enabled: true
    registry:
      url: "http://sasquatch-schema-registry-remote.sasquatch:8081"
    kafkaConsumers:
      foo-bar-remote:
        enabled: true
        database: "foo"
        topicRegexps: |
          [ "summit.foo.bar" ]

InfluxDB measurement name consistency
-------------------------------------

Kafka topics are mapped to InfluxDB measurements by Telegraf.

Even though the remote context uses a new naming convention for remote topics, InfluxDB measurement names must remain unchanged.
This ensures the InfluxDB queries work across the source and target environments.

For example, data sent to the ``foo.bar`` topic at the Summit and replicated to the ``summit.foo.bar`` topic at USDF is stored in the ``foo`` database and ``foo.bar`` measurement in InfluxDB in both environments.

The database name ``foo`` corresponds to the Sasquatch namespace in the source cluster.
See :ref:`namespaces` for more details.

Enabling remote context in a Sasquatch
--------------------------------------

Remote context is disabled by default in Sasquatch.
To enable it in a Sasquatch environment, follow these steps:

- Enable MirrorMaker2 in the target cluster to replicate the desired topics and schemas from the source cluster.
- The source cluster alias must match the source environment name (e.g., ``summit`` for Summit).
- Use the ``DefaultReplicationPolicy`` in MirrorMaker2.
- Enable the Kafdrop Remote and Schema Registry Remote instances in the target cluster.
- Configure Telegraf connectors to consume remote topics using the remote Schema Registry.
