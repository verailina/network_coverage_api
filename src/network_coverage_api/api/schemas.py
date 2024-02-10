from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel

@dataclass
class Address:
    street_name: str
    street_number: str
    city: str
    postal_code: str

    @property
    def full_address(self) -> str:
        return f"{self.street_number} {self.street_name} {self.city} {self.postal_code}"


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
