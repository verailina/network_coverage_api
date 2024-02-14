import math
from dataclasses import dataclass, astuple

import pandas as pd
from typing import List, Dict
from network_coverage_api.utils import timeit, get_logger
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


@dataclass
class MapPointData:
    point: MapPoint
    distance: float
    data: Dict | None


@dataclass
class MapConfig:
    left_border: MapPoint
    right_border: MapPoint
    _width: float = None
    _height: float = None

    @property
    def width(self) -> float:
        if self._width is None:
            self._width = self.right_border.longitude - self.left_border.longitude
        return self._width

    @property
    def height(self) -> float:
        if self._height is None:
            self._height = self.right_border.latitude - self.left_border.latitude
        return self._height

    @staticmethod
    def from_series(latitudes: pd.Series, longitudes: pd.Series) -> "MapConfig":
        left_corner = MapPoint(latitudes.min(), longitudes.min())
        right_corner = MapPoint(latitudes.max(), longitudes.max())
        return MapConfig(left_corner, right_corner)


class MapSearcher:
    """Computes the clusters and performs a search into the clustered data."""

    def __init__(self, map_config: MapConfig, cluster_size: float = 0.5):
        self.map_config = map_config
        self.cluster_size = cluster_size
        self.col_num = math.ceil(self.map_config.width / self.cluster_size)
        self.row_num = math.ceil(self.map_config.height / self.cluster_size)

    def get_cluster_id(self, cluster: Cluster) -> int:
        return cluster.row * self.col_num + cluster.column

    def get_point_cluster(self, point: MapPoint) -> Cluster:
        cluster_row = int(
            (point.latitude - self.map_config.left_border.latitude) // self.cluster_size
        )
        cluster_col = int(
            (point.longitude - self.map_config.left_border.longitude)
            // self.cluster_size
        )
        return Cluster(row=cluster_row, column=cluster_col)

    def get_border_distance(
        self,
        point: MapPoint,
        cluster: Cluster,
        axis: str = "latitude",
        border_id: int = 0,
    ) -> float:
        """For a given point computes the distance to its cluster boarders."""
        if axis == "latitude":
            return abs(
                point.latitude
                - (
                    (cluster.row + border_id) * self.cluster_size
                    + self.map_config.left_border.latitude
                )
            )
        if axis == "longitude":
            return abs(
                point.longitude
                - (
                    (cluster.column + border_id) * self.cluster_size
                    + self.map_config.left_border.longitude
                )
            )

    def get_target_clusters(self, point: MapPoint, cluster: Cluster) -> List[Cluster]:
        """Find a cluster for the target point. If point is close to a cluster border consider
        a neighbor clusters.
        """
        clusters = [cluster]
        intersection = 0.01
        # Close to the cluster right border
        if (
            self.get_border_distance(point, cluster, "latitude", 1) < intersection
            and cluster.row + 1.0 < self.row_num
        ):
            clusters.append(Cluster(cluster.row + 1, cluster.column))
        # Close to the cluster left border
        elif (
            self.get_border_distance(point, cluster, "latitude", 0) < intersection
            and cluster.row - 1.0 > 0
        ):
            clusters.append(Cluster(cluster.row - 1, cluster.column))

        # Close to the top cluster border
        if (
            self.get_border_distance(point, cluster, "longitude", 1) < intersection
            and cluster.column + 1.0 < self.col_num
        ):
            clusters.append(Cluster(cluster.row, cluster.column + 1))
        # Close to the bottom cluster border
        elif (
            self.get_border_distance(point, cluster, "longitude", 0) < intersection
            and cluster.column - 1.0 > 0
        ):
            clusters.append(Cluster(cluster.row, cluster.column - 1))
        return clusters

    def get_point_neighbors(self, point: MapPoint, data: pd.DataFrame) -> List[dict]:
        """Get neighbor data points for a target point."""
        cluster = self.get_point_cluster(point)
        logger.info(f"Point cluster: {cluster}, id: {self.get_cluster_id(cluster)}")
        neighbors = []
        target_clusters = self.get_target_clusters(point, cluster)
        for cluster in target_clusters:
            cluster_id = self.get_cluster_id(cluster)
            if cluster_id in data.index:
                df = data.loc[cluster_id]
                logger.info(
                    f"Added {len(df)} points from the cluster {cluster}, cluster_id: {cluster_id}"
                )
                if isinstance(df, pd.Series):
                    neighbors += [df.to_dict()]
                else:
                    neighbors += df.to_dict(orient="records")
        logger.info(f"Points neighborhood contains: {len(neighbors)} points")
        return neighbors

    @timeit
    def find_closest_point_data(
        self, point: MapPoint, data: pd.DataFrame
    ) -> MapPointData:
        """For a given point, find the closest point in the data."""
        best_point, best_distance = None, None
        neighbors = self.get_point_neighbors(point, data)
        for neighbor in neighbors:
            neighbor_pos = (neighbor["latitude"], neighbor["longitude"])
            distance = geopy.distance.distance(astuple(point), neighbor_pos).km
            logger.debug(
                f"Distance between: target: {point} and neighbor: {neighbor_pos}: {distance} km"
            )
            if best_point is None or distance < best_distance:
                best_point = neighbor
                best_distance = distance
        return MapPointData(
            data=best_point,
            distance=best_distance,
            point=MapPoint(
                latitude=best_point.get("latitude"),
                longitude=best_point.get("longitude"),
            ),
        )


def create_map_searcher() -> MapSearcher:
    """Create an instance of a MapSearcher based on settings.toml config."""
    config = MapConfig(
        left_border=MapPoint(
            latitude=settings.left_border_lat, longitude=settings.left_border_lon
        ),
        right_border=MapPoint(
            latitude=settings.right_border_lat, longitude=settings.right_border_lon
        ),
    )
    return MapSearcher(config, cluster_size=settings.cluster_size)
