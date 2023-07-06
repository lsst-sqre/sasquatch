.. _observatory-telemetry:

########
Overview
########

Telemetry, events, and commands from the observatory are recorded in the Engineering and Facilities Database (EFD), enabling real-time monitoring of subsystems using Chronograf dashboards and alerts.

Data analysis of the EFD is conducted in the RSP notebook aspect, utilizing the EFD client.

In the Summit environment, the EFD data is retained for a nominal period of 30 days.
The data is then replicated to the USDF environment, allowing project staff to perform analysis without disrupting Summit operations, including trend analysis on historical data.

In Sasquatch, the EFD topics fall under the ``lsst.sal`` namespace, with their schemas defined by `SAL`_.

.. _SAL: https://ts-xml.lsst.io/sal_interfaces/index.html