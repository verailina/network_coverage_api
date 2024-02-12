from network_coverage_api.utils import get_logger, timeit, get_data_path
from network_coverage_api.api.schemas import Operator
from network_coverage_api.api.geocoding import lambert93_to_gps
from network_coverage_api.network_datasource import ClusterBuilder, SeriesRange
import pandas as pd
from network_coverage_api.config import settings

logger = get_logger()


@timeit
def build_preprocessed_data(raw_network_file: str):
    preprocessed_data_file = get_data_path("network_data_converted.csv")
    if preprocessed_data_file.exists():
        preprocessed_data = pd.read_csv(preprocessed_data_file, index_col=0)
    else:
        network_data_path = get_data_path(raw_network_file)
        raw_data = pd.read_csv(str(network_data_path), sep=';', index_col=0)
        raw_data.dropna(inplace=True)
        preprocessed_data = convert_coordinates(raw_data)
        preprocessed_data.to_csv(str(preprocessed_data_file))

    for operator in Operator:
        logger.info(f"Building clusters for {operator.name}")
        operator_data = preprocessed_data.loc[operator.value]
        cluster_builder = ClusterBuilder(operator_data, cluster_size=settings.CLUSTER_SIZE)
        operator_data_path = get_data_path(f"{operator.name}_datasource.csv")
        cluster_builder.data.to_csv(str(operator_data_path))


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


if __name__ == "__main__":
    data_source_filename = "2018_01_Sites_mobiles_2G_3G_4G_France_metropolitaine_L93.csv"
    build_preprocessed_data(data_source_filename)