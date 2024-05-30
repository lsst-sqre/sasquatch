.. _influxdbapi:

################
The InfluxDB API
################

In the :ref:`EFD Client <efdclient>` section, we discussed how to access EFD data using the EFD client from a notebook in the RSP.

For service or application that needs to access EFD data, the recommended method is to query the `InfluxDB API`_.

Currently, Sasquatch uses the InfluxDB v1 API.

For example, to query data from the EFD database at the USDF environment, you need the following information:

- The ``INFLUXDB_URL`` is the URL of the InfluxDB server. For the USDF environment, the URL is ``https://usdf-rsp.slac.stanford.edu/influxdb-enterprise-data``.
- The ``INFLUXDB_DATABASE`` is the name of the database you want to query. For the EFD database, the name is ``efd``.
- The ``INFLUXDB_USER`` and ``INFLUXDB_PASSWORD`` are the credentials for accessing the database and can be obtained from the LSSTIT SQuare Vault in 1Password under "EFD reader at USDF".

.. code::

  INFLUXDB_URL = https://usdf-rsp.slac.stanford.edu/influxdb-enterprise-data
  INFLUXDB_DATABASE = "efd"
  INFLUXDB_USER = ""
  INFLUXDB_PASSWORD = ""

You can use the InfluxDB API ``/query`` endpoint to query data using `InfluxQL`_.
Here is an example on how to query the InfluxDB API using the Python requests module.

.. code:: python

  import os
  import requests


  class InfluxDBClient:
      """A simple InfluxDB client.

      Parameters
      ----------
      url : str
          The URL of the InfluxDB API.
      database_name : str
          The name of the database to query.
      username : str, optional
          The username to authenticate with.
      password : str, optional
          The password to authenticate with.
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


  client = InfluxDBClient(
      url=INFLUXDB_URL,
      database_name=INFLUXDB_DATABASE,
      username=INFLUXDB_USER,
      password=INFLUXDB_PASSWORD,
  )

  response = client.query(
      """SELECT vacuum FROM "lsst.sal.ATCamera.vacuum" WHERE time > now() - 1d"""
  )

The InfluxDB API response format
================================

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

To convert the InfluxDB API response to a Pandas DataFrame, you can use the following code, assuming you are sending a single query
and querying a single topic at a time.
The result is equivalent to the Pandas DataFrame you would get from the EFD client.

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


.. _InfluxDB API: https://docs.influxdata.com/influxdb/v1/tools/api/
.. _InfluxQL: https://docs.influxdata.com/influxdb/v1/query_language/spec/
