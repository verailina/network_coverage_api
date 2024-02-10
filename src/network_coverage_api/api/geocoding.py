
from pyproj import Transformer
from geopy.geocoders import BANFrance
from geopy import Location, Point
import pandas as pd
import importlib.resources
from network_coverage_api.api.schemas import Operator, Address
from network_coverage_api.utils import get_logger, timeit
import numpy as np

logger = get_logger()


def geocode(address: Address, n_tries: int = 5) -> Location:
    geocoder = BANFrance()
    for _ in range(n_tries):
        try:
            result = geocoder.geocode(address.full_address, exactly_one=False)
            if len(result) == 0:
                return None
            else:
                return result[0]
        except Exception as e:
            logger.error(f"Failed to geocode address {address.full_address}, error: {e}")


def geocode_reverse(latitude: float, longitude: float, n_tries: int = 5) -> Location:
    geocoder = BANFrance()
    for _ in range(n_tries):
        try:
            result = geocoder.reverse(Point(latitude, longitude), exactly_one=False)
            if len(result) == 0:
                return None
            else:
                return result[0]
        except Exception as e:
            logger.error(f"Failed to find address for {(latitude, longitude)}, error: {e}")


def lambert93_to_gps(x: float, y: float):
    """
    For ESPG codes see docs: https://spatialreference.org/
    """
    LAMBERT93_CODE = "EPSG:2154"
    WGS84_CODE = "EPSG:4326"
    transformer = Transformer.from_crs(LAMBERT93_CODE, WGS84_CODE, always_xy=True)
    longitude, latitude = transformer.transform(x, y)
    return longitude, latitude


def load_network_data() -> pd.DataFrame:
    data_dir = importlib.resources.files("network_coverage_api.data")
    with importlib.resources.as_file(data_dir) as data_dir:
        network_data_path = data_dir.joinpath("2018_01_Sites_mobiles_2G_3G_4G_France_metropolitaine_L93.csv")
        network_data = pd.read_csv(str(network_data_path), sep=';', index_col=0)
    return network_data


@timeit
def preprocess_network_data(network_data: pd.DataFrame, operator=Operator) -> pd.DataFrame:
    logger.info(f"Converting Lambert 93 data to GPS coordinates for {operator.name}")
    df = network_data.loc[operator.value].reset_index(drop=True)
    df["gps"] = df[["x", "y"]].apply(lambda row: lambert93_to_gps(row.x, row.y), axis=1)
    df.loc[:, "latitude"] = df["gps"].apply(lambda x: x[1]).round(decimals=4)
    df.loc[:, "longitude"] = df["gps"].apply(lambda x: x[0]).round(decimals=4)
    df.drop(axis=1, inplace=True, columns="gps")
    df.sort_values(["latitude", "longitude"], inplace=True)

    data_dir = importlib.resources.files("network_coverage_api.data")
    with importlib.resources.as_file(data_dir) as data_dir:
        network_data_path = data_dir.joinpath(f"{operator.name}_data_gps.csv")
        df.to_csv(str(network_data_path))
    return network_data


def get_cluster(network_data: pd.DataFrame, lat_step: float, lon_step: float):
    min_lat, max_lat = int(network_data.latitude.min()), int(network_data.latitude.max())
    min_lon, max_lon = int(network_data.longitude.min()), int(network_data.longitude.max())





if __name__ == '__main__':
    # geocode()
    # x = 102980
    # y = 6847973
    # location = lambert93_to_gps(x, y)
    # print(location)
    address = '24 Rue des Diables Bleus 73000 Chambéry'
    location = geocode(address)
    network_data = load_network_data()
    for operator in Operator:
        preprocess_network_data(network_data, operator)


    # print(f"Longitude: {network_data['longitude'].min()}, {network_data['longitude'].max()}")
    # print(f"Latitude: {network_data['latitude'].min()}, {network_data['latitude'].max()}")


