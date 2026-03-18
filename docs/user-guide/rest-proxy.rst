.. _rest-proxy:

################
Kafka REST Proxy
################

The Kafka REST Proxy allows HTTP-based clients to interact with Kafka via a REST API.

Because the Kafka REST Proxy is integrated with the Schema Registry, HTTP clients
can easily send data in Avro format.

Authentication
==============

The Kafka REST Proxy requires a Rubin Science Platform (RSP) access token for authentication with the ``wite:sasquatch`` scope.
See the `RSP documentation`_ for more information about how to obtain an access token.


Creating Kafka topics
=====================

To send data to Sasquatch, you need a Kafka topic for your metric.

Kafka topics in Sasquatch are organized in namespaces, see :ref:`namespaces` for more details.

Kafka topics can be created via Sasquatch configuration.
In this case, a Sasquatch subchart is the right place for creating your application resources, including Kafka topics.
See :ref:`adding-subcharts` for more details.

Sometimes, you may want to create Kafka topics programmatically, for example when your application needs to create topics dynamically based on the data it receives.
The Kafka REST Proxy offers an API for creating Kafka topics programmatically.

A code snippet in Python for creating a Kafka topic using the REST Proxy API looks like the following.

First get the cluster ID from the Sasquatch environment, for example, for the USDF dev environment:

.. code::

    import requests

    sasquatch_rest_proxy_url = "https://usdf-rsp-dev.slac.stanford.edu/sasquatch-rest-proxy"

    headers = {
        "content-type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

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

    headers = {
        "content-type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.post(f"{sasquatch_rest_proxy_url}/v3/clusters/{cluster_id}/topics", json=topic_config, headers=headers)

    print(response.text)

That would create the ``lsst.example.skyFluxMetric`` Kafka topic.
The topic configuration requires the number of partitions and the number of replicas for the topic.


Sending data via the Kafka REST Proxy
=====================================

To send data to a Kafka topic, make a ``POST`` request to the Kafka REST Proxy API with the Avro schema and records.

From the example in :ref:`avro-schemas` section, the request body to send the schema and one record for the ``lsst.example.skyFluxMetric`` Kafka topic would look like this:

.. code:: Python

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

Note that the Avro schema needs to be stringified, that's required when embedding the Avro schema in the JSON payload.

.. note::

    By default Sasquatch assumes every message contains a ``timestamp`` field of type ``long`` with Unix timestamps in microseconds precision.
    Another option is to use Avro type ``double`` and specify the Unix epoch timestamps in seconds.

    See :ref:`connectors` for selecting the timestamp field and configuring the timestamp format options.

The request headers to indicate an HTTP request that contains an Avro payload encoded in JSON and compatible with the REST Proxy API would be:

.. code:: Python

    headers = {
        "Content-Type": "application/vnd.kafka.avro.v2+json",
        "Accept": "application/vnd.kafka.v2+json",
        "Authorization": f"Bearer {access_token}"
    }

A code snippet in Python for sending data to the ``lsst.example.skyFluxMetric`` Kafka topic at the USDF dev environment would be:

.. code:: Python

    import requests

    url = "https://usdf-rsp-dev.slac.stanford.edu/sasquatch-rest-proxy/topics/lsst.example.skyFluxMetric"

    response = requests.request("POST", url, json=payload, headers=headers)

The REST Proxy will register the schema with the Schema Registry.
If the schema is already registered, the REST Proxy will check the schema compatibility before sending data to Kafka.

A successful response will contain the offset of the record in the Kafka topic.

Learn more about the Kafka REST Proxy API in the `Confluent documentation`_.

.. _Confluent documentation: https://docs.confluent.io/platform/current/kafka-rest/

