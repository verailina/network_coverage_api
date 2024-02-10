import pandas as pd
import importlib.resources
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
        self.data.dropna(inplace=True)
        self.data["grid"] = self.data.apply(lambda row: self.get_point_cluster(row.latitude, row.longitude), axis=1)
        self.data.set_index("grid", inplace=True)


    @staticmethod
    def load_datasource(file_name: str) -> pd.DataFrame:
        data_dir = importlib.resources.files("network_coverage_api.data")
        with importlib.resources.as_file(data_dir) as data_dir:
            data_path = data_dir.joinpath(file_name)
            df = pd.read_csv(data_path)
        return df

    def get_point_neighbors(self, latitude: float, longitude: float) -> pd.DataFrame:
        point_cluster = self.get_point_cluster(latitude, longitude)
        df = self.data.loc[point_cluster]
        df = df[abs(latitude - df["latitude"]) < self.radius]
        df = df[abs(longitude - df["longitude"]) < self.radius]
        logger.info(f"Points neighborhood contains: {df.size} points")
        return df

    @timeit
    def find_closest_point(self, latitude: float, longitude: float):
        best_neighbour = None
        neighbors = self.get_point_neighbors(latitude, longitude)
        iter = 0
        for neighbor in neighbors.to_dict(orient="records"):
            logger.info(f"Iteration {iter}")
            iter += 1
            neighbor_pos = (neighbor["latitude"], neighbor["longitude"])
            distance = geopy.distance.distance((latitude, longitude), neighbor_pos).km
            logger.info(f"Distance between: target: {(latitude, longitude)} and neighbor: {neighbor_pos}: {distance} km")
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

    def get_point_cluster(self, lat: float, lon: float) -> int:
        n_lat = int((self.lat_range.length() + .5) / self.grid_size)
        lat_pos = int((lat - self.lat_range.min_val) / self.grid_size)
        lon_pos = int((lon - self.lon_range.min_val) / self.grid_size)
        return lat_pos * n_lat + lon_pos

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
