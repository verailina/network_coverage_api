from network_coverage_api.network_datasource import ClusterBuilder, SeriesRange
import pandas as pd
from pytest import fixture
import pytest


@fixture
def cluster_builder():
    lat = pd.Series(range(10)) + 10
    lon = pd.Series(range(5)) + 5
    return ClusterBuilder(SeriesRange(lat), SeriesRange(lon))


def test_cluster_builder_init(cluster_builder):
    assert cluster_builder.lat_range.min_val == 10
    assert cluster_builder.lat_range.max_val == 19
    assert cluster_builder.lon_range.min_val == 5
    assert cluster_builder.lon_range.max_val == 9


@pytest.mark.parametrize("point, cluster", [
    ((10.01, 5.01), (0, 0)),
    ((10.5, 5.01), (1, 0)),
    ((10.4, 5.01), (0, 0)),
    ((19.0, 9.00), (18, 8)),
])
def test_cluster_builder_get_point_cluster(point, cluster, cluster_builder):
    assert cluster_builder.get_point_cluster(*point) == cluster


@pytest.mark.parametrize("cluster, cluster_id", [
    ((0, 0), 0),
    ((0, 1), 1),
    ((0, 2), 2),
    ((1, 2), 22),
    ((2, 3), 43),
])
def test_cluster_builder_get_cluster(cluster, cluster_id, cluster_builder):
    assert cluster_builder.get_cluster_id(cluster) == cluster_id
