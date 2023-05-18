
.. _efdclient:

#####################
The EFD Python client
#####################

The EFD Python client is based on `aioinflux`_  an asyncio client to access EFD data from a notebook in the RSP.

For example, at the USDF environment you can instantiate the EFD client using:

.. code::

   from lsst_efd_client import EfdClient
   efd = EfdClient("usdf_efd")

   await efd.get_topics()

where ``usdf_efd`` is an alias to the :ref:`environment <environments>`.
It helps to discover the InfluxDB API URL and the credentials to connect to the EFD database.

The EFD Python client provides convenience methods for accessing EFD data.
Read more about the methods available in the `EFD client documentation`_.

.. _EFD client documentation: https://efd-client.lsst.io
.. _aioinflux: https://aioinflux.readthedocs.io/en/stable/


InfluxQL
--------

If you need to query the EFD using InfluxQL you can instantiate the underlying `aioinflux`_ with:

.. code::

   from lsst_efd_client import EfdClient
   efd = EfdClient("usdf_efd")

   query = '''SELECT url, id FROM "lsst.sal.Electrometer.logevent_largeFileObjectAvailable" WHERE time > '2023-04-20' '''

   await efd.influx_client.query(query)


InfluxQL is picky about `single vs. double quotes`_.
The rule of thumb is to use double quotes around topic names that have special characters like ``.`` and single quotes around timestamps.

Use the ``now()`` function to query data with time relative the current time in UTC.

.. code::

   query = '''SELECT url, id FROM "lsst.sal.Electrometer.logevent_largeFileObjectAvailable" WHERE time > now() - 30d '''

Read more about the InfluxQL query syntax in the `InfluxQL documentation`_.

.. _single vs. double quotes: https://www.influxdata.com/blog/tldr-influxdb-tech-tips-july-21-2016/
.. _InfluxQL documentation: https://docs.influxdata.com/influxdb/v1.8/query_language/explore-data/