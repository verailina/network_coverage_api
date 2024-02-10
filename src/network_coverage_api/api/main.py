import uvicorn
from typing import List
from fastapi import FastAPI
from network_coverage_api.utils import get_logger
from network_coverage_api.api.schemas import Address, Operator, NetworkCoverage
from geocoding import geocode
from network_coverage_api.network_datasource import network_datasource_map

logger = get_logger()

app = FastAPI()



@app.get("/network_coverage")
async def network_coverage(street_number: str, street_name: str, city: str, postal_code: str):
    address = Address(street_name=street_name, street_number=street_number, city=city, postal_code=postal_code)
    location = geocode(address)
    result = []
    for operator in Operator:
        coverage = network_datasource_map[operator].find_closest_point(latitude=location.latitude, longitude=location.longitude)
        logger.info(f"Network coverage for {(location.latitude, location.longitude)}: {coverage}")
        result.append(coverage)
    return result


if __name__ == "__main__":
    uvicorn.run(
        "network_coverage_api.api.main:app", host="127.0.0.1", port=8088, log_level="info"
    )