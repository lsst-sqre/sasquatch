.. _tags-vs-fields:

InfluxDB tags versus fields
===========================

When writing data to InfluxDB, you have to decide which values should be tags and which should be fields.

.. hint::

   If the value is likely to be used in a "WHERE" clause in queries, and if it has fewer than 10,000 possible values, it should be a tag.

Tags are indexed, which means you can use them as filters efficiently in InfluxDB queries.

It can be difficult to decide what should be a tag and what should be a field, but here are some guidelines:

* If it's a value that will be aggregated and graphed over time, like the duration of a query, then it should be a field, because you'll never be filtering on it.
* If it's metadata like which app generated the event, then it should be a tag.

See also the official InfluxDB documentation on `tags versus fields`_ for more information.

One thing to keep in mind is that tags shouldn't have a large number of distinct values.
That could lead to a `high-cardinality`_ dataset in InfluxDB, especially when combined with other tags with many distinct values.
A high-cardinality dataset could greatly increase the memory usage of the InfluxDB instance and decrease query performance across the board.

How many values is too many?
There's not a lot of concrete advice on that, and it depends a lot on other tags and the composition of the entire dataset, so let's say **10,000** for now. This means if you have a username on an event, it can be a tag.
