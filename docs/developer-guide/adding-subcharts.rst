.. _adding-subcharts:


Adding a Sasquatch subchart
===========================

Sasquatch subcharts are applications or application resources deployed in the same namespace as Sasquatch.
Chronograf, Kafdrop and Strimzi Kafka resources are examples of Sasquatch subcharts.

Subcharts can be either **external charts** or **local charts**, and they are added as dependencies of the Sasquatch parent chart in the ``Charts.yaml`` file.

External Charts vs. Local Subcharts
-----------------------------------

Ideally, a Sasquatch subchart should deploy a ready-to-use external Helm chart.
However, there are exceptions when local charts are necessary:

- **Customized Charts**: For instance, the InfluxDB Enterprise Helm chart required significant customization and could not be deployed as a standard external chart in Sasquatch.
- **Unavailable Charts**: Certain Helm charts, like the one for ``kafdrop``, may not be available in a public repository and must be added locally.

Adding External Charts
----------------------

External charts are sourced from repositories and referenced using their repository URL.
For example, the following snippet adds the Chronograf external chart as a dependency in the ``Charts.yaml`` file:

.. code-block:: yaml

   dependencies:
     - name: chronograf
       condition: chronograf.enabled
       version: 1.2.6
       repository: https://helm.influxdata.com/

The ``condition`` key controls whether the subchart is deployed in a particular environment, allowing you to enable or disable specific charts as needed.

Adding Local Subcharts
-----------------------

Local charts are placed under the ``sasquatch/charts`` directory.
For example, the following snippet adds the ``kafdrop`` local chart as a dependency:

.. code-block:: yaml

   dependencies:
     - name: kafdrop
       condition: kafdrop.enabled
       version: 1.0.0

Using Subcharts for Application Resources
-----------------------------------------

Local subcharts can be used to provide application resources.
For example, you can define a custom ingress resource for an application by creating a local subchart with the necessary Kubernetes manifests.
This allows you to manage application-specific configurations within the Sasquatch chart structure while maintaining modularity.
Another example are Phalanx applications that depend on Sasquatch (such as the ``control-system`` or ``tap``) they use local subcharts to define Kafka topics and user resources required for those applications.

