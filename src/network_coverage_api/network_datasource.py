import pandas as pd
from typing import List, Tuple
from network_coverage_api.api.schemas import Operator, NetworkCoverage, Network
from network_coverage_api.utils import timeit, get_logger, get_data_path
import matplotlib.pyplot as plt
import geopy.distance
from network_coverage_api.api.geocoding import geocode_reverse
from network_coverage_api.config import settings

logger = get_logger()


class SeriesRange:
    def __init__(self, series: pd.Series):
        self.min_val = series.min()
        self.max_val = series.max()
        self.range_len = self.max_val - self.min_val + 1


class ClusterBuilder:
    def __init__(self, lat_range: SeriesRange, lon_range: SeriesRange, cluster_size: float = 0.5):
        self.lat_range = lat_range
        self.lon_range = lon_range
        self.cluster_size = cluster_size
        self.row_size = int(self.lon_range.range_len / self.cluster_size)

    def get_cluster_id(self, cluster: Tuple[int, int]) -> int:
        return cluster[0] * self.row_size + cluster[1]

    def get_point_cluster(self, lat: float, lon: float) -> Tuple[int, int]:
        cluster_row = int((lat - self.lat_range.min_val) // self.cluster_size)
        cluster_col = int((lon - self.lon_range.min_val) // self.cluster_size)
        return cluster_row, cluster_col


class NetworkDatasource:
    def __init__(self, operator: Operator, cluster_size: float = 0.5, radius: float = 0.01):
        self.operator = operator
        self.data = self.load_datasource(operator)

        lat_range = SeriesRange(self.data["latitude"])
        lon_range = SeriesRange(self.data["longitude"])
        self.cluster_builder = ClusterBuilder(lat_range, lon_range, cluster_size)
        self.radius = radius

    @staticmethod
    def load_datasource(operator: Operator) -> pd.DataFrame:
        data_path = get_data_path(f"{operator.name}_datasource.csv")
        if data_path.exists():
            df = pd.read_csv(data_path, index_col=0)
            df.index = df.index.astype(int)
        else:
            raise FileNotFoundError(f"Could not find {data_path}")
        return df

    def get_point_neighbors(self, latitude: float, longitude: float) -> List[dict]:
        (row, col) = self.cluster_builder.get_point_cluster(latitude, longitude)
        logger.info(f"Point cluster: {row, col}, id: {self.cluster_builder.get_cluster_id((row, col))}")
        neighbors = []
        target_clusters = [(row, col), (row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
        max_cluster = self.data.index.max()
        for (row, col) in target_clusters:
            radius = self.radius
            while radius < self.cluster_builder.cluster_size:
                cluster_id = self.cluster_builder.get_cluster_id((row, col))
                if row < 0 or col < 0 or cluster_id > max_cluster:
                    continue
                df = self.data.loc[cluster_id]
                df = df[abs(latitude - df["latitude"]) < radius]
                df = df[abs(longitude - df["longitude"]) < radius]
                logger.info(f"Added {len(df)} points from the cluster {(row, col)}, cluster_id: {cluster_id}")
                neighbors += df.to_dict(orient="records")
                if len(df) > 0:
                    break
                radius *= 2
        logger.info(f"Points neighborhood contains: {len(neighbors)} points")
        return neighbors

    @timeit
    def find_closest_point(self, latitude: float, longitude: float) -> NetworkCoverage | None:
        best_neighbour = None
        neighbors = self.get_point_neighbors(latitude, longitude)
        for neighbor in neighbors:
            neighbor_pos = (neighbor["latitude"], neighbor["longitude"])
            distance = geopy.distance.distance((latitude, longitude), neighbor_pos).km
            logger.debug(f"Distance between: target: {(latitude, longitude)} and neighbor: {neighbor_pos}: {distance} km")
            if best_neighbour is None or distance < best_neighbour.distance:
                best_neighbour = NetworkCoverage(
                    operator=self.operator.name,
                    distance=distance,
                    latitude=neighbor_pos[0],
                    longitude=neighbor_pos[1],
                    coverage={
                        network: neighbor.get(network.value) for network in Network
                    }
                )

        if best_neighbour is not None:
            neighbor_location = geocode_reverse(best_neighbour.latitude, best_neighbour.longitude)
            best_neighbour.address = neighbor_location.address if neighbor_location else None
        return best_neighbour

    def visualize_clusters(self) -> None:
        df = self.data.reset_index()
        df = df.where(df["cluster"] > 320)
        df = df.where(df["cluster"] < 500)
        df.plot.scatter(x="longitude", y="latitude", c="cluster")
        #plt.xlim(2, 4)
        plt.show()


class NetworkDatasourceLoader:
    def __init__(self):
        self.data_sources = dict()

    def get_data_source(self, operator: Operator) -> NetworkDatasource:
        if operator not in self.data_sources:
            self.data_sources[operator] = NetworkDatasource(operator=operator)

        return self.data_sources[operator]


if __name__ == "__main__":
    network_datasource = NetworkDatasource(Operator.Bouygue, cluster_size=settings.CLUSTER_SIZE)
    network_datasource.visualize_clusters()
