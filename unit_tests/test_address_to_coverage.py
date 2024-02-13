import pytest
from network_coverage_api.api.network_coverage_router import _get_network_coverage, Address
from network_coverage_api.utils import get_logger

logger = get_logger()


@pytest.mark.parametrize("address, test_data", [
    (Address(street_name="Pl. du Carrousel",
             postal_code="75001",
             city="Paris"), dict(city="Paris")),
    (Address(city="Strasbourg"), dict(city="Strasbourg")),
    (Address(postal_code="92200"), dict(city="Neuilly-sur-Seine")),
])
def test_get_network_coverage(address, test_data: dict):
    coverage_res = _get_network_coverage(address, detailed=True)
    logger.info(coverage_res)
    for item in coverage_res:
        assert item.distance < 1.
        closest_city = item.closest_location.address.split(" ")[-1] if item.closest_location else None
        if closest_city:
            assert closest_city == test_data.get("city")
