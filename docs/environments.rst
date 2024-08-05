:og:description: Description of the Sasquatch environments.

.. _environments:

############
Environments
############

The table below summarizes the Sasquatch environments and their main entry points.

+---------------------------+---------------------------------------------------+-----------------------------------+----------------+
| **Sasquatch Environment** | **Chronograf UI**                                 | **EFD Client alias**              | **VPN access** |
+===========================+===================================================+===================================+================+
| :ref:`Summit<summit>`     | https://summit-lsp.lsst.codes/chronograf          | ``summit_efd``                    | Chile VPN      |
+---------------------------+---------------------------------------------------+-----------------------------------+----------------+
| :ref:`USDF<usdf>`         | https://usdf-rsp.slac.stanford.edu/chronograf     | ``usdf_efd``                      | Not required   |
+---------------------------+---------------------------------------------------+-----------------------------------+----------------+
| :ref:`USDF dev<usdfdev>`  | https://usdf-rsp-dev.slac.stanford.edu/chronograf | ``usdfdev_efd``                   | Not required   |
+---------------------------+---------------------------------------------------+-----------------------------------+----------------+
| :ref:`TTS<tts>`           | https://tucson-teststand.lsst.codes/chronograf    | ``tucson_teststand_efd``          | NOIRLab VPN    |
+---------------------------+---------------------------------------------------+-----------------------------------+----------------+
| :ref:`BTS<bts>`           | https://base-lsp.lsst.codes/chronograf            | ``base_efd``                      | Chile VPN      |
+---------------------------+---------------------------------------------------+-----------------------------------+----------------+

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
- Schema Registry: ``http://sasquatch-schema-registry.sasquatch:8081`` (cluster internal)
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
- Kafka boostrap server:
  (not yet available)
- Schema Registry: ``http://sasquatch-schema-registry.sasquatch:8081`` (cluster internal)
- Kafka REST proxy API: ``https://usdf-rsp.slac.stanford.edu/sasquatch-rest-proxy``

.. _usdfdev:

USDF dev
--------

Sasquatch development environment at USDF.

Intended audience: Project staff.

- Chronograf: ``https://usdf-rsp-dev.slac.stanford.edu/chronograf``
- InfluxDB HTTP API: ``https://usdf-rsp-dev.slac.stanford.edu/influxdb``
- Kafdrop UI: ``https://usdf-rsp-dev.slac.stanford.edu/kafdrop``
- Kafka boostrap server:
  (not yet available)
- Schema Registry: ``http://sasquatch-schema-registry.sasquatch:8081`` (cluster internal)
- Kafka REST proxy API: ``https://usdf-rsp-dev.slac.stanford.edu/sasquatch-rest-proxy``

.. _tts:

Tucson Test Stand (TTS)
-----------------------

Sasquatch production environment at the Tucson test stand.

Intended audience: Telescope & Site team.

- Chronograf: ``https://tucson-teststand.lsst.codes/chronograf``
- InfluxDB HTTP API: ``https://tucson-teststand.lsst.codes/influxdb``
- Kafdrop UI: ``https://tucson-teststand.lsst.codes/kafdrop``
- Kafka bootstrap server: ``sasquatch-tts-kafka-bootstrap.lsst.codes:9094``
- Schema Registry: ``http://sasquatch-schema-registry.sasquatch:8081`` (cluster internal)
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
- Schema Registry: ``http://sasquatch-schema-registry.sasquatch:8081`` (cluster internal)
- Kafka REST proxy API: ``https://base-lsp.lsst.codes/sasquatch-rest-proxy``

.. _idf:

IDF
---

The IDF environment is meant to be a short-term solution to serve historical EFD data until we can restore data at USDF.
For real-time analysis of the EFD, please use the USDF environment.

Intended audience: Project staff.

- Chronograf: ``https://data-int.lsst.cloud/chronograf``
