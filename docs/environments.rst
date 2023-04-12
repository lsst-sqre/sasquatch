:og:description: Description of the Sasquatch environments.

.. _environments:

############
Environments
############

The table below summarizes the Sasquatch environments and their main entry points.

+---------------------------+---------------------------------------------------+--------------------------+----------------+
| **Sasquatch Environment** | **Chronograf UI**                                 | **EFD Client alias**     | **VPN access** |
+===========================+===================================================+==========================+================+
| :ref:`Summit<summit>`     | https://summit-lsp.lsst.codes/chronograf          | ``summit_efd``           | Chile VPN      |
+---------------------------+---------------------------------------------------+--------------------------+----------------+
| :ref:`USDF<usdf>`         | https://usdf-rsp.slac.stanford.edu/chronograf     | ``usdf_efd``             | Not required   |
+---------------------------+---------------------------------------------------+--------------------------+----------------+
| :ref:`USDF dev<usdfdev>`  | https://usdf-rsp-dev.slac.stanford.edu/chronograf | ``usdfdev_efd``          | Not required   |
+---------------------------+---------------------------------------------------+--------------------------+----------------+
| :ref:`TTS<tts>`           | https://tucson-teststand.lsst.codes/chronograf    | ``tucson_teststand_efd`` | NOIRLab VPN    |
+---------------------------+---------------------------------------------------+--------------------------+----------------+
| :ref:`BTS<bts>`           | https://base-lsp.lsst.codes/chronograf            | ``base_efd``             | Chile VPN      |
+---------------------------+---------------------------------------------------+--------------------------+----------------+

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
- Kafka brokers:

  - ``sasquatch-summit-kafka-0.lsst.codes``
  - ``sasquatch-summit-kafka-1.lsst.codes``
  - ``sasquatch-summit-kafka-2.lsst.codes``

- Kafka bootstrap server: ``sasquatch-summit-kafka-bootstrap.lsst.codes``
- Kafka REST proxy API: ``https://summit-lsp.lsst.codes/sasquatch-rest-proxy``

.. _usdf:

USDF
----

Sasquatch production environment at the USDF.

Intended audience: Project staff.

- Chronograf: ``https://usdf-rsp.slac.stanford.edu/chronograf``
- InfluxDB HTTP API: ``https://usdf-rsp.slac.stanford.edu/influxdb``
- Kafdrop UI: ``https://usdf-rsp.slac.stanford.edu/kafdrop``
- Kafka brokers:
  (not yet available)
- Kafka boostrap server:
  (not yet available)
- Kafka REST proxy API: ``https://usdf-rsp.slac.stanford.edu/sasquatch-rest-proxy``

.. _usdfdev:

USDF dev
--------

Sasquatch development environment at USDF.

Intended audience: Project staff.

- Chronograf: ``https://usdf-rsp-dev.slac.stanford.edu/chronograf``
- InfluxDB HTTP API: ``https://usdf-rsp-dev.slac.stanford.edu/influxdb``
- Kafdrop UI: ``https://usdf-rsp-dev.slac.stanford.edu/kafdrop``
- Kafka brokers:
  (not yet available)
- Kafka boostrap server:
  (not yet available)
- Kafka REST proxy API: ``https://usdf-rsp-dev.slac.stanford.edu/sasquatch-rest-proxy``

.. _tts:

Tucson Test Stand (TTS)
-----------------------

Sasquatch production environment at the Tucson test stand.

Intended audience: Telescope & Site team.

- Chronograf: ``https://tucson-teststand.lsst.codes/chronograf``
- InfluxDB HTTP API: ``https://tucson-teststand.lsst.codes/influxdb``
- Kafdrop UI: ``https://tucson-teststand.lsst.codes/kafdrop``
- Kafka brokers:

  - ``sasquatch-tts-kafka-0.lsst.codes``
  - ``sasquatch-tts-kafka-1.lsst.codes``
  - ``sasquatch-tts-kafka-2.lsst.codes``

- Kafka bootstrap server: ``sasquatch-tts-kafka-bootstrap.lsst.codes``
- Kafka REST proxy API: ``https://tucson-teststand.lsst.codes/sasquatch-rest-proxy``


.. _bts:

Base Test Stand (BTS)
---------------------

Sasquatch production environment at the Base test stand.

Intended audience: Telescope & Site team.

- Chronograf: ``https://base-lsp.lsst.codes/chronograf``
- InfluxDB HTTP API: ``https://base-lsp.lsst.codes/influxdb``
- Kafdrop UI: ``https://base-lsp.lsst.codes/kafdrop``
- Kafka brokers:

  - ``sasquatch-base-kafka-0.lsst.codes``
  - ``sasquatch-base-kafka-1.lsst.codes``
  - ``sasquatch-base-kafka-2.lsst.codes``

- Kafka bootstrap server: ``sasquatch-base-kafka-bootstrap.lsst.codes``
- Kafka REST proxy API: ``https://base-lsp.lsst.codes/sasquatch-rest-proxy``
