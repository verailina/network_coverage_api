# France Network coverage API
The API to retrieve 2G/3G/4G coverage for Free, SFR, Orange and Bouygue operators for any address in France. 
It uses the official French address database from `adresse.data.gouv.fr` to get GPS coordinates via 
the `geopy.geocoders.BANFrance` module. 
Then, it queries network coverage data from the [file](https://github.com/verailina/network_coverage_api/blob/main/src/network_coverage_api/data/2018_01_Sites_mobiles_2G_3G_4G_France_metropolitaine_L93.csv) 
to get the 2G/3G/4G network coverage information for the specified location.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Endpoints](#endpoints)
- [Examples](#examples)
- [Algorithm](#algorithm)

## Installation
To install the France Network Coverage API, follow these steps:

```bash
# Clone the repository
git clone https://github.com/verailina/network_coverage_api.git
cd network_coverage_api

# Install dependencies
pip install -r requirements.txt

# Install the `network_coverage_api` package
pip install .
```

## Usage

To launch the API server locally run the `main.py` script:
```bash
python network_coverage_api/src/network_coverage_api/api/main.py
```
Open http://127.0.0.1:8088/docs in your browser to access the Swagger UI, allowing you to call the API endpoints.

## Endpoints
 - `GET /network_coverage`: Retrieves 2G/3G/4G coverage data by Free, SFR, Orange, and Bouygues operators for a specified location.
 - `GET /network_coverage/detailed`: Extends the functionality of the previous endpoint by providing detailed location information along with the coverage data. This includes the address details, the location of the closest data point stored in the data source file, and the distance to this point.

## Examples
- `network_coverage` example:
```bash
curl -X 'GET' \
  'http://127.0.0.1:8088/network_coverage/?street_number=11&street_name=Rue%20des%20Archives&postal_code=75004&city=Paris' \
  -H 'accept: application/json'
```
Response body:
```json
    [
      {
        "operator": "Orange",
        "2G": true,
        "3G": true,
        "4G": false
      },
      {
        "operator": "SFR",
        "2G": false,
        "3G": true,
        "4G": false
      },
      {
        "operator": "Free",
        "2G": false,
        "3G": true,
        "4G": true
      },
      {
        "operator": "Bouygue",
        "2G": true,
        "3G": false,
        "4G": false
      }
    ]
```
 - `network_coverage/detailed` example:
```bash
curl -X 'GET' \
  'http://127.0.0.1:8088/network_coverage/detailed/?street_number=11&street_name=Rue%20des%20Archives&postal_code=75004&city=Paris' \
  -H 'accept: application/json'
```
Response:
```json
[
  {
    "operator": "Orange",
    "2G": true,
    "3G": true,
    "4G": false,
    "distance": 0.05196468284544001,
    "closest_location": {
      "latitude": 48.8575,
      "longitude": 2.354,
      "address": "1 Place Harvey Milk 75004 Paris"
    },
    "target_location": {
      "latitude": 48.857853,
      "longitude": 2.354464,
      "address": "11 Rue des Archives 75004 Paris"
    }
  },
  {
    "operator": "SFR",
    "2G": false,
    "3G": true,
    "4G": false,
    "distance": 0.14889523817348643,
    "closest_location": {
      "latitude": 48.857,
      "longitude": 2.3529,
      "address": "29 Rue de Rivoli 75004 Paris"
    },
    "target_location": {
      "latitude": 48.857853,
      "longitude": 2.354464,
      "address": "11 Rue des Archives 75004 Paris"
    }
  },
  {
    "operator": "Free",
    "2G": false,
    "3G": true,
    "4G": true,
    "distance": 0.11309971452254321,
    "closest_location": {
      "latitude": 48.8571,
      "longitude": 2.3555,
      "address": "4 Rue de la Verrerie 75004 Paris"
    },
    "target_location": {
      "latitude": 48.857853,
      "longitude": 2.354464,
      "address": "11 Rue des Archives 75004 Paris"
    }
  },
  {
    "operator": "Bouygue",
    "2G": true,
    "3G": false,
    "4G": false,
    "distance": 0.06367355074813373,
    "closest_location": {
      "latitude": 48.8578,
      "longitude": 2.3536,
      "address": "38 Rue de la Verrerie 75004 Paris"
    },
    "target_location": {
      "latitude": 48.857853,
      "longitude": 2.354464,
      "address": "11 Rue des Archives 75004 Paris"
    }
  }
]
```

## Algorithm
"The network coverage calculation process works as follows:

1. Obtain GPS coordinates for the input address using geopy.geocoders.BANFrance.
2. Identify the point closest to the target coordinates in the data source file and return the coverage information 
for this point.
3. For the detailed endpoint, utilize `geopy.geocoders.BANFrance` to obtain the address corresponding to the closest 
point.

### Clusterization

To streamline the search through the network coverage data, we implement clustering by applying a grid with a step 
size of 0.5 along both latitude and longitude coordinates. Each data point is assigned a cluster ID using 
the `network_coverage_api.map_engine.map_searcher` module, and the clustered data is stored in 
`network_coverage_api/data/<Operator>_datasource.csv`.

When searching for a target location, we first compute the cluster for the target (latitude, longitude) point and 
then find the closest point to the target within this cluster using the `MapSearcher` class. If the target point is 
close to the cluster border, we also consider the neighboring cluster in the search process.

Clusters can be computed by running `network_coverage_api.map_engine.data_preprocessor`:
```python
from network_coverage_api.map_engine.data_preprocessor import get_preprocessed_data, build_clustered_data
data_source_filename = (
    "2018_01_Sites_mobiles_2G_3G_4G_France_metropolitaine_L93.csv"
)
preprocessed_data = get_preprocessed_data(data_source_filename)
build_clustered_data(preprocessed_data)
```
The `cluster_size` parameter should be set in `network_coverage_api.settings.toml`.
Computed clusters can be visualized by running the script in  `network_coverage_api.map_engine.map_data`:
```python
from network_coverage_api.map_engine.map_data import MapData, Operator

map_data = MapData()
map_data.visualize_clusters(Operator.Free)
```
For a more visual representation, let's see the clusters for `cluster_size=2.0`:

![clusters_for_2.0]([file](https://github.com/verailina/network_coverage_api/blob/main/src/network_coverage_api/data/images/cluster_size_2.png).

For the recommended default `cluster_size=0.5`, the cluster will look like this:

![clusters_for_0_5]([file](https://github.com/verailina/network_coverage_api/blob/main/src/network_coverage_api/data/images/cluster_size_0_5.png).
