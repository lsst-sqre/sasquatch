.. _influxdb-stale-measurements:

###########################
InfluxDB stale measurements
###########################

It is useful to be able to find measurements in an InfluxDB database that
haven't recieved any data in a while.
This might be because:

* They are no longer needed
* We have started writing the same data to a different measurement

You can find these measurements with the ``sasquatch influxdb get-stale-measurements`` command.

If a measurement is no longer needed, it can be deleted.
If the destination for the measurement's data has changed, it can still be deleted if we don't have any use for the old data.
If we do have use for the old data, the data can be migrated to the new measurement by exporting the old measurement to a line protocol file and then using the :ref:`influxdb-migration` commands to transform it to fit the schema of the new measurement and load it into the new measurement.
