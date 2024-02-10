import pandas as pd
import importlib.resources
from typing import List, Tuple
from network_coverage_api.api.schemas import Operator, NetworkCoverage, Network
import dataclasses
from network_coverage_api.utils import timeit, get_logger
import matplotlib.pyplot as plt
import geopy.distance
from network_coverage_api.api.geocoding import geocode_reverse

logger = get_logger()


@dataclasses.dataclass
class Range:
    min_val: float
    max_val: float

    def length(self) -> float:
        return self.max_val - self.min_val


class NetworkDatasource:
    def __init__(self, operator: Operator, grid_size: float = 0.5, radius: float = 0.01):
        self.operator = operator
        self.data = self.load_datasource(f"{operator.name}_data_gps.csv")

        self.lat_range = Range(self.data["latitude"].min(), self.data["latitude"].max())
        self.lon_range = Range(self.data["longitude"].min(), self.data["longitude"].max())
        self.grid_size = grid_size
        self.radius = radius
        self.compute_clusters()

    def compute_clusters(self):
        self.data.dropna(inplace=True)
        self.data["grid"] = self.data.apply(lambda row: self.get_cluster_id(
            self.get_point_cluster(row.latitude, row.longitude)), axis=1)
        self.data.set_index("grid", inplace=True)

    def get_cluster_id(self, cluster: Tuple[int, int]) -> int:
        n_lat = int((self.lat_range.length() + .5) / self.grid_size)
        return cluster[0] * n_lat + cluster[1]

    @staticmethod
    def load_datasource(file_name: str) -> pd.DataFrame:
        data_dir = importlib.resources.files("network_coverage_api.data")
        with importlib.resources.as_file(data_dir) as data_dir:
            data_path = data_dir.joinpath(file_name)
            df = pd.read_csv(data_path)
        return df

    def get_point_neighbors(self, latitude: float, longitude: float) -> List[dict]:
        (row, col) = self.get_point_cluster(latitude, longitude)
        neighbors = []
        target_clusters = [(row, col), (row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
        max_cluster = self.data.index.max()
        for (row, col) in target_clusters:
            cluster_id = self.get_cluster_id((row, col))
            if row < 0 or col < 0 or cluster_id > max_cluster:
                continue
            df = self.data.loc[cluster_id]
            df = df[abs(latitude - df["latitude"]) < self.radius]
            df = df[abs(longitude - df["longitude"]) < self.radius]
            logger.info(f"Added {len(df)} points from the cluster {(row, col)}, cluster_id: {cluster_id}")
            neighbors += df.to_dict(orient="records")
        logger.info(f"Points neighborhood contains: {len(neighbors)} points")
        return neighbors

    @timeit
    def find_closest_point(self, latitude: float, longitude: float):
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
            best_neighbour.address = geocode_reverse(best_neighbour.latitude, best_neighbour.longitude).address
        return best_neighbour

    def get_point_cluster(self, lat: float, lon: float) -> Tuple[int, int]:
        lat_pos = int((lat - self.lat_range.min_val) / self.grid_size)
        lon_pos = int((lon - self.lon_range.min_val) / self.grid_size)
        return lat_pos, lon_pos


    def visualize_clusters(self) -> None:
        self.data.reset_index().plot.scatter(x="latitude", y="longitude", c="grid")
        plt.show()


network_datasource_map = {
    operator: NetworkDatasource(operator) for operator in Operator
}


if __name__ == "__main__":
    operator = Operator.Orange
    ds = NetworkDatasource(operator)
    ds.find_closest_point(48.882222, 2.274588)
