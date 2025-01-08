.. _schema-registry-ssl:

######################################################################
Schema Registry Pod cannot start because of an invalid SSL certificate
######################################################################

**Symptoms:**
Sasquatch Schema Registry pod cannot start and ends up in ``CrashLoopBackOff`` state.
Kafka brokers show an ``org.apache.kafka.common.errors.SslAuthenticationException``.

**Cause:**
The Schema Registry Operator cannot recreate its JKS secret when Strimzi rotates the cluster certificates.

**Solution:**
Use this procedure in Argo CD to force Schema Registry Operator to create the JKS secret:

- Delete the ``StrimziSchemaRegistry`` resource called ``sasquatch-schema-registry``
- Restart the ``Deployment`` resource called ``strimzi-registry-operator``
- Re-sync the ``StrimziSchemaRegistry`` resource called ``sasquatch-schema-registry``
