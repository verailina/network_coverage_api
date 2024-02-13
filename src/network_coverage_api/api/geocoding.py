from pyproj import Transformer
from geopy.geocoders import BANFrance
from geopy import Location, Point
from network_coverage_api.api.schemas import Address
from network_coverage_api.utils import get_logger, timeit
from geopy.exc import GeocoderServiceError

logger = get_logger()


@timeit
def geocode(address: Address, n_tries: int = 5) -> Location | None:
    geocoder = BANFrance()
    for _ in range(n_tries):
        try:
            result = geocoder.geocode(address.full_address, exactly_one=False)
            if result is None or len(result) == 0:
                return None
            else:
                return result[0]
        except GeocoderServiceError as e:
            logger.error(
                f"Failed to geocode address {address.full_address}, error: {e}"
            )


@timeit
def geocode_reverse(
    latitude: float, longitude: float, n_tries: int = 5
) -> Location | None:
    geocoder = BANFrance()
    for _ in range(n_tries):
        try:
            result = geocoder.reverse(Point(latitude, longitude), exactly_one=False)
            if result is None or len(result) == 0:
                return None
            else:
                return result[0]
        except GeocoderServiceError as e:
            logger.error(
                f"Failed to find address for {(latitude, longitude)}, error: {e}"
            )


def lambert93_to_gps(x: float, y: float):
    """
    For ESPG codes see docs: https://spatialreference.org/
    """
    LAMBERT93_CODE = "EPSG:2154"
    WGS84_CODE = "EPSG:4326"
    transformer = Transformer.from_crs(LAMBERT93_CODE, WGS84_CODE, always_xy=True)
    longitude, latitude = transformer.transform(x, y)
    return longitude, latitude
