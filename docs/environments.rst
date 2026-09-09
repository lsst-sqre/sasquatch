:og:description: Description of the Sasquatch environments.

.. _environments:

############
Environments
############

The table below summarizes the Sasquatch environments and their main entry points.

+-----------------------------------------+---------------------------------------------------+-----------------------------------+---------------------------+
| **Sasquatch Environment**               | **Chronograf UI**                                 | **EFD Client alias**              | **Web UI network access** |
+=========================================+===================================================+===================================+===========================+
| :ref:`Summit<summit>`                   | https://summit-lsp.lsst.codes/chronograf          | ``summit_efd``                    | Chile VPN                 |
+-----------------------------------------+---------------------------------------------------+-----------------------------------+---------------------------+
| :ref:`USDF<usdf>`                       | https://usdf-rsp.slac.stanford.edu/chronograf     | ``usdf_efd``                      | No VPN required           |
+-----------------------------------------+---------------------------------------------------+-----------------------------------+---------------------------+
| :ref:`USDF int<usdfint>`                | https://usdf-rsp-int.slac.stanford.edu/chronograf | (not available)                   | No VPN required           |
+-----------------------------------------+---------------------------------------------------+-----------------------------------+---------------------------+
| :ref:`USDF dev<usdfdev>`                | https://usdf-rsp-dev.slac.stanford.edu/chronograf | ``usdfdev_efd``                   | No VPN required           |
+-----------------------------------------+---------------------------------------------------+-----------------------------------+---------------------------+
| :ref:`IDF<idf>`                         | https://data.lsst.cloud/chronograf                | (not available)                   | No VPN required           |
+-----------------------------------------+---------------------------------------------------+-----------------------------------+---------------------------+
| :ref:`IDF int<idfint>`                  | https://data-int.lsst.cloud/chronograf            | (not available)                   | No VPN required           |
+-----------------------------------------+---------------------------------------------------+-----------------------------------+---------------------------+
| :ref:`IDF dev<idfdev>`                  | https://data-dev.lsst.cloud/chronograf            | ``idfdev_efd``                    | No VPN required           |
+-----------------------------------------+---------------------------------------------------+-----------------------------------+---------------------------+
| :ref:`Roundtable<roundtable>`           | https://roundtable.lsst.cloud/chronograf          | (not available)                   | No VPN required           |
+-----------------------------------------+---------------------------------------------------+-----------------------------------+---------------------------+
| :ref:`Roundtable dev<roundtabledev>`    | https://roundtable-dev.lsst.cloud/chronograf      | (not available)                   | No VPN required           |
+-----------------------------------------+---------------------------------------------------+-----------------------------------+---------------------------+
| :ref:`TTS<tts>`                         | https://tucson-teststand.lsst.codes/chronograf    | ``tucson_teststand_efd``          | NOIRLab VPN               |
+-----------------------------------------+---------------------------------------------------+-----------------------------------+---------------------------+
| :ref:`BTS<bts>`                         | https://base-lsp.lsst.codes/chronograf            | ``base_efd``                      | Chile VPN                 |
+-----------------------------------------+---------------------------------------------------+-----------------------------------+---------------------------+

The Chronograf UI access URL is the main entry point, the other URLs for each environment are listed on this page.
Chronograf requires an authenticated Rubin Science Platform session.
Direct Kafka access has separate network and mutual TLS credential requirements.
See :ref:`direct-connection` for information about configuring a Kafka client.

.. _summit:

Summit
------

Sasquatch production environment at the Summit.
This instance collects engineering data from the Summit and is the primary source of EFD data.

Intended audience: Observers and the Commissioning team at the Summit


- Chronograf: ``https://summit-lsp.lsst.codes/chronograf``
- InfluxDB HTTP API: ``https://summit-lsp.lsst.codes/influxdb``
- Kafdrop UI: ``https://summit-lsp.lsst.codes/kafdrop``
- Kafka bootstrap server: ``sasquatch-summit-kafka-bootstrap.lsst.codes:9094``
- Schema Registry: ``https://summit-lsp.lsst.codes/schema-registry``
- Kafka REST proxy API: ``https://summit-lsp.lsst.codes/sasquatch-rest-proxy``

.. _usdf:

USDF
----

Sasquatch production environment at the USDF.
This instance has EFD data replicated in real-time from the Summit.

Intended audience: Project staff.

- Chronograf: ``https://usdf-rsp.slac.stanford.edu/chronograf``
- InfluxDB HTTP API: ``https://usdf-rsp.slac.stanford.edu/influxdb-enterprise-data``
- Kafdrop UI: ``https://usdf-rsp.slac.stanford.edu/kafdrop``
- Kafdrop Remote UI: ``https://usdf-rsp.slac.stanford.edu/kafdrop-remote``
- Kafka bootstrap server: ``sasquatch-usdf-kafka-bootstrap.lsst.cloud:9094``
- Schema Registry: ``https://usdf-rsp.slac.stanford.edu/schema-registry``
- Schema Registry Remote: ``https://usdf-rsp.slac.stanford.edu/schema-registry-remote``
- Kafka REST proxy API: ``https://usdf-rsp.slac.stanford.edu/sasquatch-rest-proxy``

.. _usdfint:

USDF int
--------

Sasquatch integration environment at the USDF.
This instance is used for testing Sasquatch integrations and receives a limited selection of EFD data replicated from the Summit.

Intended audience: Project staff.

- Chronograf: ``https://usdf-rsp-int.slac.stanford.edu/chronograf``
- InfluxDB HTTP API: ``https://usdf-rsp-int.slac.stanford.edu/influxdb``
- Kafdrop UI: ``https://usdf-rsp-int.slac.stanford.edu/kafdrop``
- Kafdrop Remote UI: ``https://usdf-rsp-int.slac.stanford.edu/kafdrop-remote``
- Kafka bootstrap server: ``sasquatch-usdf-int-kafka-bootstrap.lsst.cloud:9094``
- Schema Registry: ``https://usdf-rsp-int.slac.stanford.edu/schema-registry``
- Schema Registry Remote: ``https://usdf-rsp-int.slac.stanford.edu/schema-registry-remote``
- Kafka REST proxy API: ``https://usdf-rsp-int.slac.stanford.edu/sasquatch-rest-proxy``

.. _usdfdev:

USDF dev
--------

Sasquatch development environment at USDF.

Intended audience: Project staff.

- Chronograf: ``https://usdf-rsp-dev.slac.stanford.edu/chronograf``
- InfluxDB HTTP API: ``https://usdf-rsp-dev.slac.stanford.edu/influxdb``
- Kafdrop UI: ``https://usdf-rsp-dev.slac.stanford.edu/kafdrop``
- Kafdrop Remote UI: ``https://usdf-rsp-dev.slac.stanford.edu/kafdrop-remote``
- Kafka bootstrap server: ``sasquatch-usdf-dev-kafka-bootstrap.lsst.cloud:9094``
- Schema Registry: ``https://usdf-rsp-dev.slac.stanford.edu/schema-registry``
- Schema Registry Remote: ``https://usdf-rsp-dev.slac.stanford.edu/schema-registry-remote``
- Kafka REST proxy API: ``https://usdf-rsp-dev.slac.stanford.edu/sasquatch-rest-proxy``

.. _idf:

IDF
---

Sasquatch production environment for the community science platform in Google Cloud.
This instance is mainly used for :ref:`application metrics<app-metrics>`.

Intended audience: Project staff.

- Chronograf: ``https://data.lsst.cloud/chronograf``
- InfluxDB HTTP API: ``https://data.lsst.cloud/influxdb``
- Kafdrop UI: ``https://data.lsst.cloud/kafdrop``
- Kafka bootstrap server: ``sasquatch-kafka-bootstrap.lsst.cloud:9094``
- Schema Registry: ``https://data.lsst.cloud/schema-registry``
- Kafka REST proxy API: (not available)

.. _idfint:

IDF int
-------

Sasquatch integration environment for the community science platform in Google Cloud.
This instance is used for testing.
There is no direct EFD integration.

Intended audience: Project staff.

- Chronograf: ``https://data-int.lsst.cloud/chronograf``
- InfluxDB HTTP API: ``https://data-int.lsst.cloud/influxdb``
- Kafdrop UI: ``https://data-int.lsst.cloud/kafdrop``
- Kafka bootstrap server: ``sasquatch-int-kafka-bootstrap.lsst.cloud:9094``
- Schema Registry: ``https://data-int.lsst.cloud/schema-registry``
- Kafka REST proxy API: ``https://data-int.lsst.cloud/sasquatch-rest-proxy``

.. _idfdev:

IDF dev
-------

Sasquatch dev environment for the community science platform in Google Cloud.
This instance is used for testing.

Intended audience: Project staff.

- Chronograf: ``https://data-dev.lsst.cloud/chronograf``
- InfluxDB HTTP API: ``https://data-dev.lsst.cloud/influxdb``
- Kafdrop UI: ``https://data-dev.lsst.cloud/kafdrop``
- Kafka bootstrap server: ``sasquatch-dev-kafka-bootstrap.lsst.cloud:9094``
- Schema Registry: ``https://data-dev.lsst.cloud/schema-registry``
- Kafka REST proxy API: ``https://data-dev.lsst.cloud/sasquatch-rest-proxy``

.. _roundtable:

Roundtable
----------

Sasquatch production environment for Roundtable in Google Cloud.
This instance stores application metrics and Square Events for Roundtable services.

Intended audience: Project staff.

- Chronograf: ``https://roundtable.lsst.cloud/chronograf``
- InfluxDB HTTP API: ``https://roundtable.lsst.cloud/influxdb``
- Kafdrop UI: ``https://roundtable.lsst.cloud/kafdrop``
- Kafka bootstrap server: (not externally available)
- Schema Registry: (not externally available)
- Kafka REST proxy API: (not available)

.. _roundtabledev:

Roundtable dev
--------------

Sasquatch development environment for Roundtable in Google Cloud.
This instance is used for testing application metrics and Square Events integrations for Roundtable services.

Intended audience: Project staff.

- Chronograf: ``https://roundtable-dev.lsst.cloud/chronograf``
- InfluxDB HTTP API: ``https://roundtable-dev.lsst.cloud/influxdb``
- Kafdrop UI: ``https://roundtable-dev.lsst.cloud/kafdrop``
- Kafka bootstrap server: (not externally available)
- Schema Registry: (not externally available)
- Kafka REST proxy API: (not available)

.. _tts:

Tucson Test Stand (TTS)
-----------------------

Sasquatch production environment at the Tucson test stand.

Intended audience: Telescope & Site team.

- Chronograf: ``https://tucson-teststand.lsst.codes/chronograf``
- InfluxDB HTTP API: ``https://tucson-teststand.lsst.codes/influxdb``
- Kafdrop UI: ``https://tucson-teststand.lsst.codes/kafdrop``
- Kafka bootstrap server: ``sasquatch-tts-kafka-bootstrap.lsst.codes:9094``
- Schema Registry: ``https://tucson-teststand.lsst.codes/schema-registry``
- Kafka REST proxy API: ``https://tucson-teststand.lsst.codes/sasquatch-rest-proxy``

.. _bts:

Base Test Stand (BTS)
---------------------

Sasquatch production environment at the Base test stand.

Intended audience: Telescope & Site team.

- Chronograf: ``https://base-lsp.lsst.codes/chronograf``
- InfluxDB HTTP API: ``https://base-lsp.lsst.codes/influxdb``
- Kafdrop UI: ``https://base-lsp.lsst.codes/kafdrop``
- Kafka bootstrap server: ``sasquatch-base-kafka-bootstrap.lsst.codes:9094``
- Schema Registry: ``https://base-lsp.lsst.codes/schema-registry``
- Kafka REST proxy API: ``https://base-lsp.lsst.codes/sasquatch-rest-proxy``
