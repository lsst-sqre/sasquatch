.. _influxdb-api:

############
InfluxDB API
############

This guide explains how to query InfluxDB databases directly using the InfluxDB API.

In most cases, the `EFD client`_ is the easiest and recommended way to query data from the EFD and other databases.

If the client isn't available in your environment, or if you prefer a more lightweight method, you can use the InfluxDB API as an alternative.

InfluxDB connection information
-------------------------------

The InfluxDB API uses simple authentication with a username and password.
Token-based authentication is not currently supported.

To query an InfluxDB database using the API, you will need the following connection details:

- InfluxDB API URL
- Database name
- Username and password

If you are inside the RSP notebook aspect, you can find this information using the ``lsst.rsp`` package.
For example, to retrieve InfluxDB connection information for the ``usdf_efd`` database:

.. code:: python

  from lsst.rsp import get_influxdb_credentials

  get_influxdb_credentials("usdf_efd")

If you are outside the RSP, the recommended way to retrieve this information is using the Repertoire client.
See the `Getting InfluxDB connection information`_ guide.

Alternatively, you can also retrieve the InfluxDB connection information directly from the Repertoire API.
For example, to retrieve InfluxDB connection information for the ``usdf_efd`` database, you can send a GET request to the following URL:

``https://<repertoire-url>/discovery/influxdb/usdf_efd``

where ``<repertoire-url>`` is the base URL for Repertoire for your local environment.
For Phalanx applications, the base URL for Repertoire can be obtained from ``global.repertoireUrl``.

Since the returned information includes username and password credentials, this endpoint is protected and requires authentication using an access token.
This may be a user token created through the token UI with ``"read:sasquatch"`` scope.
See the `RSP documentation`_ for more information.

.. code:: python

  import requests

  repertoire_url = "..."  # the base URL for Repertoire, e.g. obtained from global.repertoireUrl in Phalanx

  token = "..."  # obtained from somewhere else
  headers = {"content-type": "application/json", "Authorization": f"Bearer {token}"}

  response = requests.get(
      f"{repertoire_url}/discovery/influxdb/usdf_efd", headers=headers
  )

  response.raise_for_status()  # check for HTTP errors

  info = response.json()  # Parse the JSON response into a Python dictionary


See `Repertoire API documentation`_ for more information about the returned information.


The InfluxDB API query endpoint
-------------------------------

Use the InfluxDB API ``/query`` endpoint to query data using the InfluxQL query language.
See the `InfluxQL documentation`_ for more information on the supported query syntax and capabilities.

The following example shows how to query the InfluxDB API:

.. code:: python

  import requests

  influxdb_url = info.get("url")  # the URL of the InfluxDB API
  database = info.get("database")  # the name of the InfluxDB database to query
  auth = (
      info.get("username"),
      info.get("password"),
  )  # the username and password credentials for authentication

  query = """
    SELECT vacuum
    FROM "lsst.sal.ATCamera.vacuum"
    WHERE time > now() - 1h
    /* source: my-application-name */
  """  # the InfluxQL query to send to the InfluxDB API

  response = requests.get(
      f"{influxdb_url}/query", params={"db": database, "q": query}, auth=auth
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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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


Best practices for querying InfluxDB databases
----------------------------------------------

When querying InfluxDB databases, keep the following best practices in mind:

1. Use the Repertoire client or API to retrieve InfluxDB connection information. This ensures your application can adapt to changes in the environment.

2. Whenever possible, use the InfluxDB databases at USDF even if your application is running at the Summit (for example, ``usdf_efd`` instead of ``summit_efd``). These databases are intended for user queries and help reduce the impact on Summit operations.

3. Avoid querying production InfluxDB databases during development. From a development environment (such as ``usdf-rsp-dev``), use Repertoire to discover connection details for a development database (for example, ``usdfdev_efd``).

4. Write efficient InfluxQL queries. Use appropriate time ranges, filters, and functions to limit the amount of data returned and reduce load on the database. You can use the ``EXPLAIN ANALYZE`` command in InfluxQL to help diagnose query performance.

5. Add comments to your InfluxQL statements to help identify the origin of queries in InfluxDB logs. For example:

.. code:: sql

  SELECT vacuum
  FROM "lsst.sal.ATCamera.vacuum"
  WHERE time > now() - 1h
  /* source: my-application-name */




