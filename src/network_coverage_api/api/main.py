import uvicorn
from typing import List
from fastapi import FastAPI
from network_coverage_api.utils import get_logger
from network_coverage_api.api.schemas import Address, Operator, NetworkCoverage
from network_coverage_api.api.geocoding import geocode
from network_coverage_api.network_datasource import NetworkDatasourceLoader

logger = get_logger()

app = FastAPI()

network_datasource_loader = NetworkDatasourceLoader()


@app.get("/network_coverage", response_model=List[NetworkCoverage])
async def network_coverage(street_number: str | None = None,
                           street_name: str | None = None,
                           city: str | None = None,
                           postal_code: str | None = None):
    address = Address(street_name=street_name, street_number=street_number, city=city, postal_code=postal_code)
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
    return result


if __name__ == "__main__":
    uvicorn.run(
        "network_coverage_api.api.main:app", host="127.0.0.1", port=8088, log_level="info"
    )
