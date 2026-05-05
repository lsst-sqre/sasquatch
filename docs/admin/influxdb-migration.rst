.. _influxdb-migration:

###########################
InfluxDB database migration
###########################

This guide describes how to migrate an InfluxDB database from a Sasquatch
backup with the ``sasquatch influxdb migrate`` commands.

A typical use case is changing the database schema, for example dropping or renaming an InfluxDB measurement, tag, or field.

Another use case is fixing series cardinality issues in InfluxDB.
This involves changing the database schema, for example, dropping tags that have too many values and converting them into fields if possible.

In these situations, the challenge is to migrate the historical data from an old database (old schema) to the new database (new schema).
There is no official tool for doing such database migrations, and the community consensus is basically to export the database to line protocol format, transform the data and re-import it.

The ``sasquatch influxdb migrate`` commands can also be used to migrate data from one InfluxDB server to another. However, if you are not changing the database schema and just want to copy data from one InfluxDB server to another, consider using the InfluxDB backup/restore tools  instead of the migration workflow described here. The backup/restore tools are more efficient than working with line protocol files.

The database migration workflow as implemented in Sasquatch has four phases:

#. Discover the TSM files to migrate from a database backup.
#. Export those TSM files to line protocol.
#. Transform the exported line protocol files if needed.
#. Import the transformed data into the target InfluxDB instance.

.. note::

  Keep in mind that the import phase will write data into an existing database.
  Make sure that you are importing into the correct database to prevent accidental
  imports. If there are any transformations in the migration plan that change the
  database schema, use the ``--target-database`` option during import to specify
  a different database than the source database.


Running migration commands
==========================

You can manually run migration commands.
To run a migration, first you need to enable the migration deployment in
``values-<environment>.yaml``:

.. code-block:: yaml

  influxdb-migration:
    enabled: true

This creates a deployment that mounts the backup volume, giving you access
to the backup files in the ``/backup`` directory.

You can exec into the migration Pod:

.. code-block:: bash

   kubectl exec -it <sasquatch migration pod> -n sasquatch -- /bin/sh


Discover source shards
======================

Start by creating a migration run directory and discovering the shards you
want to migrate:

.. code-block:: bash

   $ sasquatch influxdb migrate discover --backup-dir /backup/sasquatch-influxdb-oss-full-20260424T050007Z --database lsst.square.metrics --retention autogen --run-dir /backup/test-migration-1 --shard 986 --shard 997 --shard 1052
   Discovered 8 TSM file(s) in 3 shard(s).

.. note::

   In a typical migration, use ``--all-shards`` during discovery so
   Sasquatch reads the backup manifest and includes every shard for the
   selected database and retention policy. This example uses repeated
   ``--shard`` options only to illustrate how to migrate a small, explicit
   shard subset.

Check the migration status:

.. code-block:: text

   $ sasquatch influxdb migrate status --run-dir /backup/test-migration-1/
   Migration run: lsst.square.metrics / autogen
   Run ID: b0becae5428e
   Backup: sasquatch-influxdb-oss-full-20260424T050007Z
   Mode: explicit
   Manifest status: discovered
   Created: 2026-05-04T18:33:21.855030+00:00
   Updated: 2026-05-04T18:33:21.855287+00:00

   Overall:
     Shards: 3
     Files: 8
     Exported: 0/8
     Transformed: 0/8
     Imported: 0/8
     Error files: 0

   Shard progress:
     Shard  Files  Exported  Transformed  Imported  State
     986    1/1    0/1         0/1            0/1         discovered
     997    1/1    0/1         0/1            0/1         discovered
     1052   6/6    0/6         0/6            0/6         discovered


Export to line protocol
=======================

Export the discovered TSM files into line protocol files under the run
directory:

.. code-block:: bash

   $ sasquatch influxdb migrate export --run-dir /backup/test-migration-1/
   Exported 8 file(s).

.. note::

   Use ``--force`` with ``sasquatch influxdb migrate export`` to re-export
   files that are already marked as exported in the manifest. This is useful
   when you want to regenerate line protocol files in an existing run
   directory.

.. code-block:: text

   $ sasquatch influxdb migrate status --run-dir /backup/test-migration-1/
   Migration run: lsst.square.metrics / autogen
   Run ID: b0becae5428e
   Backup: sasquatch-influxdb-oss-full-20260424T050007Z
   Mode: explicit
   Manifest status: exported
   Created: 2026-05-04T18:33:21.855030+00:00
   Updated: 2026-05-04T18:35:49.770125+00:00

   Overall:
     Shards: 3
     Files: 8
     Exported: 8/8
     Transformed: 0/8
     Imported: 0/8
     Error files: 0

   Shard progress:
     Shard  Files  Exported  Transformed  Imported  State
     986    1/1    1/1         0/1            0/1         exported
     997    1/1    1/1         0/1            0/1         exported
     1052   6/6    6/6         0/6            0/6         exported

The export phase produces line protocol only, so the exported files are ready
for inspection and transformation before import.


Inspect exported data
=====================

Use the ``line-protocol`` commands to inspect one of the exported files.
For example, to show the tag keys present in one file:

.. code-block:: bash

   $ sasquatch influxdb line-protocol show-tags test-migration-1/1052/000000001-000000001.lp

.. code-block:: text

   lsst.square.metrics.events.gafaelfawr.active_user_sessions: application
   lsst.square.metrics.events.gafaelfawr.active_user_tokens: application
   lsst.square.metrics.events.gafaelfawr.auth_bot: application, service, username
   lsst.square.metrics.events.gafaelfawr.login_attempt: application
   lsst.square.metrics.events.gafaelfawr.rate_limit: application, service, username
   lsst.square.metrics.events.mobu.muster: application, business, flock, success, username
   lsst.square.metrics.events.mobu.notebook_cell_execution: application, business, flock, notebook, repo, success, username
   lsst.square.metrics.events.mobu.notebook_execution: application, business, flock, notebook, repo, success, username
   lsst.square.metrics.events.mobu.nublado_delete_: application, business, flock, success, username
   lsst.square.metrics.events.mobu.nublado_spawn_lab: application, business, flock, success, username
   lsst.square.metrics.events.mobu.sia_query: application, business, flock, success, username
   lsst.square.metrics.events.mobu.tap_query: application, business, flock, success, sync, username
   lsst.square.metrics.events.noteburst.arq_job_run: application, queue
   lsst.square.metrics.events.noteburst.arq_queue_stats: application, queue
   lsst.square.metrics.events.nublado.active_labs: application
   lsst.square.metrics.events.nublado.spawn_success: application, username
   lsst.square.metrics.events.qservkafka.arq_job_run: application, queue
   lsst.square.metrics.events.qservkafka.arq_queue_stats: application, queue
   lsst.square.metrics.events.qservkafka.qserv_failure: application
   lsst.square.metrics.events.qservkafka.qserv_success: application, username
   lsst.square.metrics.events.wobbly.completed: application, service, username
   lsst.square.metrics.events.wobbly.created: application, service, username
   lsst.square.metrics.events.wobbly.queued: application, service, username


Transform exported files
========================

Create a transform plan to adjust the exported line protocol files before
import.

The ``sasquatch influxdb line-protocol`` implements the following operations to define a transform plan:

- ``convert-tag-to-field``:  Convert a tag key and value into a string field.
- ``drop-field``:            Drop a field key from a line protocol file.
- ``drop-measurement``:      Drop a measurement from a line protocol file.
- ``drop-tag``:              Drop a tag key from a line protocol file.
- ``rename-field``:          Rename a field key in a line protocol file.
- ``rename-measurement``:    Rename a measurement in a line protocol file.
- ``rename-tag``:            Rename a tag key in a line protocol file.

For example, the following plan drops the ``flock`` tag, renames the
``application`` tag to ``app``, and drops the
``lsst.square.metrics.events.qservkafka.query_failure`` measurement:

.. code-block:: bash

   cat <<EOF > plan.yaml
   - op: drop-tag
     tag: flock

   - op: rename-tag
     from: application
     to: app

   - op: drop-measurement
     measurement: lsst.square.metrics.events.qservkafka.query_failure
   EOF

Apply the transform plan:

.. code-block:: bash

   $ sasquatch influxdb migrate transform --run-dir test-migration-1/ --plan plan.yaml
   Transformed 8 file(s).

.. code-block:: text

   $ sasquatch influxdb migrate status --run-dir /backup/test-migration-1/
   Migration run: lsst.square.metrics / autogen
   Run ID: b0becae5428e
   Backup: sasquatch-influxdb-oss-full-20260424T050007Z
   Mode: explicit
   Manifest status: transformed
   Created: 2026-05-04T18:33:21.855030+00:00
   Updated: 2026-05-04T18:46:58.680591+00:00

   Overall:
     Shards: 3
     Files: 8
     Exported: 8/8
     Transformed: 8/8
     Imported: 0/8
     Error files: 0

   Shard progress:
     Shard  Files  Exported  Transformed  Imported  State
     986    1/1    1/1         1/1            0/1         transformed
     997    1/1    1/1         1/1            0/1         transformed
     1052   6/6    6/6         6/6            0/6         transformed


Import into the target database
===============================

Before importing, make sure the destination database already exists in the
target InfluxDB server.
The import phase rewrites the DML headers in each file
and verifies that the target database named in ``# CONTEXT-DATABASE`` exists before
calling ``influx -import``.

.. note::

   The ``influx -import`` command will import line protocol files into the specified target database.
   Typically the target database is different from the source database, specially if you are transforming the data.
   Always double check the ``--host`` and ``--target-database`` options to prevent accidental
   imports into the wrong database. In the example below, the target database name is the same as the source
   database ``lsst.square.metrics`` but the migration is to different InfluxDB server ``--host sasquatch-influxdb-enterprise-data``.


Run the import:

.. code-block:: bash

   $ sasquatch influxdb migrate import --run-dir test-migration-1/ --host sasquatch-influxdb-enterprise-data --port 8086 --username admin --password <password> --target-database lsst.square.metrics

.. note::

   Use ``--force`` with ``sasquatch influxdb migrate import`` to re-import
   files that are already marked as imported in the manifest. This is useful
   when you need to rerun the import phase for an existing migration run.

Check the final status:

.. code-block:: text

   $ sasquatch influxdb migrate status --run-dir test-migration-1/
   Migration run: lsst.square.metrics / autogen
   Run ID: b0becae5428e
   Backup: sasquatch-influxdb-oss-full-20260424T050007Z
   Mode: explicit
   Manifest status: imported
   Created: 2026-05-04T18:33:21.855030+00:00
   Updated: 2026-05-05T17:03:12.387941+00:00

   Overall:
     Shards: 3
     Files: 8
     Exported: 8/8
     Transformed: 8/8
     Imported: 8/8
     Error files: 0

   Shard progress:
     Shard  Files  Exported  Transformed  Imported  State
     986    1/1    1/1         1/1            1/1         imported
     997    1/1    1/1         1/1            1/1         imported
     1052   6/6    6/6         6/6            6/6         imported


Creating a migration Job
========================

For long-running migrations, define a Kubernetes Job instead of running the
commands interactively in the migration Pod.
The following example uses the Sasquatch application image and mounts the
Sasquatch backup persistent volume at ``/backup``.
That mount gives the Job
access both to the backup directory and to a run
directory under the same volume.

.. note::

  Because the backup volume is ReadWriteOnce (RWO), before applying the migration deployment make sure other Pods are not using the backup volume.

It also mounts a ConfigMap containing ``plan.yaml`` so the transform phase
can read the plan from the container filesystem.

.. code-block:: yaml

   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: sasquatch-migration-plan
     namespace: sasquatch
   data:
     plan.yaml: |
       - op: drop-tag
         tag: flock

       - op: rename-tag
         from: application
         to: app

       - op: drop-measurement
         measurement: lsst.square.metrics.events.qservkafka.query_failure
   ---
   apiVersion: batch/v1
   kind: Job
   metadata:
     name: sasquatch-migration-job
     namespace: sasquatch
   spec:
     template:
       spec:
         restartPolicy: Never
         securityContext:
           runAsNonRoot: true
           runAsUser: 1000
           runAsGroup: 1000
           fsGroup: 1000
         volumes:
         - name: backup
           persistentVolumeClaim:
             claimName: sasquatch-backup-artifacts
         - name: migration-plan
           configMap:
             name: sasquatch-migration-plan
         containers:
         - name: sasquatch-migration
           image: ghcr.io/lsst-sqre/sasquatch:1.4.0
           imagePullPolicy: IfNotPresent
           env:
           - name: SASQUATCH_INFLUXDB_USER
             valueFrom:
               secretKeyRef:
                 name: sasquatch
                 key: influxdb-user
           - name: SASQUATCH_INFLUXDB_PASSWORD
             valueFrom:
               secretKeyRef:
                 name: sasquatch
                 key: influxdb-password
           volumeMounts:
           - name: backup
             mountPath: /backup
           - name: migration-plan
             mountPath: /etc/sasquatch-migration-plan
             readOnly: true
           command:
           - /bin/sh
           - -c
           - >
             sasquatch influxdb migrate discover
             --backup-dir /backup/sasquatch-influxdb-oss-full-20260424T050007Z
             --database lsst.square.metrics
             --retention autogen
             --run-dir /backup/migration-20260424T050007Z
             --all-shards &&
             sasquatch influxdb migrate export
             --verify
             --run-dir /backup/migration-20260424T050007Z &&
             sasquatch influxdb migrate transform
             --run-dir /backup/migration-20260424T050007Z
             --plan /etc/sasquatch-migration-plan/plan.yaml &&
             sasquatch influxdb migrate import
             --run-dir /backup/migration-20260424T050007Z
             --host sasquatch-influxdb-enterprise-data
             --port 8086
             --username "${SASQUATCH_INFLUXDB_USER}"
             --password "${SASQUATCH_INFLUXDB_PASSWORD}"
             --target-database lsst.square.metrics
     backoffLimit: 0

Save the manifest as ``migration-job.yaml`` and apply it:

.. code-block:: bash

   kubectl apply -f migration-job.yaml

Update the example command sequence as needed for your migration.
For example, you might want to run the discover and export phases in one Job and run the transform and import phases in another Job, so you can inspect the exported line protocol files before applying the transform and import steps.

Operational notes
=================

- Use one run directory per migration attempt.
- Monitor the Job logs to track the progress of the migration and check for any errors.

.. code-block:: bash

  kubectl logs job/sasquatch-migration-job -n sasquatch

- Monitor the overall progress of the migration.

.. code-block:: bash

  kubectl exec -it <sasquatch migration pod> -n sasquatch -- sasquatch influxdb migrate status --run-dir <run-dir>

- Exported and transformed files remain in the run directory, so you can
  inspect them before import or rerun later phases with ``--force`` option as needed.

Known edge cases
================

- Some exports may contain multiline string field values. Those records can be produced
  directly by ``influx_inspect export`` and are not safe to import through
  ``influx -import``, which expects one point per line.
  Use ``sasquatch influxdb migrate export --run-dir <run-dir> --verify`` to
  scan exported files and fail early with the file name and measurement if
  this edge case is present.
- ``drop-field`` deletes the entire record line when removing the last field in a point.
  That's the correct choice for InfluxDB line protocol, since a point with zero fields is not valid.
- In the import phase the ``influx -host`` option only accepts hostname and not a URL with subpath like ``https://usdf-rsp.slac.stanford.edu/influxdb-enterprise-data`` for the target InfluxDB server. An nginx reverse proxy can be used to work around this limitation.
  See the Sasquatch ``influxb-migration`` subchart in Phalanx for an example of this setup.
