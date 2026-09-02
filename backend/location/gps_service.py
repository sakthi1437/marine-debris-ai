import json
import logging
import socket
import threading
import time
from dataclasses import dataclass
from backend.location.base_location import Location, LocationUnavailableError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GPSState:
    connected: bool
    latitude: float | None
    longitude: float | None
    accuracy: float | None
    timestamp: float | None
    status: str  # "CONNECTED", "WAITING", "DISCONNECTED", "STALE"
    last_update_monotonic: float | None = None


class PhoneGPSService:
    """
    Background service that connects to the Android GPS Bridge at 127.0.0.1:8765
    via TCP socket, parses newline-delimited JSON GPS stream, and maintains the latest valid fix.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8765,
        stale_timeout: float = 10.0,
        reconnect_interval: float = 2.0,
    ):
        self.host = host
        self.port = port
        self.stale_timeout = stale_timeout
        self.reconnect_interval = reconnect_interval

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        self._connected: bool = False
        self._latitude: float | None = None
        self._longitude: float | None = None
        self._accuracy: float | None = None
        self._timestamp: float | None = None
        self._last_fix_monotonic: float | None = None
        self._sock: socket.socket | None = None

    def start(self) -> None:
        """Start the background GPS listener thread."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._worker_loop,
                name="PhoneGPSServiceThread",
                daemon=True,
            )
            self._thread.start()
            logger.info("PhoneGPSService started, connecting to %s:%s", self.host, self.port)

    def stop(self, timeout: float = 2.0) -> None:
        """Stop the GPS listener thread and close socket."""
        self._stop_event.set()
        with self._lock:
            if self._sock is not None:
                try:
                    self._sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    self._sock.close()
                except OSError:
                    pass
                self._sock = None
            self._connected = False

        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        logger.info("PhoneGPSService stopped")

    def _worker_loop(self) -> None:
        """Main loop managing connection and reconnection."""
        while not self._stop_event.is_set():
            sock = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2.0)
                sock.connect((self.host, self.port))
                sock.settimeout(1.0)

                with self._lock:
                    self._sock = sock
                    self._connected = True
                logger.info("Connected to GPS Bridge at %s:%s", self.host, self.port)

                self._read_stream(sock)
            except (ConnectionRefusedError, TimeoutError, OSError) as exc:
                logger.debug("GPS Bridge connection error (%s:%s): %s", self.host, self.port, exc)
            finally:
                with self._lock:
                    if self._sock is sock:
                        self._sock = None
                    self._connected = False
                if sock is not None:
                    try:
                        sock.close()
                    except OSError:
                        pass

            # Wait for reconnect interval before retrying
            if not self._stop_event.is_set():
                self._stop_event.wait(self.reconnect_interval)

    def _read_stream(self, sock: socket.socket) -> None:
        """Read newline-delimited JSON stream from the socket."""
        buffer = ""
        while not self._stop_event.is_set():
            try:
                data = sock.recv(4096)
                if not data:
                    logger.info("GPS Bridge connection closed by remote host")
                    break
                buffer += data.decode("utf-8", errors="replace")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        self._process_message(line)
            except socket.timeout:
                continue
            except OSError as exc:
                if not self._stop_event.is_set():
                    logger.debug("Socket read error: %s", exc)
                break

    def _process_message(self, message: str) -> None:
        """Parse and validate single JSON GPS message."""
        try:
            payload = json.loads(message)
            if not isinstance(payload, dict):
                return

            if "latitude" not in payload or "longitude" not in payload:
                return

            lat = float(payload["latitude"])
            lon = float(payload["longitude"])

            # Validate coordinate boundaries
            if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                logger.warning("Coordinates out of bounds: lat=%s lon=%s", lat, lon)
                return

            accuracy = None
            if "accuracy" in payload and payload["accuracy"] is not None:
                acc = float(payload["accuracy"])
                if acc >= 0.0:
                    accuracy = acc

            timestamp = None
            if "timestamp" in payload and payload["timestamp"] is not None:
                ts = float(payload["timestamp"])
                timestamp = ts

            now = time.monotonic()
            with self._lock:
                self._latitude = lat
                self._longitude = lon
                self._accuracy = accuracy
                self._timestamp = timestamp
                self._last_fix_monotonic = now

            logger.debug("GPS update received: lat=%.6f lon=%.6f acc=%s", lat, lon, accuracy)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("Failed to parse GPS message %r: %s", message, exc)

    def get_state(self) -> GPSState:
        """Get the current thread-safe GPS state including connection and staleness status."""
        with self._lock:
            connected = self._connected
            lat = self._latitude
            lon = self._longitude
            acc = self._accuracy
            ts = self._timestamp
            last_monotonic = self._last_fix_monotonic

        if not connected:
            status = "WAITING"
        elif last_monotonic is None:
            status = "WAITING"
        elif (time.monotonic() - last_monotonic) > self.stale_timeout:
            status = "STALE"
        else:
            status = "CONNECTED"

        return GPSState(
            connected=connected,
            latitude=lat,
            longitude=lon,
            accuracy=acc,
            timestamp=ts,
            status=status,
            last_update_monotonic=last_monotonic,
        )

    def get_location(self) -> Location:
        """
        Return the current valid GPS Location snapshot.
        Raises LocationUnavailableError if GPS has no valid fix or is not connected.
        """
        state = self.get_state()
        if state.latitude is None or state.longitude is None:
            raise LocationUnavailableError("Phone GPS is waiting for valid satellite fix")
        if not state.connected and state.status not in ("CONNECTED", "STALE"):
            raise LocationUnavailableError("Phone GPS is disconnected")

        return Location(
            latitude=state.latitude,
            longitude=state.longitude,
            source="phone_gps",
            accuracy=state.accuracy,
            timestamp=state.timestamp,
        )


# Global default service instance for shared application use
_default_gps_service: PhoneGPSService | None = None
_service_lock = threading.Lock()


def get_default_gps_service() -> PhoneGPSService:
    global _default_gps_service
    with _service_lock:
        if _default_gps_service is None:
            _default_gps_service = PhoneGPSService()
            _default_gps_service.start()
        return _default_gps_service

