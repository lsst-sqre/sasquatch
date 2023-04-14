.. _dashboards:

##########
Dashboards
##########

This section collects best practices for creating dashboards in Chronograf based on our experience at Rubin Observatory.

Read more on how to create dashboards in the `Chronograf documentation`_.

.. _Chronograf documentation: https://docs.influxdata.com/chronograf/v1.10/guides/create-a-dashboard/#build-a-dashboard

Visualization types
===================

See the `visualization types`_ avaibale in Chronograf.

.. _visualization types: https://docs.influxdata.com/chronograf/v1.10/guides/visualization-types/

Time series of physical variables like temperature, pressure, etc are correlated data points.
For this type of data prefer using a line graph or a line graph + single stat visualization types.
The single stat always corresponds to the most recent value in the time series.

Time series of uncorrelated data like events are better visualized using the bar chart visualization type.

In general, the best way to identify the best visualization type is by questioning the data.
Bar charts are also useful to visualize gaps in the data.

Write efficient dashboard queries
=================================

Dashboard queries are used to build visualizations in Chronograf.
You can write dashboard queries in InfluxQL and Flux.
This section covers the basics of InfluxQL a SQL-like query language for InfluxDB.
The :ref:`advanced` section introduces the use of Flux for creating dashboards.

.. note::

   Keep in mind that a single dashboard might execute tens or even hundreds of queries.
   These queries need to return fast specially if dashboards are configured to refresh every few seconds.

When creating dashboard queries always constrain the queries by a time range.
You will notice that the query editor automatically adds the following clause for you:

.. code:: sql

   WHERE time > :dashboardTime: AND time < :upperDashboardTime:

these are pre-defined template variables that correspond to the time range configured in the date picker.
This way your charts will respond consistently when changing the time range in the date picker, but more importantly, queries constrained by time return faster in InfluxDB.

Consider using aggregation functions like ``mean()`` to sample the time series in an appropriate time grid using the clause:

.. code:: sql

   GROUP BY time(:interval:)

Chronograf will automatically set the value of ``:interval:`` based on the selected time range.
The idea behind the ``:interval:`` template variable is that you don't need to return high resolution data for visualization if you select a large time range.

Use the :guilabel:`Show template values` button in the query editor UI to inspect the actual values of template variables in your query.

Use custom template variables to build interactive dashboards
=============================================================

When creating a dashboard, you can create custom template variables to parametrize your queries and visualizations.
With custom template variables you can create interactive dashboards, when you create a template variable it becomes available
in the Chronograf UI for selection.

Any substring in your query can be parametrized by template variables.

A typical use of template variables is to label a particular time range of interest corresponding to a test performed at the observatory or to an event.

See the `M2 Functional Testing`_ dashboard for an example.
There, a ``Map`` template variable maps the test name to the time range when the test was performed.
The query looks like:

.. code:: sql

   SELECT mean("axialForceMeasured1") AS "mean_axialForceMeasured1",
          mean("axialForceMeasured2") AS "mean_axialForceMeasured2",
          mean("axialForceMeasured14") AS "mean_axialForceMeasured14"
   FROM "efd"."autogen"."lsst.sal.MTM2.axialForcesMeasured"
   WHERE :m2_test: GROUP BY time(1s)

An example of value for the ``:m2_test:`` template variable could be:

.. code::

   m2 actuator stroke A4 test,"time >= '2020-03-05 18:52:00' AND time <= '2020-03-05 19:21:00'"

Then, by selecting ``m2 actuator stroke A4 test`` in the UI, you jump straight to when the test was performed.

.. vimeo:: 817809848

Read more about `custom template variables`_ in the Chronograf documentation  .

.. _custom template variables: https://docs.influxdata.com/chronograf/v1.10/guides/dashboard-template-variables/#use-template-variables
.. _M2 Functional Testing: https://usdf-rsp.slac.stanford.edu/chronograf/sources/1/dashboards/6


Display multiple graphs in one chart
====================================

Sometimes it is useful to display multiple graphs in a single chart.
Additional graph queries can be added by using the ``+`` button in the query editor.

Strip charts
============

Multiple time series charts (strip charts) are better visualized if the time axis is aligned.
To align the time axis use the ``GROUP BY time(:interval:)`` clause with the same ``:interval:`` in each chart query to sample the data in the same time grid.


Use linked tables to correlate metrics and events
=================================================

An easy way to visualize events and correlate them with metrics or telemetry data is by using a linked table.
In Chronograf, tables are linked to charts via the time column.


.. note::

   Chronograf provides a `log viewer`_ tool that could be used to visualize CSC log events.
   To use the log viewer tool in Chronograf, data needs to be recorded in a specific measurement and follow the syslog data format.
   DM-31618 explores this possibility.


.. _log viewer: https://docs.influxdata.com/chronograf/v1.10/guides/analyzing-logs/


.. _advanced:

Advanced dashboards with Flux
=============================

Flux is a data scripting language that provides an extensive library for time series data manipulation.

Flux is good for querying and combining fields from multiple InfluxDB measurements, something that's not possible with InfluxQL.

This section walks you through the Flux code used to create the table in the `MT CSC State Transitions`_ dashboard.

.. _MT CSC State Transitions: https://usdf-rsp.slac.stanford.edu/chronograf/sources/1/dashboards/12

The following will query the ``efd`` in the selected time range and use the ``filter()`` function to get the ``summaryState`` field from the all the measurements that match the ``lsst.sal.MT.*.logevent_summaryState`` regexp.

.. code::

   from(bucket: “efd/autogen”)
      |> range(start: dashboardTime)
      |> filter(fn: (r) => r._measurement =~ /lsst.sal.MT.*.logevent_summaryState/ and (r._field == "summaryState"))

Think about this as a data pipeline, the symbol ``|>`` is called the pipe forward operator.
In each step, Flux creates one or more tables that are used as input for the next step.

In the example, the resulting tables have the ``summaryState`` values for each CSC in the selected time range.
To get the current state for each CSC use the ``last()`` function.

.. code::

   from(bucket: “efd/autogen”)
      |> range(start: dashboardTime)
      |> filter(fn: (r) => r._measurement =~ /lsst.sal.MT.*.logevent_summaryState/ and (r._field == "summaryState"))
      |> last()

Next use the ``strings`` package for string manipulation.
The  ``strings.split()`` function extracts the CSC name from the measurement and the ``map()`` function applies that to each row.
The result is assigned to a new column ``csc``:

.. code::

   import "strings"

   from(bucket: “efd/autogen”)
      |> range(start: dashboardTime)
      |> filter(fn: (r) => r._measurement =~ /lsst.sal.MT.*.logevent_summaryState/ and (r._field == "summaryState"))
      |> last()
      |> map(fn: (r) => ({
         r with
         csc: strings.split(v: r._measurement, t: ".")[2]
         })
      )

The CSC state is obtained from its numerical value and assigned to the ``state`` column.

.. code::

   import "strings"

   from(bucket: “efd/autogen”)
      |> range(start: dashboardTime)
      |> filter(fn: (r) => r._measurement =~ /lsst.sal.MT.*.logevent_summaryState/ and (r._field == "summaryState"))
      |> last()
      |> map(fn: (r) => ({
         r with
         csc: strings.split(v: r._measurement, t: ".")[2],
         state:
            if r._value == 5 then "5 (STANDBY)"
            else if r._value == 4 then "4 (OFFLINE)"
            else if r._value == 3 then "3 (FAULT)"
            else if r._value == 2 then "2 (ENABLED)"
            else if r._value == 1 then "1 (DISABLED)"
            else "UNKNOWN"
      )}
   )

Flux can also be used to perform calculations on fields.
There are many functions built-in into the language already.

The ``duration()`` function computes the duration of the current state and formats the output into a string with the approximated duration in minutes:

.. code::

   import "strings"

   from(bucket: “efd/autogen”)
      |> range(start: dashboardTime)
      |> filter(fn: (r) => r._measurement =~ /lsst.sal.MT.*.logevent_summaryState/ and (r._field == "summaryState"))
      |> last()
      |> map(fn: (r) => ({
         r with
         csc: strings.split(v: r._measurement, t: ".")[2],
         state:
            if r._value == 5 then "5 (STANDBY)"
            else if r._value == 4 then "4 (OFFLINE)"
            else if r._value == 3 then "3 (FAULT)"
            else if r._value == 2 then "2 (ENABLED)"
            else if r._value == 1 then "1 (DISABLED)"
            else "UNKNOWN",
         duration: strings.splitAfter(v: string(v: duration(v: uint(v: now()) - uint(v: r._time))), t: "m")[0]
      })
   )
   |> keep(columns: ["csc", "state", "_time", "duration"])

where ``_time`` is the timestamp of the last state transition.

Finally, use the ``keep()`` function to keep only the columns of interest in the final table.
