.. _organizations:

#############
Organizations
#############

In Chronograf organizations are used to control access to shared resources such as dashboards and alerts.

In the Chronograf UI, the user’s current organization is highlighted in the Organizations list under the User context menu.

When a user has a role in more than one organization, that user can switch to another organization by selecting the desired option from the Organizations list.

The current organizations configured at the USDF environment are:

- ``Observatory Telemetry``
- ``Pipeline Metrics``
- ``Sandbox``

``Observatory Telemetry`` is the default organization when a user first log in into Chronograf at USDF.
In that organization, users have ``editor`` role to create dashboards and alert rules.

The ``Pipeline Metrics`` and the ``Sandbox`` organizations are also available.
The ``Sandbox`` organization is an area for experimenting with Chronograf without the risk of interfering with existing dashboards.

Read more about Organizations and user roles in the `Chronograf documentation`_.
