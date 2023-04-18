
.. _efdclient:

##############
The EFD client
##############

The EFD client is a Python client to access the EFD data from a notebook in the RSP.

For example, at the USDF environment you can instantiate the EFD client using:

.. code::

   from lsst_efd_client import EfdClient
   efd = EfdClient('usdf_efd')

   await efd.get_topics()

where ``usdf_efd`` is an alias to the :ref:`environment <environments>`.
It helps to discover the InfluxDB API URL and the credentials to connect to the EFD database.

Read more about the methods available in the `EFD client`_  documentation.

.. _EFD client: https://efd-client.lsst.io

