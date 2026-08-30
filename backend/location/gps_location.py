from backend.location.base_location import LocationProvider, LocationUnavailableError


class GPSLocationProvider(LocationProvider):
    source = "live_gps"

    def get_location(self):
        # GPS hardware adapters can implement this contract without changing the UI.
        raise LocationUnavailableError("Live GPS is unavailable in this desktop environment")
