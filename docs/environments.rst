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
| :ref:`BTS<bts>`           | https://base-lsp.lsst.codes/chronograf [#f1]_     | ``base_efd``, ``summit_efd_copy`` | Chile VPN      |
+---------------------------+---------------------------------------------------+-----------------------------------+----------------+

.. rubric:: Footnotes

.. [#f1] The default Chronograf organization at BTS gives access to simulated data.
         Switch to the "Summit EFD copy" organization to access Summit EFD data from Chronograf at BTS.

.. _summit:

Summit
------

Sasquatch production environemtn at the Summit.

Intended audience: Observers and Commissioning team.

.. note::
   The Summit EFD database is also available from USDF.


- Chronograf: ``https://summit-lsp.lsst.codes/chronograf``
- InfluxDB HTTP API: ``https://summit-lsp.lsst.codes/influxdb``
- Kafdrop UI: ``https://summit-lsp.lsst.codes/kafdrop``
- Kafka bootstrap server: ``sasquatch-summit-kafka-bootstrap.lsst.codes:9094``
- Schema Registry: ``http://sasquatch-schema-registry.sasquatch:8081`` (cluster internal only)
- Kafka REST proxy API: ``https://summit-lsp.lsst.codes/sasquatch-rest-proxy``

.. _usdf:

USDF
----

Sasquatch production environment at the USDF.

Intended audience: Project staff.

- Chronograf: ``https://usdf-rsp.slac.stanford.edu/chronograf``
- InfluxDB HTTP API: ``https://usdf-rsp.slac.stanford.edu/influxdb``
- Kafdrop UI: ``https://usdf-rsp.slac.stanford.edu/kafdrop``
- Kafka boostrap server:
  (not yet available)
- Schema Registry: ``http://sasquatch-schema-registry.sasquatch:8081`` (cluster internal only)
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
- Schema Registry: ``http://sasquatch-schema-registry.sasquatch:8081`` (cluster internal only)
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
- Schema Registry:
  - ``http://sasquatch-schema-registry.sasquatch:8081`` (cluster internal)
  - ``https://tucson-teststand.lsst.codes/schema-registry`` (cluster external)
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
- Schema Registry: ``http://sasquatch-schema-registry.sasquatch:8081`` (cluster internal only)
- Kafka REST proxy API: ``https://base-lsp.lsst.codes/sasquatch-rest-proxy``
