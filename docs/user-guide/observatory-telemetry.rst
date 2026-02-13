.. _observatory-telemetry:

###########################
Observatory telemetry (EFD)
###########################

Rubin Observatory telemetry data supports real-time monitoring of the observatory systems at the Summit and is also replicated to the US Data Facility (USDF) for long-term storage and analysis.
This data is stored in the Engineering and Facility Database (EFD).

In Sasquatch, Rubin Observatory telemetry data is stored in the Engineering and Facility Database (EFD):

- ``efd``: telemetry data published by the Observatory Control System, with schemas defined by `SAL interfaces`_.

Other telemetry data include:

- ``lsst.ATCamera``, ``lsst.CCCamera``, and ``lsst.MTCamera``: telemetry data published by the Camera Control System (CCS).
- ``lsst.obsenv``: observing environment information.
