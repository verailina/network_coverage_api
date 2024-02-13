from unittest.mock import patch, Mock, call

from fastapi.testclient import TestClient
import pytest

from network_coverage_api.api.main import app
from network_coverage_api.api.network_coverage_router import _get_network_coverage
from network_coverage_api.api.schemas import (
    Operator,
    NetworkCoverage,
    NetworkCoverageDetailed,
    Location,
    Address,
)

client = TestClient(app)


@pytest.mark.parametrize(
    "coverage, response_json",
    [
        (
            [NetworkCoverage(operator=Operator.SFR, N2G=True, N3G=False, N4G=True)],
            [{"operator": "SFR", "2G": True, "3G": False, "4G": True}],
        ),
        ([], []),
    ],
)
@patch("network_coverage_api.api.network_coverage_router._get_network_coverage")
def test_get_network_coverage(get_coverage_mock, coverage, response_json):
    get_coverage_mock.return_value = coverage
    response = client.get("/network_coverage?city=Paris")
    get_coverage_mock.assert_called_with(Address(city="Paris"))
    assert response.status_code == 200
    assert response.json() == response_json


@pytest.mark.parametrize(
    "coverage, response_json",
    [
        (
            [
                NetworkCoverageDetailed(
                    operator=Operator.SFR,
                    N2G=True,
                    N3G=False,
                    N4G=True,
                    distance="0.5",
                    target_location=Location(latitude=1, longitude=1, address="Paris"),
                    closest_location=Location(latitude=1, longitude=1, address="Paris"),
                )
            ],
            [
                {
                    "operator": "SFR",
                    "2G": True,
                    "3G": False,
                    "4G": True,
                    "distance": 0.5,
                    "target_location": {
                        "latitude": 1,
                        "longitude": 1,
                        "address": "Paris",
                    },
                    "closest_location": {
                        "latitude": 1,
                        "longitude": 1,
                        "address": "Paris",
                    },
                }
            ],
        ),
        ([], []),
    ],
)
@patch("network_coverage_api.api.network_coverage_router._get_network_coverage")
def test_get_network_coverage_detailed(get_coverage_mock, coverage, response_json):
    get_coverage_mock.return_value = coverage
    response = client.get("/network_coverage/detailed?city=Paris")
    get_coverage_mock.assert_called_with(Address(city="Paris"), detailed=True)
    assert response.status_code == 200
    assert response.json() == response_json


@pytest.mark.parametrize(
    "geocoded_value, closest_data, detailed",
    [
        (None, None, False),
        (Mock(), None, False),
        (Mock(), Mock(), False),
        (Mock(), Mock(), True),
    ],
)
@patch("network_coverage_api.api.network_coverage_router.map_data")
@patch("network_coverage_api.api.network_coverage_router.create_map_searcher")
@patch("network_coverage_api.api.network_coverage_router.geocode")
@patch("network_coverage_api.api.network_coverage_router.geocode_reverse")
@patch("network_coverage_api.api.network_coverage_router.Operator", new=[Operator.Free])
@patch("network_coverage_api.api.network_coverage_router.MapPoint")
@patch("network_coverage_api.api.network_coverage_router.NetworkCoverage")
@patch("network_coverage_api.api.network_coverage_router.NetworkCoverageDetailed")
@patch("network_coverage_api.api.network_coverage_router.Location")
def test__get_network_coverage(
    location_mock,
    detailed_nc_mock,
    nc_mock,
    point_mock,
    geocode_reverse_mock,
    geocode_mock,
    searcher_mock,
    data_mock,
    geocoded_value,
    closest_data,
    detailed,
):
    address = Mock(spec=Address)
    geocode_mock.return_value = geocoded_value
    searcher = searcher_mock.return_value
    result = searcher.find_closest_point_data.return_value = closest_data

    result = _get_network_coverage(address, detailed=detailed)
    if geocoded_value is None:
        assert result == []
    else:
        searcher_mock.assert_called_once()
        data_mock.get_operator_data.assert_called_with(Operator.Free)
        data = data_mock.get_operator_data.return_value
        searcher.find_closest_point_data.assert_called_with(
            point_mock.return_value, data
        )

        if closest_data is None:
            assert result == []
        elif not detailed:
            assert result == [nc_mock.return_value]
        else:
            geocode_reverse_mock.assert_called_once_with(
                closest_data.point.latitude, closest_data.point.longitude
            )
            location = geocode_mock.return_value
            location_mock.assert_has_calls(
                [
                    call(
                        address=location.address,
                        latitude=location.latitude,
                        longitude=location.longitude,
                    ),
                    call(
                        address=geocode_reverse_mock.return_value.address,
                        latitude=closest_data.point.latitude,
                        longitude=closest_data.point.longitude,
                    ),
                ]
            )
            assert result == [detailed_nc_mock.return_value]
