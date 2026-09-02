import os
import sys
from pathlib import Path
import time
import pytest
from PIL import Image

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSize
from backend.database.database import SessionLocal, init_db
from backend.database.repository import AnomalyRepository
from desktop_app import MarineDebrisWindow, ElidedLabel, ImageView, CollapsiblePanel
from tests.backend.test_gps_service import MockGPSBridge


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_ui_layout_stability_all_14_tests(qapp, tmp_path):
    init_db()
    bridge = MockGPSBridge()
    try:
        # Create window with clear settings to test fresh startup
        window = MarineDebrisWindow()
        window.settings.clear()
        window.load_layout_state()
        window.show()
        qapp.processEvents()

        # TEST 1: Start application -> approximately 24% / 36% / 40%
        sizes = window.h_splitter.sizes()
        total_w = sum(sizes)
        assert total_w > 0
        ratios = [s / total_w for s in sizes]
        print(f"\nTEST 1 initial sizes: {sizes}, ratios: {[round(r, 3) for r in ratios]}")
        assert abs(ratios[0] - 0.24) < 0.05, f"Expected ~24% for input, got {ratios[0]:.2%}"
        assert abs(ratios[1] - 0.36) < 0.05, f"Expected ~36% for viewer, got {ratios[1]:.2%}"
        assert abs(ratios[2] - 0.40) < 0.05, f"Expected ~40% for results, got {ratios[2]:.2%}"

        initial_sizes = list(sizes)

        # TEST 2: Load an image with a VERY long filename
        long_filename = "T1acYZNvmmL12fsBd4dzpVZbnDpZ8C981G5WPBIzIpnrbluvpew2Ahi5gS3KyyV1VeryLongUnbrokenFilename_sonar.png"
        long_image_path = tmp_path / long_filename
        # create small test png
        img = Image.new("L", (320, 200), color=128)
        img.save(str(long_image_path))
        
        window.choose_file(str(long_image_path))
        qapp.processEvents()
        
        sizes_after_long_file = window.h_splitter.sizes()
        print(f"TEST 2 after long filename sizes: {sizes_after_long_file}")
        assert sizes_after_long_file == initial_sizes, "Panel widths changed after loading long filename!"

        # TEST 3: Load a very large sonar image (e.g. 4000 x 3000)
        large_image_path = tmp_path / "large_sonar_4k.png"
        large_img = Image.new("L", (4000, 3000), color=100)
        large_img.save(str(large_image_path))
        
        window.choose_file(str(large_image_path))
        qapp.processEvents()
        
        sizes_after_large_image = window.h_splitter.sizes()
        print(f"TEST 3 after 4K image sizes: {sizes_after_large_image}")
        assert sizes_after_large_image == initial_sizes, "Panel widths changed after loading large image!"

        # TEST 4: Run YOLO Analysis
        window.run_analysis()
        qapp.processEvents()
        
        sizes_after_yolo = window.h_splitter.sizes()
        print(f"TEST 4 after YOLO sizes: {sizes_after_yolo}")
        assert sizes_after_yolo == initial_sizes, "Panel widths changed after running YOLO!"

        # TEST 5: Generate multiple detections in results table
        # Let's add multiple fake detections directly to test table size resistance
        for i in range(20):
            row = window.table.rowCount()
            window.table.insertRow(row)
            for col in range(7):
                window.table.setItem(row, col, None)
        qapp.processEvents()
        
        sizes_after_detections = window.h_splitter.sizes()
        print(f"TEST 5 after 20 detections sizes: {sizes_after_detections}")
        assert sizes_after_detections == initial_sizes, "Panel widths changed after adding detections!"

        # TEST 6: Receive GPS data
        window.gps_service.stop()
        from backend.location.gps_service import PhoneGPSService
        window.gps_service = PhoneGPSService(host="127.0.0.1", port=bridge.port, stale_timeout=2.0, reconnect_interval=0.2)
        window.gps_service.start()
        time.sleep(0.2)
        
        window.mode.setCurrentText("Phone GPS")
        bridge.send_gps(9.884638, 78.079518, accuracy=1.3)
        time.sleep(0.2)
        window._on_gps_poll()
        qapp.processEvents()
        
        sizes_after_gps = window.h_splitter.sizes()
        print(f"TEST 6 after GPS update sizes: {sizes_after_gps}")
        assert sizes_after_gps == initial_sizes, "Panel widths changed after GPS update!"

        # TEST 7: Add many history records
        for i in range(50):
            row = window.history.rowCount()
            window.history.insertRow(row)
        qapp.processEvents()
        
        sizes_after_history = window.h_splitter.sizes()
        print(f"TEST 7 after 50 history rows sizes: {sizes_after_history}")
        assert sizes_after_history == initial_sizes, "Panel widths changed after history addition!"

        # TEST 8: Manually drag / resize both vertical splitters
        user_custom_sizes = [280, 650, 550]
        window.h_splitter.setSizes(user_custom_sizes)
        qapp.processEvents()
        
        user_set_sizes = window.h_splitter.sizes()
        print(f"TEST 8 user custom resized sizes: {user_set_sizes}")
        assert user_set_sizes != initial_sizes, "Splitter sizes should reflect user resize"

        # TEST 9: Load another image after manual resize
        window.choose_file(str(long_image_path))
        qapp.processEvents()
        assert window.h_splitter.sizes() == user_set_sizes, "Splitter reset after loading image!"

        # TEST 10: Run YOLO after manual resize
        window.run_analysis()
        qapp.processEvents()
        assert window.h_splitter.sizes() == user_set_sizes, "Splitter reset after running YOLO!"

        # TEST 11: Update GPS after manual resize
        bridge.send_gps(9.884699, 78.079599, accuracy=0.7)
        time.sleep(0.2)
        window._on_gps_poll()
        qapp.processEvents()
        assert window.h_splitter.sizes() == user_set_sizes, "Splitter reset after GPS update!"

        # TEST 12: Refresh / delete / clear history after manual resize
        window.load_history()
        qapp.processEvents()
        assert window.h_splitter.sizes() == user_set_sizes, "Splitter reset after history reload!"

        # TEST 13: Collapse and expand sections
        window.input_panel.toggle_collapse()
        qapp.processEvents()
        assert window.h_splitter.sizes() == user_set_sizes, "Splitter changed on collapse!"
        window.input_panel.toggle_collapse()
        qapp.processEvents()
        assert window.h_splitter.sizes() == user_set_sizes, "Splitter changed on expand!"

        # TEST 14: Window resize / maximize simulation
        window.resize(1800, 1000)
        qapp.processEvents()
        resized_sizes = window.h_splitter.sizes()
        print(f"TEST 14 resized window (1800px) sizes: {resized_sizes}")
        total_resized = sum(resized_sizes)
        # Verify no single panel consumes the entire window and all panels remain visible and usable
        for sz in resized_sizes:
            assert sz > 200, f"Panel became too narrow: {sz}px"
            assert sz < total_resized * 0.7, f"Panel consumed too much width: {sz}px of {total_resized}px"

        window.gps_service.stop()
    finally:
        bridge.close()
