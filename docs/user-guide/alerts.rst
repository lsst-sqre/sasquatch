.. _alerts:

######
Alerts
######

Alert rules are created in the Chronograf UI and can be used to send notifications to a Slack channel when certain conditions are met, for example when a metric exceeds a certain threshold.

Chronograf supports three types of alerts:

- **Threshold**: Triggered when a metric exceeds a specified threshold.
- **Relative**: Triggered when a metric deviates from its historical average by a specified percentage
- **Deadman**: Triggered when no data for a given topic is received for a specified period of time.

See more information about creating alert rules in the `Chronograf documentation`_.

