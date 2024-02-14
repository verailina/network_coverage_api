from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field, field_serializer


@dataclass
class Address:
    """Address data."""

    street_number: str | None = None
    street_name: str | None = None
    city: str | None = None
    postal_code: str | None = None

    @property
    def full_address(self) -> str:
        address = [self.street_number, self.street_name, self.city, self.postal_code]
        address = filter(lambda a: a is not None, address)
        return " ".join(address)


class Operator(Enum):
    """Network operator and its code."""

    Orange = 20801
    SFR = 20810
    Free = 20815
    Bouygue = 20820


class NetworkCoverage(BaseModel):
    """Base network coverage data."""

    operator: Operator
    N2G: bool = Field(serialization_alias="2G")
    N3G: bool = Field(serialization_alias="3G")
    N4G: bool = Field(serialization_alias="4G")

    @field_serializer("operator")
    def serialize_group(self, operator: Operator, _info):
        return operator.name


class Location(BaseModel):
    """Location data"""

    latitude: float
    longitude: float
    address: str | None = None


class NetworkCoverageDetailed(NetworkCoverage):
    """Detailed network coverage data.

    This class represents detailed network coverage data, providing additional information
    such as distance to the nearest location and detailed target and closest locations.

    Attributes:
        distance (float): The distance to the network coverage.
        closest_location (Location, optional): The location details for closest point found in the datasource.
        target_location (Location, optional): The location details for the target point.
    """

    distance: float
    closest_location: Location = None
    target_location: Location = None
