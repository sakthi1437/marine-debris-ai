from backend.location.base_location import Location, LocationProvider, LocationUnavailableError
from backend.location.gps_service import PhoneGPSService, get_default_gps_service


class GPSLocationProvider(LocationProvider):
    source = "phone_gps"

    def __init__(self, gps_service: PhoneGPSService | None = None):
        self.gps_service = gps_service or get_default_gps_service()

    def get_location(self) -> Location:
        return self.gps_service.get_location()
