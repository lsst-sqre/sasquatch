.. _avro:

############
Avro schemas
############

Sasquatch uses Avro as serialization format.
An advantage of Avro is that it provides a schema and supports schema evolution with the help of the `Confluent Schema Registry`_.

For example, assume a metric named ``skyFluxMetric`` with the following data:

.. code:: json

    {
        "timestamp": 1681248783000000,
        "band": "y",
        "instrument": "LSSTCam-imSim",
        "meanSky": -213.75839364883444,
        "stdevSky": 2328.906118708811,
    }

A simple Avro schema for this metric would look like this:

.. code:: json

    {
        "namespace": "lsst.example",
        "name": "skyFluxMetric",
        "type": "record",
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

The :ref:`namespace <namespaces>` and the metric name are used to create the full qualified metric name in Sasquatch, ``lsst.example.skyFluxMetric``, which also corresponds to the Kafka topic name.
The schema is stored in the Schema Registry and is used to validate the data sent to Sasquatch.

Read more about Avro schemas and types in the `Avro specification`_.

Adding units and description
============================

Adding units and description is recommended and they are used by the EFD client ``.get_schema()`` method to display this information and help users to understand the data.

The convention in Sasquatch is to add the ``units`` and ``description`` keys in every field of the schema, and `astropy units`_ whenerver possible.

.. code:: json

    {
        "namespace": "lsst.example",
        "name": "skyFluxMetric",
        "type": "record",
        "fields": [
            {
                "name": "timestamp",
                "type": "long",
                "units": "ms",
                "description": "The time the metric was measured in millisecons since the Unix epoch."
            },
            {
                "name": "band",
                "type": "string",
                "units": "unitless",
                "description": "The observation band associated to this metric."
            },
            {
                "name": "instrument",
                "type": "string",
                "units": "unitless",
                "description": "The name of the instrument associated to this metric."
            },
            {
                "name": "meanSky",
                "type": "float",
                "units": "adu",
                "description": "The mean sky flux in ADU."
            },
            {
                "name": "stdevSky",
                "type": "float",
                "units": "adu",
                "description": "The standard deviation of the sky flux in ADU."

            }
        ]
    }

.. _astropy units: https://docs.astropy.org/en/stable/units/

Optional fields
===============

In some situations, you don’t have values for all the fields defined in the schema.
In this case you can mark the field as optional and provide a default value.
Sasquatch uses the Avro null value for nullable fields, and the schema for a nullable field uses the `Union`_ type:

.. code:: json

    {"name": "meanSky", "type": ["null", "float"], "default": null}

Note that because of the union type, when sending data to Sasquatch this will not work:

.. code:: json

    {"meanSky": 2328.906}

Intead, you must do this:

.. code:: json

    {"meanSky": {"float": 2328.906}}

.. _Union: https://avro.apache.org/docs/1.11.1/specification/#unions

Schema evolution
================

In Sasquatch, schema changes must be *forward-compatible* so that consumers won't break.
Sasquatch consumers include Kafka consumers, any application that queries InfluxDB, and Chronograf dashboards.

Forward compatibility means that data produced with a new schema can be read by consumers using the previous schema.
An example of a forward-compatible schema change is adding a new field to the schema.
Removing or renaming an existing field are examples of non forward-compatible schema changes.

Read more about forward compatibility in the `Confluent Schema Registry`_ documentation.

.. _Confluent Schema Registry: https://docs.confluent.io/platform/current/schema-registry/fundamentals/avro.html#forward-compatibility


Suppose there's a dashboard in Chronograf with a chart that displays a time series of ``meanSky`` and ``stdevSky`` values grouped by ``band``.
The ``timestamp``, ``band``, ``meanSky`` and ``stdevSky`` fields are always required for that chart to work.
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

Now, suppose you want to add a table linked to the previous chart to display the visit ID associated with this metric.
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

New messages sent to Sasquatch now require the ``visit`` field and a new query that uses the ``visit`` information can be implemented.
Because this is a forward-compatible schema change, existing queries won't break since they don't use the ``visit`` field.


.. _Avro specification: https://avro.apache.org/docs/1.11.1/specification/
