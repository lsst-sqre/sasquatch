.. _sending-data:

########
Overview
########

In Sasquatch, data is sent initially to Kafka, a distributed streaming platform, where it acts as a centralized hub for data ingestion.
Subsequently, the data is routed from Kafka to InfluxDB, a high-performance time series database, utilizing the InfluxDB sink connector.

For seamless integration and easy data transmission, the recommended approach to send data to Sasquatch is through the Kafka REST Proxy.
This method is particularly useful for clients that are not yet prepared to establish a direct connection with Kafka and its associated Schema Registry.

This section provides comprehensive insights into the concept of namespaces and highlights the significance of Avro within the context of Sasquatch.
Additionally, it illustrates the practical implementation of the :ref:`Kafka REST Proxy <rest-proxy>` API, demonstrating how it can be employed to efficiently send data to Sasquatch.

To gain hands-on experience and replicate the data transmission process, you can follow the step-by-step instructions outlined.
By doing so, you will be able to send data to an example topic within Sasquatch, hosted at USDF dev.
Furthermore, you can utilize :ref:`Kafdrop <kafdrop-ui>`, a user-friendly web-based interface, to browse Kafka topics and visualize the messages being exchanged.
