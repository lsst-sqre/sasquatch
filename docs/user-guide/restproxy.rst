.. _rest-proxy:

################
Kafka REST Proxy
################

The Kafka REST Proxy allows HTTP-based clients to interact with Kafka via a REST API.

Because the Kafka REST Proxy is integrated with the Schema Registry, HTTP clients
can easily send data in Avro format.

Kafka topics
============

To send data to Sasquatch, first, you need to :ref:`create-a-kafka-topic` for your metric.

.. note::

    Kafka topics must be created with the right :ref:`namespace prefix <namespaces>` to be added to the Kafka REST Proxy API.

Use ``/topics`` in the Kafka REST Proxy API to list the available topics.

At USDF dev, for example, the endpoint for the ``lsst.example.skyFluxMetric`` Kafka topic is:

- ``https://usdf-rsp-dev.slac.stanford.edu/sasquatch-rest-proxy/topics/lsst.example.skyFluxMetric``


Send data via the Kafka REST Proxy API
======================================

To send data to a Kafka topic, make a ``POST`` request to the Kafka REST Proxy API with the Avro schema and records.

From the example in the previous section, the request body would be:

.. code:: json

    {
	"value_schema": "{\"namespace\": \"lsst.example\", \"type\": \"record\", \"name\": \"skyFluxMetric\", \"fields\": [{\"name\": \"timestamp\",\"type\": \"long\"}, {\"name\": \"band\",\"type\": \"string\"}, {\"name\": \"instrument\",\"type\": \"string\", \"default\": \"LSSTCam-imSim\"}, {\"name\": \"meanSky\",\"type\": \"float\"}, {\"name\": \"stdevSky\",\"type\": \"float\",}]}",
	"records": [
		{
			"value": {
				"timestamp": 1681248783000000,
				"band": "y",
				"instrument": "LSSTCam-imSim",
				"meanSky": -213.75839364883444,
				"stdevSky": 2328.906118708811
			}
		}
	]
    }

Note that the Avro schema needs to be stringified with backslashes before each double quote.
This schema formatting is required to send the Avro schema via the REST Proxy API.

In addition to the request body, you need the ``Content-type`` and ``Accept`` headers to indicate an HTTP request that contains an Avro payload encoded in JSON and compatible with the REST Proxy v2 API.

.. code:: json

    {
    "Content-Type": "application/vnd.kafka.avro.v2+json",
    "Accept": "application/vnd.kafka.v2+json"
    }


A code snippet in Python to send data to the ``lsst.example.skyFluxMetric`` Kafka topic at the USDF dev environment would be:

.. code:: Python

    import requests

    url = "https://usdf-rsp-dev.slac.stanford.edu/sasquatch-rest-proxy/topics/lsst.example.skyFluxMetric"

    payload = {
        "value_schema": '{"namespace": "lsst.example", "type": "record", "name": "skyFluxMetric", "fields": [{"name": "timestamp", "type": "long"}, {"name": "band", "type": "string"}, {"name": "instrument", "type": "string", "default": "LSSTCam-imSim"}, {"name": "meanSky","type": "float"}, {"name": "stdevSky","type": "float"}]}',
        "records": [
            {
                "value": {
                    "timestamp": 1681248783000000,
                    "band": "y",
                    "instrument": "LSSTCam-imSim",
                    "meanSky": -213.75839364883444,
                    "stdevSky": 2328.906118708811,
                }
            }
        ],
    }
    headers = {
        "Content-Type": "application/vnd.kafka.avro.v2+json",
        "Accept": "application/vnd.kafka.v2+json",
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    print(response.text)

The REST Proxy will register the schema with the Schema Registry.
If the schema is already registered, the REST Proxy will check the schema compatibility before sending data to Kafka.

Note that from the HTTP response, you can get the schema ID and re-use it for subsequent requests.

.. code:: json

    {
	"value_schema_id": 213
	"records": [
		{
			"value": {
				"timestamp": 1681248783000000,
				"band": "y",
				"instrument": "LSSTCam-imSim",
				"meanSky": -213.75839364883444,
				"stdevSky": 2328.906118708811
			}
		}
	]
    }

.. _create-a-kafka-topic:

Create a Kafka topic
====================

The Kafka REST Proxy also offers an API for managing Kafka topics.

To create a Kafka topic, first, get the Kafka cluster ID.
A code snippet in Python for getting the cluster ID from the USDF dev environment would be:

.. code::

    import requests

    sasquatch_rest_proxy_url = "https://usdf-rsp-dev.slac.stanford.edu/sasquatch-rest-proxy"

    headers = {"content-type": "application/json"}

    r = requests.get(f"{sasquatch_rest_proxy_url}/v3/clusters", headers=headers)

    cluster_id = r.json()['data'][0]['cluster_id']

    print(cluster_id)


Then make a ``POST`` request to the ``/topics`` endpoint:

.. code::

    topic_config = {
        "topic_name": "lsst.example.skyFluxMetric",
        "partitions_count": 1,
        "replication_factor": 3
    }

    headers = {"content-type": "application/json"}

    response = requests.post(f"{sasquatch_rest_proxy_url}/v3/clusters/{cluster_id}/topics", json=topic_config, headers=headers)

    print(response.text)

That creates the ``lsst.example.skyFluxMetric`` Kafka topic with one partition and three replicas, one for each broker in the cluster.

.. _namespaces:

Namespaces
==========

The following namespaces are currently configured with the Kafka REST Proxy:

- ``lsst.example``
- ``lsst.debug``
- ``lsst.dm``

Only Kafka topics created with those prefixes are added to the Kafka REST Proxy API.