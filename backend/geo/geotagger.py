from backend.schemas.metadata import Metadata


def geotag(metadata: Metadata) -> tuple[float, float, str]:
    source = metadata.source if metadata.source in {"manual", "live_gps", "metadata", "simulated"} else "simulated"
    return metadata.latitude, metadata.longitude, source
