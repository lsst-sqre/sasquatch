.. _managing-shards:


######################################
Managing Shards in an InfluxDB Cluster
######################################

The InfluxDB storage engine organizes data into shards, which are logical partitions of the database that contain a subset of the data.
In the default Sasquatch configuration, the shard duration is 7 days, starting at 00:00:00.000 UTC on Sunday and ending at 23:59:59.999 UTC on the following Saturday.
An InfluxDB Enterprise cluster enables horizontal scaling and high availability by distributing shards across multiple data nodes.

This guide outlines the use of the `influxd-ctl`_ and `influx_inspect`_ tools to manage shards in an InfluxDB cluster.

Listing Shards
==============

The ``influxd-ctl`` tool is available on the InfluxDB Enterprise meta nodes.
To view all shards and their metadata use the ``influxd-ctl show-shards`` command.

.. code-block:: bash

    kubectl -n sasquatch exec -it sasquatch-influxdb-enterprise-meta-0  -- influxd-ctl show-shards

This command displays information about all shards in the cluster, including the shard ID, Database, Retention Policy, Replication status, Start time, End time, and Owners.

For example, the following command lists the shard IDs for the EFD database and the corresponding Start and End times:

.. code-block:: bash

    kubectl -n sasquatch exec -it sasquatch-influxdb-enterprise-meta-0 -- influxd-ctl show-shards | awk '$2 == "efd" { print $1, $2, $6, $7 }' | sort -k1,1n


In Sasquatch deployments, the InfluxDB cluster has replication factor two, meaning that each shard is replicated on two data nodes. 
The data nodes where the shards are stored is reported under the Owners column. 

Detailed information about the shards such as state (hot or cold), last modified time and size can be obtained by running the ``influxd-ctl show-shards -v`` command.

The `filesystem layout`_ of a data node is as follows:

.. code-block:: bash

    <data-dir>/<database>/<retention-policy>/<shard-id>

- ``<data-dir>``: The base directory for data storage, defined by the data configuration setting in the influxdb.conf file (``/var/lib/influxdb/data`` by default).
- ``<database>``: Each database has its own subdirectory under the data directory.
- ``<retention-policy>``: Within each database directory, there is a subdirectory for each retention policy.
- ``<shard-id>``: Shards are stored in directories named by their unique numeric shard ID.


Checking data integrity
=========================

To verify the integrity of a shard across the cluster, use the ``influx_inspect`` tool on a data node, e.g. ``sasquatch-influxdb-enterprise-data-0``:

.. code-block:: bash

    kubectl -n sasquatch exec -it sasquatch-influxdb-enterprise-data-0  -- influx_inspect verify -dir /var/lib/influxdb/data/<database>/<retention-policy>/<shard-id>


This command checks the integrity of the `Time-Structured Merge Tree (TSM)`_ files.

The same shard can differ in size across the cluster due to compaction and other operations. 
The ``influx_inspect verify`` command checks the integrity of the shard data, not the size.

Read more about shard compaction operations in the InfluxDB `storage engine`_ documentation. 

The `Anti-Entropy service`_ in InfluxDB Enterprise ensures that the data is consistent across the cluster by comparing the data in the shards on different data nodes. 
However, this tool is consumes too much resources and InfluxData recommends turning it off on small clusters like Sasquatch.

Shard movement
==============

Shard movement is the process of moving a shard from one data node to another. This operation is useful when a data node is decommissioned or when rebalancing the cluster.

The ``influxd-ctl`` tool provides commands to `move shards`_ between data nodes.

Read more about cluster `rebalancing`_ in the InfluxDB documentation.

Backup and restore
==================

The ``influxd-ctl`` tool provides commands to backup and restore shards. 

However, a meta node doesn't have enough space to keep the backup files so we need to download the tool
and bind it to a meta node to perform the backup and restore operations.

Download the ``influxd-ctl`` tool from the InfluxData website:

.. code-block:: bash

    wget https://dl.influxdata.com/enterprise/releases/influxdb-meta-1.11.3_c1.11.3-1.x86_64.rpm
    rpm2cpio influxdb-meta-1.11.3_c1.11.3-1.x86_64.rpm | cpio -idmv
    

To backup a shard, use the ``influxd-ctl backup`` command:

.. code-block:: bash

    influxd-ctl -bind  <meta pod IP address>:8091 backup -db efd -shard <shard ID>  /backup-dir


To restore a shard, use the ``influxd-ctl restore`` command:

.. code-block:: bash

    influxd-ctl -bind  <meta pod IP address>:8091 restore -db efd -shard <shard ID> -shard <shard ID> -newshard <new shard ID>  /backup-dir

Where ``<shard ID>`` identifies the shard to be restored from the backup and ``<new shard ID>`` identifies the shard in the destination database to restore to. 

.. note::

    If you are restoring a shard from the same database, ``<new shard ID>`` is the same as the ``<shard ID>``.  

    If you are restoring a shard from a different database (e.g. restoring data the Summit EFD database to the USDF EFD database) **shard IDs do not align**, and so ``<new shard ID>`` should reflect the shard ID in the destination database which has **the same same start time** as in the source database.

Hot shards should be truncated using the ``influxd-ctl truncate-shards`` command before backup and restore operations.

For a cold shard it is also possible to manually copy the shard TSM files to one of the destination data nodes under the appropriate directory, and then use the ``influxd-ctl copy-shards`` command to copy the shard to the other data node. 

This procedure was applied to restore shard 786 at the USDF EFD database, after InfluxData ran an offline compaction of the shard to fix a slow query issue. 
In this case the shard restore procedure is as follows:

.. code-block:: bash

    # List owners of shard 786
    kubectl exec -it sasquatch-influxdb-enterprise-meta-0 -n sasquatch -- influxd-ctl show-shards | grep 786

    # Remove shard 786 from the one of its owners (data-0):
    kubectl exec -it sasquatch-influxdb-enterprise-data-0 -n sasquatch -- /bin/bash
    cd /var/lib/influxdb/data/efd/autogen/
    rm -r 786 
         
    # Manually copy the fully compacted TSM files and the fields.idx file for shard 786 to data-0 under the appropriate directory
    kubectl -n sasquatch cp efd/autogen/786/  sasquatch-influxdb-enterprise-data-0:/var/lib/influxdb/data/efd/autogen/

    # Remove shard 786 from the other data node (data-1):
    kubectl exec -it sasquatch-influxdb-enterprise-meta-0 -n sasquatch -- influxd-ctl remove-shard sasquatch-influxdb-enterprise-data-1.sasquatch-influxdb-enterprise-data.sasquatch.svc.cluster.local:8088 786

    # Copy shard 786 from data-0 to data-1
    kubectl exec -it sasquatch-influxdb-enterprise-meta-0 -n sasquatch -- influxd-ctl copy-shard sasquatch-influxdb-enterprise-data-0.sasquatch-influxdb-enterprise-data.sasquatch.svc.cluster.local:8088 sasquatch-influxdb-enterprise-data-1.sasquatch-influxdb-enterprise-data.sasquatch.svc.cluster.local:8088 786

    # Finally restart the InfluxDB Enterprise data statefulset to reload the shards data and rebuild the TSM in-memory indexes.
 
.. note::

    Note the difference between removing the shard files manually and using the ``influxd-ctl remove-shard`` command. 
    The ``remove-shard`` command removes the shard from the meta node and the data node, while manually removing the shard files only removes the shard from the data node.


.. _influxd-ctl: https://docs.influxdata.com/enterprise_influxdb/v1/tools/influxd-ctl/
.. _influx_inspect: https://docs.influxdata.com/enterprise_influxdb/v1/tools/influx_inspect/
.. _storage engine: https://docs.influxdata.com/enterprise_influxdb/v1/concepts/storage_engine
.. _filesystem layout: https://docs.influxdata.com/enterprise_influxdb/v1/concepts/file-system-layout/
.. _Time-Structured Merge Tree (TSM): https://docs.influxdata.com/enterprise_influxdb/v1/concepts/
.. _Anti-Entropy service: https://docs.influxdata.com/enterprise_influxdb/v1/concepts/anti_entropy_service/
.. _move shards: https://docs.influxdata.com/enterprise_influxdb/v1/features/clustering-features/#shard-movement
.. _rebalancing: https://docs.influxdata.com/enterprise_influxdb/v1/administration/manage/clusters/rebalance/




