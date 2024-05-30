
.. _efdclient:

#####################
The EFD Python client
#####################

The EFD client built on top of the `aioinflux`_ library and provides a high-level API to interact with the EFD.

The EFD client is designed to be used in the RSP notebook aspect.
For services that need to access the EFD, see how to query the :ref:`InfluxDB API <influxdbapi>` directly.

For example, from a notebook running at the `USDF RSP`_ you can instantiate the EFD client using:

.. code::

   from lsst_efd_client import EfdClient
   client = EfdClient("usdf_efd")

   await client.get_topics()

``usdf_efd`` is an alias for the InfluxDB instance at USDF. With that the EFD client discovers the InfluxDB URL, database and credentials to connect to that
environment.

If you are using the EFD client on another environment, see the corresponding alias in the :ref:`environments <environments>` page.

Learn more about the methods available in the `documentation`_.

.. _documentation: https://efd-client.lsst.io

InfluxQL
--------

To perform queries directly using InfluxQL, you can make use of the ``influx_client.query()`` method in conjunction with the EFD client.

For a comprehensive understanding of the InfluxQL query syntax, we recommend referring to the `InfluxQL documentation`_.

.. code::

   from lsst_efd_client import EfdClient
   client = EfdClient("usdf_efd")

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

.. _aioinflux: https://aioinflux.readthedocs.io/
.. _USDF RSP: https://usdf-rsp.slac.stanford.edu/
.. _single vs. double quotes: https://www.influxdata.com/blog/tldr-influxdb-tech-tips-july-21-2016/
.. _InfluxQL documentation: https://docs.influxdata.com/influxdb/v1.8/query_language/explore-data/
