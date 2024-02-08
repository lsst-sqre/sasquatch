.. _observatory-telemetry:

########
Overview
########

Rubin Observatory generates a large amount of engineering data, which is stored in the Engineering and Facilities Database (EFD).

The EFD data is used at the Summit for real-time monitoring of the observatory systems using Chronograf dashboards and alerts.

The EFD data is also replicated to the US Data Facility (USDF) for long-term storage and analysis.

Data analysis of the EFD is conducted in the RSP notebook aspect, utilizing the EFD Python client.

In Sasquatch, the EFD topics fall under the ``lsst.sal`` namespace, with their schemas defined by `SAL`_.

.. _SAL: https://ts-xml.lsst.io/sal_interfaces/index.html
