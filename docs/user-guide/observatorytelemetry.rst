.. _observatory-telemetry:

########
Overview
########

Observatory telemetry, events and commands are recorded in the Engineering and Facilities Database (EFD) enabling real-time monitoring
of the Observatory subsystems using Chronograf :ref:`dashboards <dashboards>` and :ref:`alerts <alerts>`.

Analysis of the EFD data is done in the notebook aspect of the RSP using the :ref:`EFD client <efdclient>`.

At the Summit environment, the nominal retention period for the EFD data is 30 days.
The EFD data is replicated to the USDF environment whitin a few seconds.
The USDF the environment where the project staff should connect to perform their analysis without interfering with the Summit operations, including trend analysis on historical data.

In Sasquatch, the EFD topics are in the ``lsst.sal`` namespace and their schemas are defined by `SAL`_.

.. _SAL: https://ts-xml.lsst.io/sal_interfaces/index.html