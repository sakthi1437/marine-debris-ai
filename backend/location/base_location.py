from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float
    source: str


class LocationProvider(ABC):
    source = "unknown"

    @abstractmethod
    def get_location(self) -> Location:
        """Return a location or raise LocationUnavailableError."""


class LocationUnavailableError(RuntimeError):
    pass
