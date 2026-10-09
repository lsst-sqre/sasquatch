.. _influxdb-users:

#######################
Creating InfluxDB users
#######################

The ``influxdb-users`` Sasquatch subchart creates non-administrator users in
InfluxDB and grants them database-level privileges. It supports the InfluxDB
OSS and InfluxDB Enterprise deployments managed by Sasquatch.

The subchart runs an ``influx`` command-line client against each configured
target. For each user, it creates the user and then grants each configured
database privilege. It does not create databases.


Prepare the password secret
===========================

Store the password as a static secret in Sasquatch.

#. Add a key for the password to
   :file:`applications/sasquatch/secrets.yaml` in Phalanx. For example:

   .. code-block:: yaml

      influxdb-grafana-reader-password:
        description: >-
          Password for the Grafana InfluxDB user.
        if: influxdb-users.enabled

#. Follow Phalanx documentation to add the static secret to the secret store before syncing
   the application.


Configure users and privileges
==============================

Add an ``influxdb-users`` section to
:samp:`applications/sasquatch/values-{environment}.yaml` in Phalanx. This
example creates one user with read access to two databases:

.. code-block:: yaml

   influxdb-users:
     enabled: true
     targets:
       - name: influxdb
         hostname: sasquatch-influxdb
         users:
           - username: grafana-reader
             passwordSecretRef:
               name: sasquatch
               key: influxdb-grafana-reader-password
             databases:
               - name: efd
                 privilege: READ
               - name: engineering
                 privilege: READ

``name``
   A unique, DNS-compatible name for the target. It is used in the Kubernetes
   Job name and labels.

``hostname``
   The Kubernetes service hostname for the InfluxDB target. Specify only the
   hostname, without a URL scheme, port, path, or command-line options. Common
   Sasquatch examples include ``sasquatch-influxdb`` for InfluxDB OSS and
   ``sasquatch-influxdb-enterprise-data`` for InfluxDB Enterprise.

``username``
   The InfluxDB user to create. Usernames are quoted by the subchart, so names
   containing hyphens are supported.

``passwordSecretRef``
   The Kubernetes Secret name and key containing the new user's password.

``databases``
   The databases to which privileges are granted. Database names are quoted,
   and each database name must be unique for a given user and target. The
   supported privileges are ``READ``, ``WRITE``, and ``ALL``.

To manage multiple InfluxDB instances, add one target for each instance.

The subchart creates one post-install or post-upgrade Job per target.


Known limitations
=================

The subchart manages creation and additive grants only:

* It does not inspect existing users or grants.
* It does not update or rotate an existing user's password.
* It does not revoke privileges or delete users.
* Removing a user or database from the Helm values does not change existing
  InfluxDB state.
* Granting ``READ`` does not remove an existing ``WRITE`` or ``ALL``
  privilege.
