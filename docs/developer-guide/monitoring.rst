.. _monitoring:

##########
Monitoring
##########

This page consolidates information about monitoring Sasquatch at the Summit and USDF environments.

Summit
------

**Strimzi Kafka**
   - `Kafka cluster health, broker level throughput, memory and cpu usage <https://grafana.ls.lsst.org/d/eeav6ekv85f5sd/strimzi-kafka?orgId=1&from=now-30m&to=now&timezone=browser&var-DS_PROMETHEUS=mimir&var-prom_cluster=yagan.cp&var-kubernetes_namespace=sasquatch&var-strimzi_cluster_name=sasquatch&var-pool_name=$__all&var-kafka_broker=$__all&var-kafka_topic=$__all&var-kafka_partition=$__all&refresh=1m>`_
   - `Topic level throughput, under replicated partitions, ISRs, and consumer lag  <https://grafana.ls.lsst.org/d/deav6eunobnk0f/strimzi-kafka-exporter?orgId=1&from=now-30m&to=now&timezone=browser&var-DS_PROMETHEUS=mimir&var-prom_cluster=yagan.cp&var-kubernetes_namespace=sasquatch&var-strimzi_cluster_name=sasquatch&var-consumergroup=$__all&var-topic=$__all&refresh=1m>`_
   - `Broker latency metrics <https://grafana.ls.lsst.org/d/deevzz8wv0074a/strimzi-kafka-broker-latency?orgId=1&from=now-30m&to=now&timezone=browser&var-namespace=sasquatch&var-cluster=yagan.cp&var-kafka_broker=$__all>`_

**Telegraf Connectors**
   - `Summit connectors memory usage, buffer size, throughput, errors <https://summit-lsp.lsst.codes/chronograf/sources/1/dashboards/371?refresh=Paused&lower=now%28%29%20-%206h>`_

**InfluxDB**
   - `Summit InfluxDB CPU and Memory usage, network <https://grafana.ls.lsst.org/d/6581e46e4e5c7ba40a07646515ef7b35/kubernetes-compute-resources-pod?orgId=1&from=now-1h&to=now&timezone=utc&var-datasource=default&var-cluster=yagan.cp&var-namespace=sasquatch&var-pod=sasquatch-influxdb-enterprise-data-0&refresh=10s>`_
   - `Summit InfluxDB writes and query load <https://summit-lsp.lsst.codes/chronograf/sources/1/dashboards/636?refresh=Paused&lower=now%28%29%20-%2024h>`_

USDF
----

**Slack alerts**
   - #ops-usdf-alerts

**Telegraf Connectors**
   - `USDF connectors memory usage, buffer size, throughput, errors <https://usdf-rsp.slac.stanford.edu/chronograf/sources/1/dashboards/116?refresh=Paused&lower=now%28%29%20-%2015m>`_
   - `Telegraf connector timeouts <https://grafana.slac.stanford.edu/d/bf0ecc79-046e-4632-9c43-281350dcfaf2/sasquatch-timeouts?orgId=1&from=now-7d&to=now&timezone=browser>`_

**InfluxDB**
   - `USDF InfluxDB CPU and Memory usage, network <https://grafana.slac.stanford.edu/d/dd71bcda-7744-4a86-bb10-f3cb65a1255c/kubernetes-workload-state?var-bin=2m&orgId=1&from=now-1h&to=now&timezone=America%2FLos_Angeles&var-node=$__all&var-namespace=vcluster--usdf-rsp&var-topk=10&var-filter_by_pod=sasquatch-influxdb-enterprise-active.%2A&var-filter_by_container=.%2A>`_
   - `USDF InfluxDB writes and query load <https://usdf-rsp.slac.stanford.edu/chronograf/sources/1/dashboards/67?refresh=Paused&lower=now%28%29%20-%2024h>`_
   - `Slow queries in the last 24h <https://grafana.slac.stanford.edu/d/ff43qxi8owpa8e/sasquatch-slow-queries?orgId=1&from=now-24h&to=now&timezone=browser>`_


Summit - USDF connection
------------------------

**Slack alerts**
   - #status-efd

**MirrorMaker**
   - `Summit replication <https://usdf-rsp.slac.stanford.edu/kafdrop/>`_
   - `MM2 timeouts <https://grafana.slac.stanford.edu/d/bf0ecc79-046e-4632-9c43-281350dcfaf2/sasquatch-timeouts?orgId=1&from=now-7d&to=now&timezone=browser>`_

**Summit - USDF connection**
   - `Perfsonar <https://ps-cma.amlight.net/grafana/d/aaatqaA0QfVk/vera-rubin-observatory-perfsonar-matrix?orgId=1>`__

