
.. _timestamps:

#######################
Working with timestamps
#######################

Ideally, each CSC records the time at which the telemetry being reported was measured.
The CSC timestamp field can be found by inspecting the topic schema from the `SAL documentation`_ or using the EFD client.

For example, for the ``MTMount.azimuth`` telemetry topic:

.. code:: Python

	from lsst_efd_client import EfdClient
	client = EfdClient("usdf_efd")

	schema = await client.get_schema("lsst.sal.MTMount.azimuth")
	schema


.. _SAL documentation: https://ts-xml.lsst.io/sal_interfaces/index.html

From which you see, among the other fields:

.. code::

   name        description                                               units      aunits   is_array

   timestamp   Time at which the data was measured (TAI, unix seconds).  second     s        False

When the CSC timestamp is not present, you can use a SAL timestamp.

SAL timestamps are added automatically by SAL and have the ``private_`` prefix.
In particular, the ``private_sndStamp`` timestamp is the time at which the message was published by the CSC in TAI, which should be very close to the time at which the telemetry was measured.
In fact, many telemetry topics rely on the ``private_sndStamp`` timestamp for that.

The ``private_sndStamp`` timestamp is also converted to UTC and recorded in the ``private_efdStamp`` field, which is used as the time index in the EFD.

Chronograf
==========

Chronograf dashboards display time in UTC *or* in your local timezone.
This can be changed by using the :guilabel:`UTC/Local` toggle in the Chronograf UI.

The function ``now()`` in InfluxQL returns time in UTC and can be used to query data relative to the current timestamp:

.. code:: SQL

   SELECT "actualPosition" FROM "efd"."autogen"."lsst.sal.MTMount.azimuth" WHERE time > now() - 1h

See `Time Syntax`_ for the time syntax when querying the EFD with InfluxQL.

.. _Time Syntax: https://docs.influxdata.com/influxdb/v1.8/query_language/explore-data/#time-syntax


EFD client
==========

When querying the EFD with the EFD client, it is a good practice to convert all timestamps to UTC first.

Suppose you read the time of the start and end of an observation from the image header in TAI.
Use the `astropy.time`_ package to convert time from TAI to UTC.

.. code:: Python

	from astropy.time import Time

	start_time = Time(header["DATE-BEG"], scale="tai").utc
	end_time = Time(header["DATE-END"], scale="tai").utc

Then use the UTC timestamps in your EFD query:

.. code:: Python

	actual_position = await client.select_time_series("lsst.sal.MTMount.azimuth",  ["actualPosition"], start_time, end_time)


See the `EFD client`_ documentation for other ways to query time ranges.


.. _astropy.time: https://docs.astropy.org/en/stable/time/index.html
.. _EFD client: https://efd-client.lsst.io