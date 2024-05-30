.. _sending-data:

########
Overview
########

In Sasquatch, data is sent initially to Kafka, a distributed streaming platform, where it acts as a centralized hub for data ingestion.
Subsequently, the data is routed from Kafka to InfluxDB, a high-performance time series database, utilizing the InfluxDB sink connector.

The recommended method for sending data to Sasquatch is through the Kafka REST Proxy API.
This method is particularly useful for clients that don't want to establish a direct connection to Kafka and the Schema Registry.

This section describes how Sasquatch uses namespaces, Avro schemas and provides a practical example on how to use the :ref:`Kafka REST Proxy <rest-proxy>` to send data to Sasquatch.

To gain hands-on experience, you can follow the step-by-step instructions outlined in this section.
By doing so, you will be able to send data to an example topic within Sasquatch, hosted at USDF dev environment.

To browse Kafka topics and visualize the messages being exchanged, you can utilize :ref:`Kafdrop <kafdrop-ui>`.