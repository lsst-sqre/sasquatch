.. _sending-data:

########
Overview
########


In sasquatch, data is sent to Kafka first and then persisted in InfluxDB or another data store using off-the-shell Kafka connectors.

Sasquatch uses Avro format and the Confluent Schema registry to ensure schemas can evolve safely.

The Kafka REST Proxy is the recommended method for sending data to Sasquatch, specially for clients that are not ready to connect directly to Kafka and the Schema Registry.

Sasquatch provides the Kafdrop UI tool for browsing Kafka topics and viewing messages.
