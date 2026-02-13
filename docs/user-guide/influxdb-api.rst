.. _influxdb-api:

############
InfluxDB API
############

This guide describes how to access the InfluxDB API, which can be useful for services or applications that need to query data stored in Sasquatch.

InfluxDB connection information
-------------------------------

From the Rubin Science Platform, list the InfluxDB databases available in your environment with:

.. code::

    from lsst.rsp list_influxdb_labels

    list_influxdb_labels()

This returns a list of database labels that you can use to retrieve connection information using the `Repertoire`_ service discovery.
You can retrieve the connection information with:

.. code:: Python

    from lsst.rsp import get_influxdb_credentials

    get_influxdb_credentials("<database_label>")

To query the InfluxDB v1 API, you need the InfluxDB API URL, the database name, and the username and password credentials to connect to the database.


The InfluxDB API query endpoint
-------------------------------

Use the InfluxDB API ``/query`` endpoint to query data using the InfluxQL query language.
See the `InfluxQL documentation`_ for more information on the supported query syntax and capabilities.

Here is an example on how to query the InfluxDB v1 API using the Python requests module.

.. code:: python

  import os
  import requests


  class InfluxDBClient:
      """A simple InfluxDB client.

      Parameters
      ----------
      url : str
          The InfluxDB API URL
      database_name : str
          The name of the database to query.
      username : str, optional
          The username to connect to the database.
      password : str, optional
          The password to connect to the database.
      """

      def __init__(
          self,
          url: str,
          database_name: str,
          username: str | None = None,
          password: str | None = None,
      ) -> None:
          self.url = url
          self.database_name = database_name
          self.auth = (username, password) if username and password else None

      def query(self, query: str) -> dict:
          """Send a query to the InfluxDB API."""
          params = {"db": self.database_name, "q": query}
          try:
              response = requests.get(f"{self.url}/query", params=params, auth=self.auth)
              response.raise_for_status()
              return response.json()
          except requests.exceptions.RequestException as exc:
              raise InfluxDBError(f"An error occurred: {exc}") from exc


The InfluxDB API response format
--------------------------------

The following example illustrates how to use the InfluxDB client to send a query to the InfluxDB API and the expected response format.

.. code:: python

  # Instantiate the InfluxDB client with the appropriate connection information
  client = InfluxDBClient()

  # Example query to the InfluxDB API
  response = client.query(
      """SELECT vacuum FROM "lsst.sal.ATCamera.vacuum" WHERE time > now() - 1h"""
  )

The above query retrieves the ``vacuum`` measurements for the ``ATCamera`` in the last hour, using the InfluxQL ``now()`` function to specify a time range relative to the server's current time.
The InfluxDB API response is a JSON object with the following structure:

.. code:: json

  {
    "results": [
      {
        "statement_id": 0,
        "series": [
          {
            "columns": ["time", "vacuum"],
            "name": "lsst.sal.ATCamera.vacuum",
            "values": [
              ["2024-05-30T16:49:40.119558Z", 3.08e-7],
              ["2024-05-30T16:49:50.120548Z", 3.17e-7],
              ["2024-05-30T16:50:00.12093Z", 3.52e-7]
            ]
          }
        ]
      }
    ]
  }

The ``/query`` endpoint supports sending multiple queries in a single request by separating them with a semicolon.
If you send a single query like above the result will have a single ``statement_id``.
You can query multiple topics in a single request as well.
If you query a single topic like above the result will have a single ``series``.


Converting the InfluxDB API response to a Pandas DataFrame
----------------------------------------------------------

To convert the InfluxDB v1 API response to a Pandas DataFrame, you can use the following code, assuming you are sending a single query
and querying a single topic at a time like in the example above.

The result is equivalent to the Pandas DataFrame you would get when using the EFD client.

.. code:: python

  import pandas as pd


  def _to_dataframe(self, response: dict) -> pd.DataFrame:
      """Convert an InfluxDB response to a Pandas dataframe.

      Parameters
      ----------
      response : dict
          The JSON response from the InfluxDB API.
      """
      # One query submitted at a time
      statement = response["results"][0]
      # One topic queried at a time
      series = statement["series"][0]
      result = pd.DataFrame(series.get("values", []), columns=series["columns"])
      if "time" not in result.columns:
          return result
      result = result.set_index(pd.to_datetime(result["time"])).drop("time", axis=1)
      if result.index.tzinfo is None:
          result.index = result.index.tz_localize("UTC")
      if "tags" in series:
          for k, v in series["tags"].items():
              result[k] = v
      if "name" in series:
          result.name = series["name"]
      return result
