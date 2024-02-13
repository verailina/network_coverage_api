from typing import Annotated

from fastapi import APIRouter, Query
from typing import List
from network_coverage_api.utils import get_logger
from network_coverage_api.api.schemas import (
    Address,
    Operator,
    NetworkCoverage,
    NetworkCoverageDetailed,
    Location,
)
from network_coverage_api.api.geocoding import geocode, geocode_reverse
from network_coverage_api.map_engine.map_searcher import MapPoint, create_map_searcher
from network_coverage_api.map_engine.map_data import MapData


logger = get_logger()
NetworkCoverageRouter = APIRouter()
map_data = MapData()

POSTAL_CODE_PATTERN = r"^(?:0[1-9]|[1-8]\d|9[0-8])\d{3}$"
STREET_NUMBER_PATTERN = r"^[1-9]+\d*\w*$"


@NetworkCoverageRouter.get("/", response_model=List[NetworkCoverage])
async def get_network_coverage(
    street_number: Annotated[str | None, Query(pattern=STREET_NUMBER_PATTERN)] = None,
    street_name: str | None = None,
    postal_code: Annotated[str | None, Query(pattern=POSTAL_CODE_PATTERN)] = None,
    city: str | None = None,
):
    address = Address(
        street_name=street_name,
        street_number=street_number,
        city=city,
        postal_code=postal_code,
    )
    return _get_network_coverage(address)


@NetworkCoverageRouter.get("/detailed/", response_model=List[NetworkCoverageDetailed])
async def get_detailed_network_coverage(
    street_number: Annotated[str | None, Query(pattern=STREET_NUMBER_PATTERN)] = None,
    street_name: str | None = None,
    postal_code: Annotated[str | None, Query(pattern=POSTAL_CODE_PATTERN)] = None,
    city: str | None = None,
):
    address = Address(
        street_name=street_name,
        street_number=street_number,
        city=city,
        postal_code=postal_code,
    )
    return _get_network_coverage(address, detailed=True)


def _get_network_coverage(
    address: Address, detailed: bool = False
) -> List[NetworkCoverage]:
    location = geocode(address)
    result = []
    logger.info(f"Geocoded address: {address}: {location}")
    if location is None:
        logger.info(f"Address not found: {address}")
        return result

    target_point = MapPoint(latitude=location.latitude, longitude=location.longitude)
    searcher = create_map_searcher()

    for operator in Operator:
        data = map_data.get_operator_data(operator)
        closest_data = searcher.find_closest_point_data(target_point, data)
        logger.info(f"Network coverage for {target_point}: {closest_data}")
        if closest_data is None:
            logger.info(f"No {operator.name} data found for {address}")
            continue
        network_coverage = dict(
            operator=operator,
            N2G=closest_data.data.get("2G"),
            N3G=closest_data.data.get("3G"),
            N4G=closest_data.data.get("4G"),
        )
        if not detailed:
            result.append(NetworkCoverage(**network_coverage))
        else:
            network_coverage["distance"] = closest_data.distance
            network_coverage["target_location"] = Location(
                address=location.address,
                latitude=location.latitude,
                longitude=location.longitude,
            )
            latitude, longitude = (
                closest_data.point.latitude,
                closest_data.point.longitude,
            )
            neighbor_location = geocode_reverse(latitude, longitude)
            network_coverage["closest_location"] = Location(
                address=neighbor_location.address if neighbor_location else None,
                latitude=latitude,
                longitude=longitude,
            )
            result.append(NetworkCoverageDetailed(**network_coverage))
    return result
