.. _sending-data:

########
Overview
########

In Sasquatch, data is sent to Kafka first and then to InfluxDB using the InfluxDB sink connector.

The Kafka REST Proxy is the recommended method for sending data to Sasquatch, especially for clients that are not ready to connect to Kafka and the Schema Registry.

This section discusses the Avro format and schema evolution.
It also shows how to use the Kafka REST Proxy API for sending data to Sasquatch.

You can reproduce the steps yourself to send data to an example topic to Sasquatch at USDF dev.

Then you can use the Kafdrop UI for browsing Kafka topics and view the messages.
