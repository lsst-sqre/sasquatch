.. _avro:

#########################
Avro and schema evolution
#########################

Sasquatch uses the Avro format.
An advantage of Avro is that it has a schema that comes with the data and supports schema evolution.

Sasquatch uses the `Confluent Schema Registry`_ to ensure schemas can evolve safely.
In Sasquatch, schema changes must be *forward-compatible* so that consumers of Sasquatch won't break.
That includes Kafka consumers, InfluxDB queries, and even Chronograf dashboards.

Forward compatibility means that data produced with a new schema can be read by consumers using the previous schema.
An example of a forward-compatible schema change is adding a new field.
Removing or renaming an existing field are non forward-compatible schema changes.

Read more about forward compatibility in the `Confluent Schema Registry`_ documentation.

.. _Confluent Schema Registry: https://docs.confluent.io/platform/current/schema-registry/fundamentals/avro.html#forward-compatibility

For example, assume the ``skyFluxMetric`` metric with the following payload:

.. code:: json

    {
        "timestamp": 1681248783000000,
        "band": "y",
        "instrument": "LSSTCam-imSim",
        "meanSky": -213.75839364883444,
        "stdevSky": 2328.906118708811,
    }

Suppose there's a dashboard in Chronograf with a chart that displays a time series of ``meanSky`` and ``stdevSky`` values grouped by ``band``.
Thus the ``timestamp``, ``band``, ``meanSky`` and ``stdevSky`` fields are required in the metric record for the dashboard to work.
The following Avro schema will ensure these fields are always present:

.. code:: json

    {
        "namespace": "lsst.example",
        "type": "record",
        "name": "skyFluxMetric",
        "fields": [
            {
                "name": "timestamp",
                "type": "long"
            },
            {
                "name": "band",
                "type": "string"
            },
            {
                "name": "instrument",
                "type": "string",
            },
            {
                "name": "meanSky",
                "type": "float"
            },
            {
                "name": "stdevSky",
                "type": "float"
            }
        ]
    }

Suppose you want to add a table linked to the previous chart in the dashboard to display the visit ID associated with this metric.
Adding the ``visit`` field to the schema is a *forward-compatible* change, so that's allowed:

.. code:: json

    {
        "namespace": "lsst.example",
        "type": "record",
        "name": "skyFluxMetric",
        "fields": [
            {
                "name": "timestamp",
                "type": "long"
            },
            {
                "name": "band",
                "type": "string"
            },
            {
                "name": "instrument",
                "type": "string",
            },
            {
                "name": "visit",
                "type": "int"
            },
            {
                "name": "meanSky",
                "type": "float"
            },
            {
                "name": "stdevSky",
                "type": "float"
            }
        ]
    }

New messages sent to Sasquatch now require the ``visit`` field and a new version of the dashboard that uses the ``visit`` information can be implemented.
Because this is a forward-compatible schema change, previous dashboard versions won't break since they don't use the ``visit`` field.

In Sasquatch, a metric (or a telemetry topic) corresponds to a Kafka topic.
The metric :ref:`namespace <namespaces>` is specified in the Avro schema, and the metric full qualified name in this example is ``lsst.example.skyFluxMetric``.

Read more about Avro schemas and types in the `Avro specification`_.

.. _Avro specification: https://avro.apache.org/docs/1.11.1/specification/
