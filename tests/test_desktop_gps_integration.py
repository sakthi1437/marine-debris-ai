import os
import sys
from pathlib import Path
import time
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from backend.database.database import SessionLocal, init_db
from backend.database.repository import AnomalyRepository
from desktop_app import MarineDebrisWindow
from tests.backend.test_gps_service import MockGPSBridge


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_desktop_gps_full_workflow(qapp, tmp_path):
    init_db()
    bridge = MockGPSBridge()
    try:
        # Instantiate window with custom port to connect to our MockGPSBridge
        window = MarineDebrisWindow()
        # Point the window's gps_service to the test bridge port
        window.gps_service.stop()
        from backend.location.gps_service import PhoneGPSService
        window.gps_service = PhoneGPSService(host="127.0.0.1", port=bridge.port, stale_timeout=3.0, reconnect_interval=0.2)
        window.gps_service.start()
        time.sleep(0.3)

        # 1. Verify initial UI state
        assert window.mode.currentText() == "Manual"
        assert window.latitude.text() == "9.9252"
        assert window.longitude.text() == "78.1194"
        assert "manual" in window.location_note.text()

        # 2. Switch to Phone GPS
        window.mode.setCurrentText("Phone GPS")
        window._on_gps_poll()
        assert "Phone GPS" in window.location_note.text()

        # 3. Stream first GPS coordinate
        bridge.send_gps(9.884638, 78.079518, accuracy=1.3)
        time.sleep(0.2)
        window._on_gps_poll()

        assert window.latitude.text() == "9.884638"
        assert window.longitude.text() == "78.079518"
        assert "CONNECTED" in window.location_note.text()
        assert "1.3m" in window.location_note.text()

        # 4. Load a test image
        uploads = list((Path(__file__).resolve().parents[1] / "backend" / "data" / "uploads").glob("*.png"))
        assert len(uploads) > 0, "Upload images should exist"
        test_image = str(uploads[0])
        window.selected_file = test_image

        # 5. Run first analysis
        window.run_analysis()
        assert window.result is not None
        assert window.result["mode"] == "ai"
        assert window.table.rowCount() == len(window.result["detections"])
        
        for det in window.result["detections"]:
            assert det["metadata_source"] == "phone_gps"
            assert abs(det["latitude"] - 9.884638) < 1e-5
            assert abs(det["longitude"] - 78.079518) < 1e-5

        analysis_1_survey = window.result["survey_id"]

        # 6. Stream second GPS coordinate (phone moves)
        bridge.send_gps(9.884672, 78.079551, accuracy=0.8)
        time.sleep(0.2)
        window._on_gps_poll()

        assert window.latitude.text() == "9.884672"
        assert window.longitude.text() == "78.079551"

        # Verify analysis #1 in SQLite retains original coordinates (snapshot rule)
        with SessionLocal() as db:
            items_1 = AnomalyRepository(db).list(analysis_1_survey)
            for item in items_1:
                assert abs(item.latitude - 9.884638) < 1e-5
                assert abs(item.longitude - 78.079518) < 1e-5
                assert item.metadata_source == "phone_gps"

        # 7. Run second analysis with new coordinates
        window.run_analysis()
        assert window.result is not None
        analysis_2_survey = window.result["survey_id"]
        assert analysis_2_survey != analysis_1_survey

        for det in window.result["detections"]:
            assert det["metadata_source"] == "phone_gps"
            assert abs(det["latitude"] - 9.884672) < 1e-5
            assert abs(det["longitude"] - 78.079551) < 1e-5

        # 8. Test Manual mode isolation
        window.mode.setCurrentText("Manual")
        window.latitude.setText("11.1111")
        window.longitude.setText("22.2222")
        window._on_gps_poll()
        # Ensure GPS poll does NOT overwrite manual values
        assert window.latitude.text() == "11.1111"
        assert window.longitude.text() == "22.2222"
        assert "manual" in window.location_note.text()

        # Clean shutdown
        window.gps_service.stop()
    finally:
        bridge.close()

