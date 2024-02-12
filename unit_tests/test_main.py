from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from network_coverage_api.api.main import app, NetworkCoverage, Address, Operator
from network_coverage_api.api.geocoding import Location

client = TestClient(app)


@patch('network_coverage_api.api.main.geocode')
@patch('network_coverage_api.api.main.network_datasource_loader')
def test_network_coverage(loader_mock, geocode_mock):
    loader_mock.get_data_source.return_value.find_closest_point.return_value = Mock(spec=NetworkCoverage)
    response = client.get("/network_coverage?city=Paris")
    geocode_mock.assert_called_with(Address(city="Paris"))
    for operator in Operator:
        assert loader_mock.get_data_source.called_with(operator)
    assert loader_mock.get_data_source.return_value.find_closest_point.called_with(
        latitude=geocode_mock.return_value.latitude,
        longitude=geocode_mock.return_value.longitude)
    assert response.status_code == 200
