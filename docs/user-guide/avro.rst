.. _avro-schemas:

############
Avro schemas
############

Sasquatch uses `Avro`_ as serialization format.
Avro is a binary format, it provides a schema for the data and supports schema evolution via the `Confluent Schema Registry`_.

This guide describes how to define Avro schemas for your data and how to use them in Sasquatch.

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

The :ref:`namespace <namespaces>` and the metric name are used to create the full qualified name ``lsst.example.skyFluxMetric``.
The full qualified name is also corresponds to the Kafka topic name.
The schema is stored in the Schema Registry and is used to validate the data sent to Sasquatch.

Read more about Avro schemas and types in the `Avro specification`_.

Adding units and description
============================

It is recommended to add units and description to the schema.
Some clients like the EFD client can display this information to help users understand the data.

The convention in Sasquatch is to add the ``units`` and ``description`` keys in every field of the schema.
Use `astropy units`_ whenever possible.

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

Default values
==============

In Avro it is possible to provide a default value for fields, however it is only used during schema evolution, for example, when a new field is added to the schema and old data is read.
Not that it doesn't make the field optional at encoding time, so when sending data to Sasquatch all fields defined in the schema must be present, even if they have a default value.

The convention in Sasquatch is to use the Avro ``null`` value as default value.
The schema uses the `Union`_ type:

.. code:: json

    {"name": "meanSky", "type": ["null", "float"], "default": null}

Note that because of the union type, when sending data to Sasquatch this will not work:

.. code:: json

    {"meanSky": 2328.906}

Instead use the following format for fields with default values:

.. code:: json

    {"meanSky": {"float": 2328.906}}

Schema evolution
================

In Sasquatch, schema changes should be *forward-compatible* so that consumers won't break.
Sasquatch consumers include Kafka consumers like Telegraf, any application that queries InfluxDB, and Chronograf dashboards.

Forward compatibility means that data produced with a new schema can be read by consumers using the previous schema.
An example of a forward-compatible schema change is adding a new field to the schema with a default value, so that old consumers can ignore the new field and new consumers can use the default value when reading old data.
Removing or renaming existing fields are examples of non forward-compatible schema changes.

Read more about forward compatibility in the `Confluent Schema Registry`_ documentation.

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
Adding the ``visit`` field to the schema is a *forward-compatible* change.

Additionally, adding the ``visit`` field with a default value will ensure that old messages can still be read by new consumers.

The new schema will look like this:

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
                "type": ["null", "int"], "default": null}
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

New messages sent to Sasquatch now require the ``visit`` field and a new consumers that use the ``visit`` information can be implemented.
Because the visit field has a default value, new consumers can still read old messages that don't have the ``visit`` field.


