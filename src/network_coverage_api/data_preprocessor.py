import importlib.resources
from network_coverage_api.utils import get_logger, timeit
from network_coverage_api.api.schemas import Operator
from network_coverage_api.api.geocoding import lambert93_to_gps
from network_coverage_api.network_datasource import ClusterBuilder, SeriesRange
import pandas as pd
from network_coverage_api.config import settings

logger = get_logger()


@timeit
def build_preprocessed_data(raw_network_file: str):
    raw_data = load_raw_network_data(raw_network_file)
    raw_data.dropna(inplace=True)
    preprocessed_data = convert_coordinates(raw_data)
    dump_dataframe(preprocessed_data, "network_data_converted.csv")

    for operator in Operator:
        logger.info(f"Building clusters for {operator.name}")
        operator_data = preprocessed_data.loc[operator.value].reset_index(drop=True)
        lat_range = SeriesRange(operator_data["latitude"])
        lon_range = SeriesRange(operator_data["longitude"])
        cluster_builder = ClusterBuilder(lat_range, lon_range, cluster_size=settings.cluster_size)

        operator_data["cluster"] = operator_data.apply(lambda row: cluster_builder.get_cluster_id(
            cluster_builder.get_point_cluster(row.latitude, row.longitude)), axis=1)
        operator_data.set_index("cluster", inplace=True)
        dump_dataframe(operator_data, f"{operator.name}_datasource.csv")

@timeit
def load_raw_network_data(file_name: str) -> pd.DataFrame:
    data_dir = importlib.resources.files("network_coverage_api.data")
    with importlib.resources.as_file(data_dir) as data_dir:
        network_data_path = data_dir.joinpath(file_name)
        network_data = pd.read_csv(str(network_data_path), sep=';', index_col=0)
    return network_data


@timeit
def convert_coordinates(network_data: pd.DataFrame) -> pd.DataFrame:
    logger.info(f"Converting Lambert 93 data to GPS coordinates")
    df = network_data
    df["gps"] = df[["x", "y"]].apply(lambda row: lambert93_to_gps(row.x, row.y), axis=1)
    df.loc[:, "latitude"] = df["gps"].apply(lambda x: x[1]).round(decimals=4)
    df.loc[:, "longitude"] = df["gps"].apply(lambda x: x[0]).round(decimals=4)
    df.drop(axis=1, inplace=True, columns="gps")
    #df.sort_values(["latitude", "longitude"], inplace=True)
    return df


def dump_dataframe(operator_data: pd.DataFrame, data_file_name: str) -> None:
    data_dir = importlib.resources.files("network_coverage_api.data")
    with importlib.resources.as_file(data_dir) as data_dir:
        network_data_path = data_dir.joinpath(data_file_name)
        operator_data.to_csv(str(network_data_path))


if __name__ == "__main__":
    data_source_filename = "2018_01_Sites_mobiles_2G_3G_4G_France_metropolitaine_L93.csv"
    build_preprocessed_data(data_source_filename)