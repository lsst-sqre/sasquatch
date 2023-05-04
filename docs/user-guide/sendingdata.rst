.. _sending-data:

########
Overview
########

In Sasquatch, data is sent to Kafka first and then to InfluxDB using the InfluxDB sink connector.

The :ref:`Kafka REST Proxy <rest-proxy>` is the recommended method for sending data to Sasquatch, especially for clients that are not ready to connect to Kafka and the Schema Registry.

This section discusses namespaces and the role of Avro in Sasquatch.
It also shows how to use the :ref:`Kafka REST Proxy <rest-proxy>` API for sending data to Sasquatch.

You can reproduce the steps yourself to send data to an example topic to Sasquatch at USDF dev.
Then you can use :ref:`Kafdrop <kafdrop-ui>` for browsing Kafka topics and viewing the messages.
