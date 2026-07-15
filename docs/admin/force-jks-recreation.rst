.. force-jks-recreation


Force keystore secret recreation
================================

Sasquatch `strimzi-registry-operator <https://github.com/lsst-sqre/strimzi-registry-operator>`_ should correctly recreate the Java Key Store (JKS) secret when Kafka CA or client certs rotate.

To force the JKS secret to be recreated, you can delete the ``StrimziSchemaRegistry`` resource called ``sasquatch-schema-registry`` in Argo CD and resync, this will trigger the operator to recreate the JKS secret with the new CA and client certs and redeploy the Schema Registry.

To check the certificate validity period in the JKS secret, you can use the following command:

.. code:: bash

    kubectl get secret sasquatch-schema-registry-jks \
    -n sasquatch \
    -o jsonpath='{.data.keystore\.jks}' \
    | base64 --decode > /tmp/keystore.jks

    keytool -list -v \
    -keystore /tmp/keystore.jks \
    -storepass '<keystore password>'

where the keystore password is also stored in the ``sasquatch-schema-registry-jks`` secret.
