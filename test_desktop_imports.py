#!/usr/bin/env python3
"""Test script to verify desktop_app.py can be imported"""

import sys
from pathlib import Path

print("=" * 60)
print("TESTING DESKTOP APP IMPORTS")
print("=" * 60)

try:
    # Test basic imports that desktop_app.py uses
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QImage, QPixmap
    from PySide6.QtWidgets import QApplication, QMainWindow
    print("✓ PySide6 imports successful")
except ImportError as e:
    print(f"✗ PySide6 import failed: {e}")
    sys.exit(1)

try:
    from backend.ai.preprocessing import validate_image
    print("✓ backend.ai.preprocessing imports successful")
except ImportError as e:
    print(f"✗ backend.ai.preprocessing import failed: {e}")
    sys.exit(1)

try:
    from backend.core.config import settings
    print("✓ backend.core.config imports successful")
except ImportError as e:
    print(f"✗ backend.core.config import failed: {e}")
    sys.exit(1)

try:
    from backend.database.database import SessionLocal, init_db
    print("✓ backend.database.database imports successful")
except ImportError as e:
    print(f"✗ backend.database.database import failed: {e}")
    sys.exit(1)

try:
    from backend.database.repository import AnomalyRepository
    print("✓ backend.database.repository imports successful")
except ImportError as e:
    print(f"✗ backend.database.repository import failed: {e}")
    sys.exit(1)

try:
    from backend.geo.geotagger import geotag
    print("✓ backend.geo.geotagger imports successful")
except ImportError as e:
    print(f"✗ backend.geo.geotagger import failed: {e}")
    sys.exit(1)

try:
    from backend.location.gps_location import GPSLocationProvider
    from backend.location.base_location import LocationUnavailableError
    from backend.location.manual_location import ManualLocationProvider
    from backend.location.metadata_location import MetadataLocationProvider
    print("✓ backend.location modules imports successful")
except ImportError as e:
    print(f"✗ backend.location imports failed: {e}")
    sys.exit(1)

try:
    from backend.reports.generator import csv_report, json_report
    print("✓ backend.reports.generator imports successful")
except ImportError as e:
    print(f"✗ backend.reports.generator import failed: {e}")
    sys.exit(1)

try:
    from backend.schemas.metadata import Metadata
    print("✓ backend.schemas.metadata imports successful")
except ImportError as e:
    print(f"✗ backend.schemas.metadata import failed: {e}")
    sys.exit(1)

try:
    from backend.services.analysis_service import analyze
    print("✓ backend.services.analysis_service imports successful")
except ImportError as e:
    print(f"✗ backend.services.analysis_service import failed: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("TESTING DATABASE INITIALIZATION")
print("=" * 60)

try:
    init_db()
    print("✓ Database initialized successfully")
    
    db_path = settings.database_path
    if db_path.exists():
        size_bytes = db_path.stat().st_size
        print(f"  Database file: {db_path}")
        print(f"  Database size: {size_bytes} bytes")
    else:
        print(f"  Database will be created at: {db_path}")
except Exception as e:
    print(f"✗ Database initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("ALL DESKTOP APP IMPORTS AND INITIALIZATION SUCCESSFUL")
print("=" * 60)
