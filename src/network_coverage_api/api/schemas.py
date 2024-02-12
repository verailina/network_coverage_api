from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field, field_serializer


@dataclass
class Address:
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
    Orange = 20801
    SFR = 20810
    Free = 20815
    Bouygue = 20820


class NetworkCoverage(BaseModel):
    operator: Operator
    N2G: bool = Field(serialization_alias="2G")
    N3G: bool = Field(serialization_alias="3G")
    N4G: bool = Field(serialization_alias="4G")

    @field_serializer("operator")
    def serialize_group(self, operator: Operator, _info):
        return operator.name


class Location(BaseModel):
    latitude: float
    longitude: float
    address: str | None = None


class NetworkCoverageDetailed(NetworkCoverage):
    distance: float
    closest_location: Location = None
    target_location: Location = None
