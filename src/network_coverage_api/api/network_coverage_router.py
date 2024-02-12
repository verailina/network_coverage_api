from fastapi import APIRouter
from typing import List
from network_coverage_api.utils import get_logger
from network_coverage_api.api.schemas import Address, Operator, NetworkCoverage, NetworkCoverageDetailed, Location
from network_coverage_api.api.geocoding import geocode, geocode_reverse
from network_coverage_api.network_datasource import NetworkDatasourceLoader


logger = get_logger()
network_datasource_loader = NetworkDatasourceLoader()
NetworkCoverageRouter = APIRouter()


@NetworkCoverageRouter.get("/", response_model=List[NetworkCoverage])
async def get_network_coverage(
        street_number: str | None = None,
        street_name: str | None = None,
        city: str | None = None,
        postal_code: str | None = None):
    address = Address(street_name=street_name, street_number=street_number, city=city, postal_code=postal_code)
    return _get_network_coverage(address)


@NetworkCoverageRouter.get("/detailed/", response_model=List[NetworkCoverageDetailed])
async def get_detailed_network_coverage(
        street_number: str | None = None,
        street_name: str | None = None,
        city: str | None = None,
        postal_code: str | None = None):
    address = Address(street_name=street_name, street_number=street_number, city=city, postal_code=postal_code)
    return _get_network_coverage(address, detailed=True)


def _get_network_coverage(address: Address, detailed: bool = False) -> List[NetworkCoverage]:
    location = geocode(address)
    result = []
    logger.info(f"Geocoded address: {address}: {location}")
    if location is None:
        logger.info(f"Address not found: {address}")
        return result

    for operator in Operator:
        datasource = network_datasource_loader.get_data_source(operator)
        coverage = datasource.find_closest_point(
            latitude=location.latitude, longitude=location.longitude)
        logger.info(f"Network coverage for {(location.latitude, location.longitude)}: {coverage}")
        if coverage is not None:
            result.append(coverage)

    if detailed:
        for coverage in result:
            coverage.target_location = Location(
                address=location.address,
                latitude=location.latitude,
                longitude=location.longitude
            )
            neighbor_location = geocode_reverse(coverage.closest_location.latitude, coverage.closest_location.longitude)
            coverage.closest_location.address = neighbor_location.address if neighbor_location else None
    return result


