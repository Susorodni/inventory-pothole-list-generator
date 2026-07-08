import requests
import json

url = ("https://gis.indy.gov/server/rest/services"
        "/MapIndy/MapIndyProperty/MapServer/10/query")

params = {
    "where": "1=1",
    "outFields": "*",
    "returnGeometry": "false",
    "resultRecordCount": 1,
    "f": "json"
}

data = requests.get(url, params=params).json()

print(json.dumps(list(data["features"][0]["attributes"].keys()), indent=2))
