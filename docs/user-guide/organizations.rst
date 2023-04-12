.. _organizations:

#############
Organizations
#############

In Chronograf organizations are used to control acess to shared resources such as databases, dashboards and alerts to users.

In the Chronograf UI, the user’s current organization is highlighted in the Organizations list under the User context menu.

When a user has a role in more than one organization, that user can switch to another organization by selecting the desired option from the Organizations list.

The current organizations configured at the USDF environment are:

- ``Observatory telemetry``
- ``Sandbox``

``Observatory Telemetry`` is the default organization when a user first log in into Chronograf at USDF.
In that organization, users have ``viewer`` role to the ``efd`` database and dashboards which are replicated
from the Summit environment.

The ``Sandbox`` organization is an area for experimenting with Chronograf without the risk of interfering with existing resources.
In this organization, users have ``editor`` role so they can create dashboards and alerts with access to all the existing databases.

When we start recording metrics for Data Release Processing and Alert Production in Sasquatch we plan on creating organizations for those contexts as well.

Read more about Organizations and user roles in the `Chronograf documentation`_.

.. _Chronograf documentation: https://docs.influxdata.com/chronograf/v1.10/administration/managing-organizations/#about-chronograf-organizations
