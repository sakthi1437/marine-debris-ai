import json
import socket
import threading
import time
import pytest

from backend.location.base_location import LocationUnavailableError
from backend.location.gps_location import GPSLocationProvider
from backend.location.gps_service import PhoneGPSService, GPSState
from backend.geo.geotagger import geotag
from backend.schemas.metadata import Metadata


class MockGPSBridge:
    """Helper mock TCP server to simulate Android MarineGPSBridge."""

    def __init__(self, host="127.0.0.1", port=0):
        self.host = host
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind((host, port))
        self.port = self.server_sock.getsockname()[1]
        self.server_sock.listen(1)
        self.server_sock.settimeout(2.0)
        self.client_sock: socket.socket | None = None
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()

    def _accept_loop(self):
        while not self._stop_event.is_set():
            try:
                client, _ = self.server_sock.accept()
                self.client_sock = client
            except socket.timeout:
                continue
            except OSError:
                break

    def send_gps(self, lat: float, lon: float, accuracy: float = 1.3, timestamp: int = 1788110597000):
        payload = {
            "latitude": lat,
            "longitude": lon,
            "accuracy": accuracy,
            "timestamp": timestamp,
        }
        data = (json.dumps(payload) + "\n").encode("utf-8")
        if self.client_sock:
            self.client_sock.sendall(data)

    def send_raw(self, raw_str: str):
        if self.client_sock:
            self.client_sock.sendall(raw_str.encode("utf-8"))

    def disconnect_client(self):
        if self.client_sock:
            try:
                self.client_sock.shutdown(socket.SHUT_RDWR)
                self.client_sock.close()
            except OSError:
                pass
            self.client_sock = None

    def close(self):
        self._stop_event.set()
        self.disconnect_client()
        try:
            self.server_sock.close()
        except OSError:
            pass
        self._thread.join(timeout=1.0)


def test_gps_service_connect_and_receive():
    bridge = MockGPSBridge()
    try:
        service = PhoneGPSService(
            host=bridge.host,
            port=bridge.port,
            stale_timeout=2.0,
            reconnect_interval=0.2,
        )
        service.start()

        # Wait for connection
        time.sleep(0.3)
        state = service.get_state()
        assert state.connected is True
        assert state.status == "WAITING"

        # Send a valid GPS fix
        bridge.send_gps(9.884638, 78.079518, accuracy=1.3, timestamp=1788110597000)
        time.sleep(0.2)

        state = service.get_state()
        assert state.connected is True
        assert state.status == "CONNECTED"
        assert abs(state.latitude - 9.884638) < 1e-5
        assert abs(state.longitude - 78.079518) < 1e-5
        assert state.accuracy == 1.3
        assert state.timestamp == 1788110597000

        # Send second updated GPS fix
        bridge.send_gps(9.884672, 78.079551, accuracy=0.9, timestamp=1788110600000)
        time.sleep(0.2)

        state2 = service.get_state()
        assert abs(state2.latitude - 9.884672) < 1e-5
        assert abs(state2.longitude - 78.079551) < 1e-5
        assert state2.accuracy == 0.9

        service.stop()
    finally:
        bridge.close()


def test_gps_service_malformed_and_boundary_handling():
    bridge = MockGPSBridge()
    try:
        service = PhoneGPSService(
            host=bridge.host,
            port=bridge.port,
            stale_timeout=2.0,
            reconnect_interval=0.2,
        )
        service.start()
        time.sleep(0.3)

        # Initial valid fix
        bridge.send_gps(10.0, 80.0, 2.0)
        time.sleep(0.1)
        assert service.get_state().latitude == 10.0

        # Send malformed JSON (should be ignored without crash)
        bridge.send_raw("THIS IS NOT JSON\n")
        bridge.send_raw("{latitude: invalid}\n")
        time.sleep(0.1)
        assert service.get_state().latitude == 10.0

        # Send invalid coordinates (out of bounds)
        bridge.send_raw(json.dumps({"latitude": 95.0, "longitude": 80.0}) + "\n")
        bridge.send_raw(json.dumps({"latitude": 10.0, "longitude": -190.0}) + "\n")
        time.sleep(0.1)
        assert service.get_state().latitude == 10.0

        # Send valid new fix
        bridge.send_gps(12.3456, 76.5432, 1.1)
        time.sleep(0.1)
        assert abs(service.get_state().latitude - 12.3456) < 1e-4

        service.stop()
    finally:
        bridge.close()


def test_gps_service_staleness():
    bridge = MockGPSBridge()
    try:
        # Set short stale timeout of 0.3s for testing
        service = PhoneGPSService(
            host=bridge.host,
            port=bridge.port,
            stale_timeout=0.3,
            reconnect_interval=0.2,
        )
        service.start()
        time.sleep(0.2)

        bridge.send_gps(9.884638, 78.079518, 1.3)
        time.sleep(0.1)
        assert service.get_state().status == "CONNECTED"

        # Wait past stale timeout
        time.sleep(0.4)
        state = service.get_state()
        assert state.status == "STALE"
        assert state.latitude == 9.884638  # Coordinates still available

        # Send fresh update -> back to CONNECTED
        bridge.send_gps(9.884640, 78.079520, 1.2)
        time.sleep(0.1)
        assert service.get_state().status == "CONNECTED"

        service.stop()
    finally:
        bridge.close()


def test_gps_service_reconnection():
    bridge = MockGPSBridge()
    try:
        service = PhoneGPSService(
            host=bridge.host,
            port=bridge.port,
            stale_timeout=2.0,
            reconnect_interval=0.2,
        )
        service.start()
        time.sleep(0.3)
        assert service.get_state().connected is True

        # Disconnect client
        bridge.disconnect_client()
        time.sleep(0.1)
        assert service.get_state().connected is False
        assert service.get_state().status == "WAITING"

        # Auto-reconnection should happen within reconnect interval
        time.sleep(0.5)
        assert service.get_state().connected is True

        service.stop()
    finally:
        bridge.close()


def test_gps_location_provider_and_snapshot_isolation():
    bridge = MockGPSBridge()
    try:
        service = PhoneGPSService(
            host=bridge.host,
            port=bridge.port,
            stale_timeout=5.0,
            reconnect_interval=0.2,
        )
        service.start()
        time.sleep(0.3)

        provider = GPSLocationProvider(service)

        # Before any fix, get_location raises LocationUnavailableError
        with pytest.raises(LocationUnavailableError):
            provider.get_location()

        # Send Fix #1
        bridge.send_gps(9.884638, 78.079518, accuracy=1.3)
        time.sleep(0.1)

        # Snapshot #1
        loc1 = provider.get_location()
        assert loc1.source == "phone_gps"
        assert abs(loc1.latitude - 9.884638) < 1e-5
        assert abs(loc1.longitude - 78.079518) < 1e-5

        # Move phone / Send Fix #2
        bridge.send_gps(9.884672, 78.079551, accuracy=0.8)
        time.sleep(0.1)

        # Snapshot #2
        loc2 = provider.get_location()
        assert abs(loc2.latitude - 9.884672) < 1e-5
        assert abs(loc2.longitude - 78.079551) < 1e-5

        # Snapshot #1 remains frozen and unaffected
        assert abs(loc1.latitude - 9.884638) < 1e-5
        assert abs(loc1.longitude - 78.079518) < 1e-5

        # Test geotagger integration
        metadata = Metadata(survey_id="TEST_SURVEY", latitude=loc1.latitude, longitude=loc1.longitude, source=loc1.source)
        lat, lon, src = geotag(metadata)
        assert lat == loc1.latitude
        assert lon == loc1.longitude
        assert src == "phone_gps"

        service.stop()
    finally:
        bridge.close()

