import math
from dataclasses import dataclass, astuple

import pandas as pd
from matplotlib import pyplot as plt
from typing import List, Dict
from network_coverage_api.api.schemas import Operator
from network_coverage_api.utils import timeit, get_logger, get_data_path
import geopy.distance
from network_coverage_api.config import settings


logger = get_logger()


@dataclass
class MapPoint:
    latitude: float
    longitude: float


@dataclass
class Cluster:
    row: int
    column: int


class SeriesRange:
    def __init__(self, series: pd.Series):
        self.min_val = series.min()
        self.max_val = series.max()
        self.range_len = self.max_val - self.min_val + 1


@dataclass
class MapPointData:
    point: MapPoint
    distance: float
    data: Dict | None


class MapSearcher:
    def __init__(self, data: pd.DataFrame, cluster_size: float = 0.5):
        lat_range = SeriesRange(data["latitude"])
        lon_range = SeriesRange(data["longitude"])
        self.lat_range = lat_range
        self.lon_range = lon_range
        self.cluster_size = cluster_size
        self.col_size = math.ceil(self.lon_range.range_len / self.cluster_size)
        self.row_size = math.ceil(self.lat_range.range_len / self.cluster_size)

    def get_cluster_id(self, cluster: Cluster) -> int:
        return cluster.row * self.row_size + cluster.column

    def get_point_cluster(self, point: MapPoint) -> Cluster:
        cluster_row = int((point.latitude - self.lat_range.min_val) // self.cluster_size)
        cluster_col = int((point.longitude - self.lon_range.min_val) // self.cluster_size)
        return Cluster(row=cluster_row, column=cluster_col)

    def get_target_clusters(self, point: MapPoint, cluster: Cluster) -> List[Cluster]:
        clusters = [cluster]
        intersection = 0.01
        # Close to the cluster right border
        if (abs(point.latitude - ((cluster.row + 1.) * self.cluster_size + self.lat_range.min_val)) < intersection
                and cluster.row + 1. < self.row_size):
            clusters.append((cluster.row + 1., cluster.column))
        # Close to the cluster left border
        elif (abs(point.latitude - (cluster.row * self.cluster_size) + self.lat_range.min_val) < intersection
              and cluster.row - 1. > 0):
            clusters.append((cluster.row - 1., cluster.column))

        # Close to the top cluster border
        if (abs(point.longitude - ((cluster.column + 1.) * self.cluster_size) + self.lon_range.min_val) < intersection
                and cluster.column + 1. < self.col_size):
            clusters.append((cluster.row, cluster.column + 1.))
        # Close to the bottom cluster border
        elif (abs(point.longitude - (cluster.column * self.cluster_size) + self.lon_range.min_val) < intersection
              and cluster.column - 1. > 0):
            clusters.append((cluster.row, cluster.column - 1.))
        return clusters

    def visualize_clusters(self) -> None:
        df = self.data.reset_index()
        df.plot.scatter(x="longitude", y="latitude", c="cluster")
        plt.show()

    def get_point_neighbors(self, point: MapPoint) -> List[dict]:
        cluster = self.get_point_cluster(point)
        logger.info(f"Point cluster: {cluster}, id: {self.get_cluster_id(cluster)}")
        neighbors = []
        target_clusters = self.get_target_clusters(point, cluster)
        for cluster in target_clusters:
            cluster_id = self.get_cluster_id(cluster)
            if cluster_id in self.data.index:
                df = self.data.loc[cluster_id]
                logger.info(f"Added {len(df)} points from the cluster {cluster}, cluster_id: {cluster_id}")
                neighbors += df.to_dict(orient="records")
                if len(df) > 0:
                    break
        logger.info(f"Points neighborhood contains: {len(neighbors)} points")
        return neighbors

    @timeit
    def find_closest_point_data(self, point: MapPoint) -> MapPointData:
        best_point, best_distance = None, None
        neighbors = self.get_point_neighbors(point)
        for neighbor in neighbors:
            neighbor_pos = (neighbor["latitude"], neighbor["longitude"])
            distance = geopy.distance.distance(astuple(point), neighbor_pos).km
            logger.debug(f"Distance between: target: {point} and neighbor: {neighbor_pos}: {distance} km")
            if best_point is None or distance < best_distance:
                best_point = neighbor
                best_distance = distance
        return MapPointData(data=best_point, distance=best_distance,
                            point=MapPoint(latitude=best_point.get("latitude"), longitude=best_point.get("longitude")))


class MapSearcherFactory:
    def __init__(self):
        self.map_searchers = dict()

    def get_map_searcher(self, operator: Operator) -> MapSearcher:
        if operator not in self.map_searchers:
            data = self.load_datasource(operator)
            self.map_searchers[operator] = MapSearcher(data, cluster_size=settings.CLUSTER_SIZE)

        return self.map_searchers[operator]

    @staticmethod
    def load_datasource(operator: Operator) -> pd.DataFrame:
        data_path = get_data_path(f"{operator.name}_datasource.csv")
        if data_path.exists():
            df = pd.read_csv(data_path, index_col=0)
            df.index = df.index.astype(int)
        else:
            raise FileNotFoundError(f"Could not find {data_path}")
        return df


if __name__ == "__main__":
    operator = Operator.Bouygue
    data = MapSearcherFactory.load_datasource(operator)
    cluster_builder = MapSearcher(data, cluster_size=settings.CLUSTER_SIZE)
    cluster_builder.visualize_clusters()
