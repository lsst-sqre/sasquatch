:og:description: Sasquatch Frequently Asked Question.

.. _faq:

FAQ
===

Do you need dedicated DevOps personnel to maintain Sasquatch? If so, how many?
------------------------------------------------------------------------------

Typically, 0.2 FTE (Full-Time Equivalent) is sufficient to maintain Sasquatch after deployment. 
Currently, we manage Sasquatch across five different environments (Kubernetes clusters) with less than 1 FTE.

How do you deploy Sasquatch on Kubernetes?
------------------------------------------

We developed our own internal developer platform `Phalanx`_ to manage application deployment configuration, including the Rubin Science Platform (RSP) and ancillary services. 

.. _Phalanx: https://phalanx.lsst.io

What is the throughput and number of simultaneous clients connecting to Sasquatch?
----------------------------------------------------------------------------------

- **Data Producers:** Approximately 65+ Control System Components (CSCs) grouped into ~20 connectors (writers) produce data at an estimated 10 MB/s during Rubin Observatory operations.
- **Data Consumers:** Users at the Summit control room view Chronograf dashboards, and engineers use the Rubin Science Platform (RSP) for querying InfluxDB via a Python client. Sasquatch data collected at the Summit is also replicated to USDF for project-wide availability.

How do you interact with InfluxDB?
----------------------------------

In addition to Chronograf, the EFD Python client is our primary tool for interacting with data stored in InfluxDB facilitating data analysis within the Rubin Science Platform (RSP).

Have you found a need for more InfluxDB tags usage? It seemed that Rubin Observatory wasn't using InfluxDB tags much for the EFD.
---------------------------------------------------------------------------------------------------------------------------------

Yes, we recently redesigned the InfluxDB schema for the LSST Camera to accommodate its hierarchical data structure (Camera, Raft, Sensor, Amplifier, etc)
This subsystem now uses many tags. You can view an `example configuration here`_.

.. _example configuration here: https://github.com/lsst-sqre/phalanx/blob/main/applications/sasquatch/values-summit.yaml#L184

For other subsystems, while the InfluxDB schema could be improved, query performance has been acceptable without extensive tag usage. 
Therefore, this has not been a priority.

What happens when an InfluxDB data node goes offline? Is all data available?
----------------------------------------------------------------------------

Yes, with an InfluxDB Cluster and replication factor set to two, all data is still available when a node goes offline.


How easy is it to add a storage node to expand capacity? Can this be done without downtime? 
-------------------------------------------------------------------------------------------

We use local storage for our InfluxDB cluster to enhance performance. 
Thus you can expand the InfluxDB cluster storage capacity by adding more data nodes while maintaining the data replication factor.

Once the new data nodes are available, you just increase the replica count configuration for data pods. 
This automatically registers the new cluster members, and thanks to the built-in high-availability (HA) configuration, this can be done without downtime.

Some considerations:
- Familiarity with the ``influxctl`` admin tool to manage shards in the cluster is required.
- InfluxDB Enterprise includes an `Anti-Entropy (AE)`_ service to ensure data consistency across replicas. 
This service must be turned off during manual shard restoration to avoid conflicts with the restore process.

.. _Anti-Entropy (AE): https://docs.influxdata.com/enterprise_influxdb/v1/administration/configure/anti-entropy/

We recommend using a replication factor of two for the cluster.
With a replication factor of two each shard is replicated across at least two nodes.
Adding more than two data nodes increases storage capacity, however not all nodes will hold the same shards. 

Chronograf and Kapacitor usage. How difficult is to create lots of dashboards? Did one team develop all dashboards, or was it distributed between other software teams? Learning curve remarks.
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

We use Chronograf for data visualization/exploration and Kapacitor for alerting. 
Here are our observations:

- Chronograf is intuitive and enables our users to create their own dashboards. While we provide guidance, each team is responsible for creating and maintaining their dashboards.
- Lack of a "dashboard as code" approach. While dashboards can be exported as JSON, editing or version-controlling them is challenging.
- In the Chronograf UI, dashboards are presented as a flat list without folder organization or labels, making it hard to browse 200+ dashboards at the Summit.
- Query results are not cached, so shared links hit the database multiple times.
- Kapacitor has been effective for creating alert rules and integrating with Slack notifications. Chronograf provides a user-friendly interface for this.
- Both dashboards and alerts are stored in respective databases, requiring backups. Programmatic creation is not yet supported.

**Future Plans:** We are evaluating **Grafana** and **Apache Superset** to address some of these limitations while continuing to use Chronograf for data exploration. 
We value Chronograf's query builder, which is easy to use and supports both InfluxQL and Flux.

How responsive is plotting look backs? How does this compare to Grafana?
--------------------------------------------------------------------------------

Chronograf is very responsive for long look backs.
Chronograf's ``:interval:`` template variable dynamically adjusts the time grouping in queries, ensuring smooth visualizations regardless of the time range.
It might be possible to implement similar functionality in Grafana using template variables, but we have not explored this yet.

Was it easy to maintain/interface/add to Kafka?
-----------------------------------------------

Kafka has a steep learning curve and a complex deployment setup with brokers, controllers, Kafka Connect, MirrorMaker 2, Schema Registry, etc.
The Strimzi Operator simplifies the deployment and management of Kafka on Kubernetes.

Our Kafka clients are mainly written in Python and Java. 
We also provide a REST API (Confluent's Kafka REST Proxy) for easier Kafka interfacing using HTTP clients.

How straightforward are Kafka or JVM upgrades? Any JVM-related issues?
----------------------------------------------------------------------

We use `Strimzi`_ to manage Kafka deployments on Kubernetes, which simplifies many administration tasks including upgrades. 

.. _Strimzi: https://sasquatch.lsst.io/developer-guide/index.html

No JVM-related issues have been encountered other than the usual memory tuning and garbage collection settings.

How are Kafka topics managed and accessed? 
------------------------------------------

Kafka topics have three replicas for fault tolerance. 
We disable topic auto creation in Kafka, thus each client must request topic creation.
While Kafka lacks native namespaces, we use a topic naming convention to group topics by subsystem.
Each client has a unique Kafka user with ACLs specifying accessible topics. 
