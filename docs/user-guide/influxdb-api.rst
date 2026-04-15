.. _influxdb-api:

############
InfluxDB API
############

This guide describes how to access the InfluxDB API, which can be useful for services or applications that need to query InfluxDB directly without using the `EFD client`_.

InfluxDB connection information
-------------------------------

The InfluxDB API uses simple authentication based on username and password credentials, currently there is no support for token-based authentication.

To query the InfluxDB API, you need the InfluxDB API URL, the database name, and the username and password credentials.
The recommended way to retrieve this information from the RSP is using the `Repertoire client`_.

Alternatively, you can retrieve the InfluxDB connection information directly from the Repertoire API endpoint  ``/repertoire/discovery/influxdb``.
For example, to retrieve InfluxDB connection information for the ``usdf_efd`` database at USDF you can send a GET request to the following URL:

``https://usdf-rsp.slac.stanford.edu/repertoire/discovery/influxdb/usdf_efd``

Since the returned information includes username and password credentials, this endpoint is protected and requires authentication using an access token.
This may be a user token created through the token UI with ``"read:sasquatch"`` scope.
See the `RSP documentation`_ for more information.

.. code:: python

  import requests

  repertoire_url = (
      "https://usdf-rsp.slac.stanford.edu/repertoire/discovery/influxdb/usdf_efd"
  )
  token = "..."  # obtained from somewhere else

  headers = {"content-type": "application/json", "Authorization": f"Bearer {token}"}

  info = requests.get(f"{repertoire_url}", headers=headers)

See `Repertoire API documentation`_ for more information about the returned information.


The InfluxDB API query endpoint
-------------------------------

Use the InfluxDB API ``/query`` endpoint to query data using the InfluxQL query language.
See the `InfluxQL documentation`_ for more information on the supported query syntax and capabilities.

The following example shows how to query the InfluxDB API:

.. code:: python

  import requests

  influxdb_url = "https://usdf-rsp.slac.stanford.edu/influxdb-enterprise-data/"  # the URL of the InfluxDB API
  database_name = "efd"  # the name of the database to query
  auth = (
      "username",
      "password",
  )  # the username and password credentials for authentication

  query = """SELECT vacuum FROM "lsst.sal.ATCamera.vacuum" WHERE time > now() - 1h"""  # the InfluxQL query to send to the InfluxDB API

  response = requests.get(
      f"{influxdb_url}/query", params={"db": database_name, "q": query}, auth=auth
  )


The InfluxDB API response format
--------------------------------

The above query retrieves the ``vacuum`` measurements for the ``ATCamera`` in the last hour.
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
and querying a single topic at a time like in the example above.

The result is equivalent to the Pandas DataFrame you would get when using the `EFD client`_.

.. code:: python

  import pandas as pd


  def to_dataframe(response: dict) -> pd.DataFrame:
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


  to_dataframe(response.json())
