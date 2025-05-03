.. _backups:

##################
Backup and restore
##################

Sasquatch supports scheduled backups of key services (e.g., Chronograf, Kapacitor, InfluxDB OSS and InfluxDB Enterprise) via a Kubernetes CronJob.
Backup data is stored using a persistent volume and managed via retention policies.

This guide describes how to enable and configure scheduled backups in Sasquatch using the backup subchart.

Enabling Backup Items
=====================

Edit your ``values-<environment>.yaml`` file to enable the services you wish to back up.
Only enabled items will be included in the scheduled backup job.

For example, to back up InfluxDB OSS, Chronograf, and Kapacitor update the ``backupItems`` section:

.. code-block:: yaml

  backup:
    enabled: true
    backupItems:
      - name: "chronograf"
        enabled: true
        retentionDays: 7
      - name: "kapacitor"
        enabled: true
        retentionDays: 7
      - name: "influxdb-enterprise-incremental"
        enabled: false
      - name: "influxdb-oss-full"
        enabled: true
        retentionDays: 3

The enabled items are passed to the `backup script`_ for execution.

Configure Backup Schedule
=========================

Set the ``schedule`` value using standard `cron syntax <https://en.wikipedia.org/wiki/Cron>`_. For example, to run backups daily at 3:00 AM:

.. code-block:: yaml

  backup:
    enabled: true
    schedule: "0 3 * * *"

Persistent Storage Configuration
================================

Ensure the backup job has persistent storage to retain backup files.
You can configure size and storage class:

.. code-block:: yaml

  backup:
    enabled: true
    persistence:
      enabled: true
      size: "100Gi"         # Size of the PVC
      storageClass: ""      # Use the cluster default, or specify your own (e.g., "standard")

If not provided, defaults will be used (``100Gi`` size, default storage class).


Verifying a Backup
==================

Once deployed, you can check the CronJob and logs:

.. code-block:: bash

   kubectl get cronjob/sasquatch-backup -n sasquatch
   kubectl get job -n sasquatch
   kubectl logs job/sasquatch-backup-29102580 -n sasquatch

Backups will be stored on the configured persistent volume and managed according to their retention policies.

Suspending a Backup
===================

If you need to temporarily disable the execution of the backup CronJob without deleting it, you can suspend it using the following command:

.. code-block:: bash

   kubectl patch cronjob sasquatch-backup -n sasquatch -p '{"spec" : {"suspend" : true }}'

To resume the job later:

.. code-block:: bash

   kubectl patch cronjob sasquatch-backup -n sasquatch -p '{"spec" : {"suspend" : false }}'

This is useful when running a restore command that might take longer that the scheduled window to prevent a new backup job from writing to the backup volume.


Restoring from a Backup
=======================

You can manually restore from the backup files stored in the persistent volume.
To restore a backup, you can enable the restore deployment.

.. code-block:: yaml

   restore:
     enabled: true

This creates a deployment that mount backup volume giving you access to the backup files in the ``/backup`` directory.
You can then use the backup files to restore the services.

Restoring from a Chronograf backup
==================================

All Chronograf data is stored in a BoltDB file, including configurations and dashboards.

To restore a Chronograf BoltDB file, choose the backup file you want to restore from and copy it to the Chronograf Pod you want to restore to.

.. code-block:: bash

   kubectl -n sasquatch cp <BoltDB file> <chronograf pod>:/var/lib/chronograf/

Example:

.. code-block:: bash

   # Copy the backup file to the Chronograf Pod
   kubectl -n sasquatch cp manke-chronograf-2025-02-02/chronograf-v1.db sasquatch-chronograf-5f4778478f-9zhjx:/var/lib/chronograf/

Then restart the Chonograf deployment to load the new DB.

Restoring from a Kapacitor backup
=================================

Kapacitor also stores all its data in a BoltDB file, including configurations and alert rules.

To restore a Kapacitor BoltDB file, choose the backup file you want to restore from and copy it to the Kapacitor Pod you want to restore to.

.. code-block:: bash

   kubectl -n sasquatch cp <BoltDB file> <kapacitor pod>:/var/lib/kapacitor/

Example:

.. code-block:: bash

   # Copy the backup file to the Kapacitor Pod
   kubectl -n sasquatch cp manke-kapacitor-2025-02-02/kapacitor.db sasquatch-kapacitor-5cc8776957-t8c9x:/var/lib/kapacitor/

Then restart the Kapacitor deployment to load the new DB.

Restoring from an InfluxDB Enterprise Incremental backup
========================================================

To restore from InfluxDB Enterprise incremental backups, you can either execute directly from the Sasquatch restore Pod or run a dedicated Kubernetes Job for long-running restores.

Executing into the Sasquatch Restore Pod
----------------------------------------

If the Sasquatch restore deployment is enable, you can exec into the restore Pod:

.. code-block:: bash

   kubectl exec -it <sasquatch restore pod> -n sasquatch -- /bin/sh

Then run the restore command.
See the `InfluxDB Enterprise documentation`_ for more details on the restore command.

Creating a Restore Job
----------------------

For long-running restores, define a Kubernetes Job:

.. code-block:: yaml

   apiVersion: batch/v1
   kind: Job
   metadata:
     name: sasquatch-restore-job
     namespace: sasquatch
   spec:
     template:
       spec:
         serviceAccountName: sasquatch-backup
         restartPolicy: Never
         securityContext:
           runAsNonRoot: true
           runAsUser: 1000
           runAsGroup: 1000
           fsGroup: 1000
         volumes:
         - name: backup
           persistentVolumeClaim:
             claimName: sasquatch-backup
         containers:
         - name: sasquatch-backup
           image: ghcr.io/lsst-sqre/sasquatch:1.3.0
           imagePullPolicy: IfNotPresent
           volumeMounts:
           - name: backup
             mountPath: /backup
           command:
           - /bin/sh
           - -c
           - >
             influxd-ctl -bind sasquatch-influxdb-enterprise-standby-meta:8091
             restore -db efd backup/sasquatch-influxdb-enterprise-backup/
     backoffLimit: 1

Apply it with:

.. code-block:: bash

   kubectl apply -f restore-job.yaml

You can monitor the Job with:

.. code-block:: bash

   kubectl get job -n sasquatch
   kubectl logs job/sasquatch-restore-job -n sasquatch

Once the restore is complete, the Job will terminate and its Pod can be cleaned up.

.. _backup script: https://github.com/lsst-sqre/sasquatch/blob/main/backup/backup.sh
.. _InfluxDB Enterprise documentation: https://docs.influxdata.com/enterprise_influxdb/v1/administration/backup-and-restore/
