:og:description: Rubin Observatory's telemetry and metrics service
:html_theme.sidebar_secondary.remove:

.. toctree::
   :hidden:

   User guide <user-guide/index>
   Environments <environments>
   Administrators <admin/index>
   FAQ <faq>
   Resources <resources>

#########
Sasquatch
#########

Sasquatch is the Rubin Observatory's service for metrics and telemetry data.

Built on Apache Kafka and InfluxDB, Sasquatch offers an efficient solution for collecting, storing and querying time-series data.

See the :ref:`user-guide` for more information on Sasquatch and how to use it within the different Rubin Observatory :ref:`environments`.

Sasquatch is deployed through Phalanx_.


.. grid:: 2
   :gutter: 3

   .. grid-item-card:: User Guide
      :link: user-guide/index
      :link-type: doc

      Learn how to access, visualize and send data to Sasquatch.

   .. grid-item-card:: Environments
      :link: environments
      :link-type: doc

      See the different environments where Sasquatch is deployed.

   .. grid-item-card:: Administrators
      :link: admin/index
      :link-type: doc

      Learn how administer and troubleshoot Sasquatch.

.. _Phalanx: https://phalanx.lsst.io
