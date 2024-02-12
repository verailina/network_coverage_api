from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel

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


class Network(str, Enum):
    N2G = "2G"
    N3G = "3G"
    N4G = "4G"


class NetworkCoverage(BaseModel):
    operator: str
    coverage: dict[Network, bool]
    latitude: float
    longitude: float
    distance: float
    address: str = None
