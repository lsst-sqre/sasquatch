.. request-exceeded-time-limit-error:


“Request exceeded user-specified time limit" error when Telegraf consumes kafka topics
======================================================================================


In Sasquatch, you might see the ``Request exceeded user-specified time limit`` error in Telegraf when consuming Kafka topics.
This error means the broker didn’t complete the request within the timeout the client expects.



.. code::

  2025-10-27T22:36:52Z E! [inputs.kafka_consumer] Error in plugin: channel:
  kafka: error while consuming lsst.sal.MTM2.temperature/26:
  kafka server: Request exceeded the user-specified time limit in the request


Mitigations
-----------

Reduce request size
^^^^^^^^^^^^^^^^^^^

``consumer_fecth_default`` sets the number of bytes to fetch from the broker in each request.
Reduce ``consumer_fetch_default`` so Telegraf receives smaller payloads more frequently.
This can be set per Telegraf Kafka consumer in the environment ``values.yaml`` file and may vary depending on data volume being handled.

Example:

.. code:: yaml

  telegraf:
    kafkaConsumers:
      m1m3ts:
        enabled: true
        consumer_fetch_default: "500KB"  # reduce to receive smaller payloads, default is 1MB
        database: "efd"
        topicRegexps: |
          [ "lsst.sal.MTM1M3TS" ]


Increase Telegraf processing time
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``max_processing_time`` sets the maximum amount of time the consumer should take to process messages.
This can be set per Telegraf Kafka consumer in the environment ``values.yaml`` file:

.. code:: yaml

  telegraf:
    kafkaConsumers:
      m1m3ts:
        enabled: true
        max_processing_time: "10s"  # increase to tolerate longer processing times, default is 1s
        database: "efd"
        topicRegexps: |
          [ "lsst.sal.MTM1M3TS" ]

