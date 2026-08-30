from backend.location.base_location import Location, LocationProvider


class ManualLocationProvider(LocationProvider):
    source = "manual"

    def __init__(self, latitude: float, longitude: float):
        self.latitude = latitude
        self.longitude = longitude

    def get_location(self) -> Location:
        return Location(self.latitude, self.longitude, self.source)
