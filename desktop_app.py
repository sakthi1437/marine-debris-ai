import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QSplitter, QStatusBar, QTabWidget, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget,
)

from backend.ai.preprocessing import validate_image
from backend.core.config import settings
from backend.database.database import SessionLocal, init_db
from backend.database.repository import AnomalyRepository
from backend.geo.geotagger import geotag
from backend.location.gps_location import GPSLocationProvider
from backend.location.base_location import LocationUnavailableError
from backend.location.manual_location import ManualLocationProvider
from backend.location.metadata_location import MetadataLocationProvider
from backend.reports.generator import csv_report, json_report
from backend.schemas.metadata import Metadata
from backend.services.analysis_service import analyze


class ImageView(QLabel):
    def __init__(self):
        super().__init__("No image loaded")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(420, 360)
        self.setStyleSheet("background:#08131c; border:1px solid #294252; color:#78909c;")

    def show_file(self, path: str):
        image = QImage(path)
        if image.isNull():
            self.setText("Unable to display image")
            return
        self.setPixmap(QPixmap.fromImage(image).scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def resizeEvent(self, event):
        pixmap = self.pixmap()
        if pixmap and not pixmap.isNull():
            self.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        super().resizeEvent(event)


class MarineDebrisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        init_db()
        self.selected_file = ""
        self.metadata_file = ""
        self.result = None
        self.setWindowTitle("Marine Debris Analysis Tool")
        self.resize(1480, 900)
        self.setStyleSheet("""
            QWidget { background:#0d1b24; color:#d7e5e8; font-size:13px; }
            QGroupBox { border:1px solid #294252; margin-top:10px; padding:12px; }
            QGroupBox::title { color:#69d2c2; subcontrol-origin:margin; left:10px; padding:0 4px; }
            QLineEdit, QComboBox, QTextEdit { background:#102631; border:1px solid #355466; padding:7px; }
            QPushButton { background:#183847; border:1px solid #3c7182; padding:8px 12px; }
            QPushButton:hover { background:#235364; }
            QPushButton#analyze { background:#0b877e; font-weight:bold; padding:11px; }
            QTabWidget::pane { border:1px solid #294252; }
            QHeaderView::section { background:#18313d; color:#8de0d1; padding:6px; }
            QTableWidget { gridline-color:#25424e; alternate-background-color:#10242e; }
        """)
        self.build_ui()
        self.load_history()

    def build_ui(self):
        root = QWidget(); layout = QVBoxLayout(root)
        header = QHBoxLayout(); title = QLabel("MARINE DEBRIS ANALYSIS TOOL\n<small>Side-scan sonar intelligence workstation</small>")
        title.setStyleSheet("font-size:20px; font-weight:bold; color:#8de0d1;")
        self.demo = QCheckBox("DEMO MODE"); self.demo.setChecked(True); self.demo.setStyleSheet("color:#f2c66d; font-weight:bold;")
        header.addWidget(title); header.addStretch(); header.addWidget(self.demo); layout.addLayout(header)
        splitter = QSplitter(Qt.Horizontal); splitter.addWidget(self.controls()); splitter.addWidget(self.viewer()); splitter.addWidget(self.results()); splitter.setSizes([300, 650, 470]); layout.addWidget(splitter, 1)
        self.history = QTableWidget(0, 4); self.history.setHorizontalHeaderLabels(["Timestamp", "Filename", "Detections", "Location"]); self.history.cellClicked.connect(self.reload_history)
        history_box = QGroupBox("ANALYSIS HISTORY"); history_layout = QVBoxLayout(history_box); history_layout.addWidget(self.history); layout.addWidget(history_box, 0)
        self.log = QTextEdit(); self.log.setReadOnly(True); self.log.setMaximumHeight(80); layout.addWidget(self.log)
        self.setCentralWidget(root); self.setStatusBar(QStatusBar()); self.statusBar().showMessage("Ready. Select a sonar image.")

    def controls(self):
        box = QGroupBox("INPUT & LOCATION"); layout = QVBoxLayout(box)
        self.drop = QLabel("Drop a sonar image here\nPNG / JPG / JPEG / TIFF"); self.drop.setAlignment(Qt.AlignCenter); self.drop.setAcceptDrops(True); self.drop.setStyleSheet("border:1px dashed #4d7985; padding:25px; color:#8daab0;")
        self.drop.dragEnterEvent = lambda e: e.acceptProposedAction() if e.mimeData().hasUrls() else None
        self.drop.dropEvent = lambda e: self.choose_file(e.mimeData().urls()[0].toLocalFile())
        layout.addWidget(self.drop); browse = QPushButton("Browse image"); browse.clicked.connect(self.browse_image); layout.addWidget(browse)
        self.file_info = QLabel("No file selected"); self.file_info.setWordWrap(True); layout.addWidget(self.file_info)
        location = QGroupBox("LOCATION SOURCE"); form = QFormLayout(location)
        self.mode = QComboBox(); self.mode.addItems(["manual", "metadata", "live_gps", "simulated"]); self.mode.currentTextChanged.connect(self.location_mode_changed); form.addRow("Mode", self.mode)
        self.latitude = QLineEdit("9.9252"); self.longitude = QLineEdit("78.1194"); form.addRow("Latitude", self.latitude); form.addRow("Longitude", self.longitude)
        self.metadata_button = QPushButton("Load JSON / CSV metadata"); self.metadata_button.clicked.connect(self.browse_metadata); form.addRow(self.metadata_button)
        self.location_note = QLabel("Location source: manual"); self.location_note.setWordWrap(True); form.addRow(self.location_note); layout.addWidget(location)
        self.analyze_button = QPushButton("ANALYZE SONAR IMAGE"); self.analyze_button.setObjectName("analyze"); self.analyze_button.clicked.connect(self.run_analysis); layout.addWidget(self.analyze_button)
        layout.addStretch(); return box

    def viewer(self):
        box = QGroupBox("SONAR IMAGE VIEWER"); layout = QVBoxLayout(box); self.tabs = QTabWidget()
        self.original = ImageView(); self.processed = ImageView(); self.annotated = ImageView()
        for name, view in [("Original", self.original), ("Processed", self.processed), ("Annotated", self.annotated)]: self.tabs.addTab(view, name)
        layout.addWidget(self.tabs); return box

    def results(self):
        box = QGroupBox("DETECTION RESULTS"); layout = QVBoxLayout(box); self.summary = QLabel("No analysis loaded"); self.summary.setWordWrap(True); layout.addWidget(self.summary)
        self.table = QTableWidget(0, 7); self.table.setHorizontalHeaderLabels(["Object", "Confidence", "Final Score", "Priority", "Latitude", "Longitude", "Source"]); self.table.setAlternatingRowColors(True); layout.addWidget(self.table)
        buttons = QHBoxLayout(); save = QPushButton("Save analysis"); save.clicked.connect(lambda: self.statusBar().showMessage("Analysis is saved in SQLite.")); json_button = QPushButton("Export JSON"); json_button.clicked.connect(lambda: self.export("json")); csv_button = QPushButton("Export CSV"); csv_button.clicked.connect(lambda: self.export("csv")); buttons.addWidget(save); buttons.addWidget(json_button); buttons.addWidget(csv_button); layout.addLayout(buttons); return box

    def browse_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select sonar image", "", "Images (*.png *.jpg *.jpeg *.tif *.tiff *.bmp)")
        if path: self.choose_file(path)

    def choose_file(self, path):
        try:
            width, height = validate_image(Path(path).read_bytes(), Path(path).name, settings.max_upload_size_mb * 1024 * 1024)
            self.selected_file = path; size = Path(path).stat().st_size / 1024
            self.file_info.setText(f"{Path(path).name}\n{width} x {height} px | {size:.1f} KB"); self.drop.setText(Path(path).name); self.statusBar().showMessage("Image ready for analysis")
        except (OSError, ValueError) as exc: QMessageBox.warning(self, "Invalid image", str(exc))

    def browse_metadata(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load location metadata", "", "Metadata (*.json *.csv)")
        if path:
            try:
                location = MetadataLocationProvider(path).get_location(); self.metadata_file = path; self.mode.setCurrentText("metadata"); self.latitude.setText(str(location.latitude)); self.longitude.setText(str(location.longitude)); self.location_note.setText(f"Location source: metadata ({Path(path).name})")
            except ValueError as exc: QMessageBox.warning(self, "Invalid metadata", str(exc))

    def location_mode_changed(self, mode):
        if mode == "live_gps":
            try: GPSLocationProvider().get_location()
            except LocationUnavailableError as exc: self.location_note.setText(str(exc)); return
        self.location_note.setText(f"Location source: {mode}")

    def run_analysis(self):
        if not self.selected_file: return QMessageBox.warning(self, "Image required", "Select a sonar image first.")
        try:
            if self.mode.currentText() == "metadata": location = MetadataLocationProvider(self.metadata_file).get_location()
            elif self.mode.currentText() == "live_gps": location = GPSLocationProvider().get_location()
            else: location = ManualLocationProvider(float(self.latitude.text()), float(self.longitude.text())).get_location()
            metadata = Metadata(survey_id="SURVEY_SAMPLE", latitude=location.latitude, longitude=location.longitude, source="simulated" if self.demo.isChecked() else location.source)
            with SessionLocal() as db: self.result = analyze(Path(self.selected_file).read_bytes(), Path(self.selected_file).name, metadata, AnomalyRepository(db), demo=self.demo.isChecked())
            self.show_result(); self.load_history(); self.log.append(f"Completed {self.result['analysis_id']} with {len(self.result['detections'])} detections")
        except (OSError, ValueError, RuntimeError) as exc: QMessageBox.critical(self, "Analysis failed", str(exc)); self.log.append(f"ERROR: {exc}")

    def show_result(self):
        image = self.result["image"]; self.original.show_file(image["original_path"]); self.processed.show_file(image["processed_path"]); self.annotated.show_file(image["annotated_path"]); self.tabs.setCurrentIndex(2)
        label = "DEMONSTRATION DATA / SIMULATED LOCATION" if self.result["mode"] == "demo" else "AI ANALYSIS"
        self.summary.setText(f"{label}\nProcessing: {self.result['processing_time_ms']} ms | Prototype Anomaly Score shown as Final Score")
        self.table.setRowCount(0)
        for detection in self.result["detections"]:
            row = self.table.rowCount(); self.table.insertRow(row); values = [detection["object_type"], f"{detection['model_confidence']:.1%}", f"{detection['final_confidence']:.1%}", detection["priority"], f"{detection['latitude']:.5f}", f"{detection['longitude']:.5f}", detection["metadata_source"]]
            for column, value in enumerate(values): self.table.setItem(row, column, QTableWidgetItem(str(value)))

    def load_history(self):
        try:
            with SessionLocal() as db: items = AnomalyRepository(db).list()
            grouped = {}
            for item in items: grouped.setdefault(item.survey_id, []).append(item)
            self.history.setRowCount(0)
            for entries in grouped.values():
                row = self.history.rowCount(); self.history.insertRow(row); first = entries[0]; values = [first.created_at.isoformat(timespec="seconds"), first.image_name, str(len(entries)), f"{first.latitude:.4f}, {first.longitude:.4f}"]
                for column, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setData(Qt.ItemDataRole.UserRole, first.survey_id)
                    self.history.setItem(row, column, item)
        except Exception as exc: self.log.append(f"History unavailable: {exc}")

    def reload_history(self, row, _column):
        survey_id = self.history.item(row, 0).data(Qt.ItemDataRole.UserRole)
        try:
            with SessionLocal() as db: items = AnomalyRepository(db).list(survey_id)
            if not items: return
            image_path = next((path for path in (Path(__file__).parent / "backend" / "data" / "uploads").glob(f"{survey_id}_*")), None)
            if not image_path: return self.statusBar().showMessage("Stored image artifact is unavailable.")
            annotated = Path(__file__).parent / "backend" / "data" / "processed" / f"{survey_id}.png"
            processed = Path(__file__).parent / "backend" / "data" / "processed" / f"{survey_id}_processed.png"
            self.result = {"survey_id": survey_id, "mode": "demo" if items[0].metadata_source == "simulated" else "ai", "processing_time_ms": 0, "image": {"original_path": str(image_path), "processed_path": str(processed), "annotated_path": str(annotated)}, "detections": [{"object_type": item.object_type, "model_confidence": item.model_confidence, "final_confidence": item.final_confidence, "priority": item.priority, "latitude": item.latitude, "longitude": item.longitude, "metadata_source": item.metadata_source} for item in items]}
            self.show_result(); self.statusBar().showMessage(f"Reloaded analysis {survey_id}")
        except Exception as exc: self.log.append(f"History reload failed: {exc}")

    def export(self, kind):
        if not self.result: return QMessageBox.information(self, "No analysis", "Run an analysis before exporting.")
        suffix = ".json" if kind == "json" else ".csv"; path, _ = QFileDialog.getSaveFileName(self, f"Export {kind.upper()}", "marine_debris_report" + suffix, f"{kind.upper()} (*{suffix})")
        if not path: return
        try:
            with SessionLocal() as db: items = AnomalyRepository(db).list(self.result["survey_id"])
            payload = json.dumps(json_report(items), indent=2) if kind == "json" else csv_report(items)
            Path(path).write_text(payload, encoding="utf-8"); self.statusBar().showMessage(f"Exported {path}")
        except (OSError, ValueError) as exc: QMessageBox.critical(self, "Export failed", str(exc))


def main():
    app = QApplication(sys.argv); window = MarineDebrisWindow(); window.show(); sys.exit(app.exec())


if __name__ == "__main__": main()
