.. _license:

########################################
InfluxDB Enterprise license installation
########################################

This guide describes how to install and verify InfluxDB Enterprise licenses in Sasquatch environments.

Overview
========

InfluxDB Enterprise cluster and single-node instances require a valid license to operate.
Licenses are renewed annually.
SLAC initiates the requisition process in early November, since existing licenses expire in early December.

InfluxData delivers license files in JSON format via email.
After receipt, they are uploaded to the LSST IT SQuaRE 1Password vault.
Look for ``InfluxDB Enterprise Licenses`` entry in 1Password or create a new folder to store new license files.

License Types by Environment
----------------------------

The vault entry also records which Sasquatch environment each license is assigned to.
Example:

.. code-block:: text

  Attached license files for InfluxDB Enterprise (expiration on 2025-12-08T00:00:00Z):

  License #763 - 2x8_Production (USDF - InfluxDB Enterprise active instance)
  License #465 - 2x8_Production (Summit - InfluxDB Enterprise active instance)
  License #779 - Single Node (Summit - InfluxDB Enterprise standby instance)
  License #477 - Single Node
  License #319 - Single Node (USDF - InfluxDB Enterprise standby instance)
  License #956 - Non-Production (idfdev - InfluxDB Enterprise de instance)


Both USDF and Summit operate two InfluxDB Enterprise instances:

- Active instance: uses a cluster license (2 nodes × 8 cores).

-	Standby instance: sses a single-node license (1 node × 16 cores).

License Installation
--------------------

Each environment assigned license file must be stored in the ``sasquatch`` Kubernetes secret under the key ``influxdb-enterprise-license``.
The secret is mounted from a volume in the InfluxDB Enterprise meta Pods, a restart of the meta Pods is **not required** after updating the secret.

Follow the Phalanx procedure to `update a static secret`_.

Verifying License Installation
------------------------------

After updating the secret, verify that the license is present and recognized by the InfluxDB Enterprise meta Pods.

1. Inspect the license inside a meta Pod

.. code-block:: bash

  kubectl exec -it sasquatch-influxdb-enterprise-meta-0 -n sasquatch -- \
  cat /var/run/secrets/influxdb/license.json

You should see the JSON contents of the installed license file.
In particular, verify that the ``expires_at`` field reflects the new expiration date.

2. Check meta Pod logs for a successful license load message **after** the installation

A successful load is indicated by a message similar to:

.. code-block:: bash

  kubectl logs sasquatch-influxdb-enterprise-meta-0 -n sasquatch

  ts=2024-12-09T21:15:24.588979Z lvl=info msg="Reading InfluxDB Enterprise license locally" \
  log_id=0~KMKgvG001 service=licensing path=/var/run/secrets/influxdb/license.json

If this message is present, the new license was detected and applied.


.. _update a static secret: https://phalanx.lsst.io/admin/update-a-secret.html
