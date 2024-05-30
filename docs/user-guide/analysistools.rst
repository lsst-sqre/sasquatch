.. _analysis-tools:

######################
Analysis Tools metrics
######################

The `Analysis Tools`_ package is used to create science performance metrics from the `LSST Pipelines`_ outputs.

Currently, the Analysis Tools metrics are dispatched to the ``usdfdev_efd`` environment under the ``lsst.dm`` namespace.

The :ref:`EFD Python client <efdclient>` can be used to query them.

For example, to get the list of analysis tools in the ``lsst.dm`` namespace, you can use:

.. code:: python

    from lsst_efd_client import EfdClient

    client = EfdClient("usdfdev_efd", db_name="lsst.dm")

    await client.get_topics()


Example notebooks
=================

.. grid:: 3

   .. grid-item-card:: Analysis Tools metrics
      :link: https://github.com/lsst-sqre/sasquatch/blob/main/docs/user-guide/notebooks/AnalysisTools.ipynb
      :link-type: url

      Learn how to query Analysis Tools metrics using the EFD Python client and InfluxQL.


.. _LSST Pipelines: https://pipelines.lsst.io
.. _Analysis Tools: https://pipelines.lsst.io/v/daily/modules/lsst.analysis.tools/index.html
