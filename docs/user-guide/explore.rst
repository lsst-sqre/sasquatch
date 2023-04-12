.. _explore:

################
Data Exploration
################

The Chronograf Explore tool allows you to browse databases and topics in InfluxDB.

InfluxDB provides an SQL-like query language called `InfluxQL`_ and a more powerful data scripting language called `Flux`_.
Both languages can be used in the Data Explore tool to query your data.

See :ref:`environments` for the Chronograf URL in each Sasquatch environment.

For example, to query the ``lsst.example.skyFluxMetric`` metric created in the previous section, go to `Chronograf at USDF dev`_, and use the following InfluxQL query in the Explore tool:

.. code::

    SELECT "meanSky" FROM "lsst.example"."autogen"."lsst.example.skyFluxMetric"

where ``lsst.example`` is the InfluxDB database, ``autogen`` is the defualt InfluxDB retention policy and ``lsst.example.skyFluxMetric`` is the InfluxDB measurement for this metric.

Read more about the Chronograf Explore tool in the `Chronograf documentation`_.

.. _InfluxQL: https://docs.influxdata.com/influxdb/v1.8/query_language/
.. _Flux: https://docs.influxdata.com/influxdb/v1.8/flux/
.. _Chronograf at USDF dev: https://usdf-rsp-dev.slac.stanford.edu/chronograf/
.. _Chronograf documentation: https://docs.influxdata.com/chronograf/v1.10/guides/querying-data/
