
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

To perform queries directly using InfluxQL, you can make use of the ``influx_client.query()`` method in conjunction with the EFD client.

For a comprehensive understanding of the InfluxQL query syntax, we recommend referring to the `InfluxQL documentation`_.

.. code::

   from lsst_efd_client import EfdClient
   efd = EfdClient("usdf_efd")

   query = '''SELECT vacuum FROM "lsst.sal.ATCamera.vacuum" WHERE time > '2023-04-20' '''

   await client.influx_client.query(query)

InfluxQL is picky about `single vs. double quotes`_.
The rule of thumb is to use double quotes around topic names that have special characters like ``.`` and single quotes around timestamps.

Use the ``now()`` function to query data with time relative the current time in UTC.

.. code::

   query = '''SELECT vacuum FROM "lsst.sal.ATCamera.vacuum" WHERE time > now() - 6h '''


Example notebooks
-----------------

.. grid:: 3

   .. grid-item-card:: Querying the EFD with InfluxQL
      :link: https://github.com/lsst-sqre/sasquatch/blob/main/docs/user-guide/notebooks/UsingInfluxQL.ipynb
      :link-type: url

      Learn how to use the EFD client and InfluxQL to query EFD data.

   .. grid-item-card:: Downsampling data with the GROUP BY time() clause
      :link: https://github.com/lsst-sqre/sasquatch/blob/main/docs/user-guide/notebooks/Downsampling.ipynb
      :link-type: url

      Learn how to downsample data with InfluxQL.

   .. grid-item-card:: Chunked queries: Efficient Data Retrieval
      :link: https://github.com/lsst-sqre/sasquatch/blob/main/docs/user-guide/notebooks/ChunkedQueries.ipynb
      :link-type: url

      Learn how to return chunked responses with the EFD client.

.. _single vs. double quotes: https://www.influxdata.com/blog/tldr-influxdb-tech-tips-july-21-2016/
.. _InfluxQL documentation: https://docs.influxdata.com/influxdb/v1.8/query_language/explore-data/