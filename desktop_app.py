import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QSettings, QSize
from PySide6.QtGui import QColor, QImage, QPixmap, QFontMetrics
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QSplitter, QStatusBar, QTabWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QHeaderView, QAbstractItemView, QSizePolicy,
)

from backend.ai.preprocessing import validate_image
from backend.core.config import settings
from backend.database.database import SessionLocal, init_db
from backend.database.repository import AnomalyRepository
from backend.database.models import Anomaly
from backend.geo.geotagger import geotag
from backend.location.base_location import LocationUnavailableError
from backend.location.gps_location import GPSLocationProvider
from backend.location.gps_service import PhoneGPSService
from backend.location.manual_location import ManualLocationProvider
from backend.location.metadata_location import MetadataLocationProvider
from backend.reports.generator import csv_report, json_report
from backend.schemas.metadata import Metadata
from backend.services.analysis_service import analyze


class ElidedLabel(QLabel):
    """
    QLabel that elides text when contents exceed available width,
    preventing long unbroken strings (e.g. filenames) from expanding parent panels.
    """
    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)
        self._raw_text = text
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setMinimumWidth(0)

    def setText(self, text: str):
        self._raw_text = text
        self.setToolTip(text)
        self._update_elided()

    def text(self) -> str:
        return self._raw_text

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elided()

    def _update_elided(self):
        if not self._raw_text:
            super().setText("")
            return
        lines = self._raw_text.split("\n")
        fm = self.fontMetrics()
        avail_width = max(10, self.width() - 4)
        elided_lines = []
        for line in lines:
            if fm.horizontalAdvance(line) > avail_width:
                elided_lines.append(fm.elidedText(line, Qt.ElideMiddle, avail_width))
            else:
                elided_lines.append(line)
        super().setText("\n".join(elided_lines))

    def minimumSizeHint(self) -> QSize:
        return QSize(0, super().minimumSizeHint().height())

    def sizeHint(self) -> QSize:
        return QSize(0, super().sizeHint().height())


class ImageView(QLabel):
    """Image viewer for sonar images with non-expanding automatic scaling."""
    def __init__(self):
        super().__init__("No image loaded")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background:#08131c; border:1px solid #294252; color:#78909c;")
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setMinimumSize(0, 0)
        self._pixmap: QPixmap | None = None

    def show_file(self, path: str):
        image = QImage(path)
        if image.isNull():
            self._pixmap = None
            self.setText("Unable to display image")
            return
        self._pixmap = QPixmap.fromImage(image)
        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self):
        if self._pixmap and not self._pixmap.isNull():
            target_size = self.size()
            if target_size.width() > 1 and target_size.height() > 1:
                scaled = self._pixmap.scaled(
                    target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scaled_pixmap()

    def minimumSizeHint(self) -> QSize:
        return QSize(0, 0)

    def sizeHint(self) -> QSize:
        return QSize(100, 100)


class CollapsiblePanel(QGroupBox):
    """A group box with built-in collapse/expand functionality."""
    def __init__(self, title: str):
        super().__init__(title)
        self.is_collapsed = False
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(4)

        # Header with collapse button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        
        self.collapse_button = QPushButton("▼")
        self.collapse_button.setMaximumWidth(28)
        self.collapse_button.setMaximumHeight(20)
        self.collapse_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #69d2c2;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                color: #8de0d1;
            }
        """)
        self.collapse_button.clicked.connect(self.toggle_collapse)
        
        header_layout.addStretch()
        header_layout.addWidget(self.collapse_button)
        self.main_layout.addLayout(header_layout)

        # Content container
        self.content_widget = QWidget()
        self.content_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(4)
        self.main_layout.addWidget(self.content_widget, 1)

    def add_widget(self, widget: QWidget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        self.content_layout.addLayout(layout)

    def toggle_collapse(self):
        self.is_collapsed = not self.is_collapsed
        self.collapse_button.setText("▲" if self.is_collapsed else "▼")
        self.content_widget.setVisible(not self.is_collapsed)


class MarineDebrisWindow(QMainWindow):
    """Main application window for Marine Debris Analysis Tool."""
    
    SETTINGS_ORG = "MarineDebris"
    SETTINGS_APP = "DesktopApp"
    SETTINGS_SPLITTER_H = "splitter_h_state"
    SETTINGS_SPLITTER_V = "splitter_v_state"
    
    def __init__(self):
        super().__init__()
        init_db()
        self.selected_file = ""
        self.metadata_file = ""
        self.result = None
        self.gps_service = PhoneGPSService(host="127.0.0.1", port=8765)
        self.gps_service.start()
        self.gps_timer = QTimer(self)
        self.gps_timer.timeout.connect(self._on_gps_poll)
        self.gps_timer.start(250)
        
        self.settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        
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
        self.load_layout_state()
        self.load_history()

    def closeEvent(self, event):
        self.save_layout_state()
        self.gps_service.stop()
        super().closeEvent(event)

    def build_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        
        # Header title
        header = QHBoxLayout()
        title = QLabel("SIDE SCAN SONAR INTELLIGENCE WORKSTATION")
        title.setStyleSheet("font-size:20px; font-weight:bold; color:#8de0d1;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Main top workspace horizontal splitter
        self.h_splitter = QSplitter(Qt.Horizontal)
        self.h_splitter.setOpaqueResize(True)
        self.h_splitter.setChildrenCollapsible(False)
        
        self.input_panel = self.build_input_location_panel()
        self.viewer_panel = self.build_sonar_viewer_panel()
        self.results_panel = self.build_detection_results_panel()
        
        self.h_splitter.addWidget(self.input_panel)
        self.h_splitter.addWidget(self.viewer_panel)
        self.h_splitter.addWidget(self.results_panel)
        
        # Assign stretch factors matching required 24% / 36% / 40%
        self.h_splitter.setStretchFactor(0, 24)
        self.h_splitter.setStretchFactor(1, 36)
        self.h_splitter.setStretchFactor(2, 40)
        
        # Vertical splitter for top workspace + history panel
        self.v_splitter = QSplitter(Qt.Vertical)
        self.v_splitter.setOpaqueResize(True)
        self.v_splitter.setChildrenCollapsible(False)
        
        self.v_splitter.addWidget(self.h_splitter)
        self.history_panel = self.build_history_panel()
        self.v_splitter.addWidget(self.history_panel)
        
        self.v_splitter.setStretchFactor(0, 70)
        self.v_splitter.setStretchFactor(1, 30)
        
        layout.addWidget(self.v_splitter, 1)
        
        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready. Select a sonar image.")

    def build_input_location_panel(self) -> CollapsiblePanel:
        panel = CollapsiblePanel("INPUT LOCATION")
        
        # Drop area
        self.drop = ElidedLabel("Drop a sonar image here\nPNG / JPG / JPEG / TIFF")
        self.drop.setAlignment(Qt.AlignCenter)
        self.drop.setAcceptDrops(True)
        self.drop.setStyleSheet("border:1px dashed #4d7985; padding:20px; color:#8daab0;")
        self.drop.dragEnterEvent = lambda e: e.acceptProposedAction() if e.mimeData().hasUrls() else None
        self.drop.dropEvent = lambda e: self.choose_file(e.mimeData().urls()[0].toLocalFile())
        panel.add_widget(self.drop)
        
        # Browse button
        browse = QPushButton("Browse image")
        browse.clicked.connect(self.browse_image)
        panel.add_widget(browse)
        
        # File info label
        self.file_info = ElidedLabel("No file selected")
        panel.add_widget(self.file_info)
        
        # Location source box
        location = QGroupBox("LOCATION SOURCE")
        form = QFormLayout(location)
        
        self.mode = QComboBox()
        self.mode.addItems(["Manual", "Phone GPS", "Metadata"])
        self.mode.currentTextChanged.connect(self.location_mode_changed)
        form.addRow("Mode", self.mode)
        
        self.latitude = QLineEdit("9.9252")
        self.longitude = QLineEdit("78.1194")
        form.addRow("Latitude", self.latitude)
        form.addRow("Longitude", self.longitude)
        
        self.metadata_button = QPushButton("Load JSON / CSV metadata")
        self.metadata_button.clicked.connect(self.browse_metadata)
        form.addRow(self.metadata_button)
        
        self.location_note = ElidedLabel("Location source: manual")
        form.addRow(self.location_note)
        
        panel.add_widget(location)
        
        # Analyze button
        self.analyze_button = QPushButton("ANALYZE SONAR IMAGE")
        self.analyze_button.setObjectName("analyze")
        self.analyze_button.clicked.connect(self.run_analysis)
        panel.add_widget(self.analyze_button)
        
        panel.content_layout.addStretch()
        return panel

    def build_sonar_viewer_panel(self) -> CollapsiblePanel:
        panel = CollapsiblePanel("SONAR IMAGE VIEWER")
        
        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.original = ImageView()
        self.processed = ImageView()
        self.annotated = ImageView()
        
        for name, view in [("Original", self.original), ("Processed", self.processed), ("Annotated", self.annotated)]:
            self.tabs.addTab(view, name)
        
        panel.add_widget(self.tabs)
        return panel

    def build_detection_results_panel(self) -> CollapsiblePanel:
        panel = CollapsiblePanel("DETECTION RESULTS")
        
        self.summary = ElidedLabel("No analysis loaded")
        panel.add_widget(self.summary)
        
        # Detection table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Object", "Confidence", "Final Score", "Priority", "Latitude", "Longitude", "Source"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        panel.add_widget(self.table)
        
        # Action buttons
        buttons = QHBoxLayout()
        save = QPushButton("Save analysis")
        save.clicked.connect(lambda: self.statusBar().showMessage("Analysis is saved in SQLite."))
        
        json_button = QPushButton("Export JSON")
        json_button.clicked.connect(lambda: self.export("json"))
        
        csv_button = QPushButton("Export CSV")
        csv_button.clicked.connect(lambda: self.export("csv"))
        
        buttons.addWidget(save)
        buttons.addWidget(json_button)
        buttons.addWidget(csv_button)
        panel.add_layout(buttons)
        
        return panel

    def build_history_panel(self) -> CollapsiblePanel:
        panel = CollapsiblePanel("ANALYSIS HISTORY")
        
        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(4)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_history)
        controls.addWidget(refresh_btn)
        
        delete_selected_btn = QPushButton("Delete Selected")
        delete_selected_btn.clicked.connect(self.delete_selected_history)
        controls.addWidget(delete_selected_btn)
        
        clear_all_btn = QPushButton("Clear All History")
        clear_all_btn.clicked.connect(self.clear_all_history)
        controls.addWidget(clear_all_btn)
        
        controls.addStretch()
        panel.add_layout(controls)
        
        self.history = QTableWidget(0, 7)
        self.history.setHorizontalHeaderLabels([
            "Timestamp", "Filename", "Detections", "Location Source", "Latitude", "Longitude", "Source"
        ])
        self.history.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history.setSelectionMode(QAbstractItemView.MultiSelection)
        self.history.cellClicked.connect(self.on_history_cell_clicked)
        self.history.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.history.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        panel.add_widget(self.history)
        
        return panel

    def browse_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select sonar image", "", "Images (*.png *.jpg *.jpeg *.tif *.tiff *.bmp)"
        )
        if path:
            self.choose_file(path)

    def choose_file(self, path: str):
        try:
            width, height = validate_image(
                Path(path).read_bytes(), Path(path).name, settings.max_upload_size_mb * 1024 * 1024
            )
            self.selected_file = path
            size = Path(path).stat().st_size / 1024
            self.file_info.setText(f"{Path(path).name}\n{width} x {height} px | {size:.1f} KB")
            self.drop.setText(Path(path).name)
            self.statusBar().showMessage("Image ready for analysis")
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Invalid image", str(exc))

    def browse_metadata(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load location metadata", "", "Metadata (*.json *.csv)"
        )
        if path:
            try:
                location = MetadataLocationProvider(path).get_location()
                self.metadata_file = path
                self.mode.setCurrentText("Metadata")
                self.latitude.setText(str(location.latitude))
                self.longitude.setText(str(location.longitude))
                self.location_note.setText(f"Location source: metadata ({Path(path).name})")
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid metadata", str(exc))

    def location_mode_changed(self, mode: str):
        self._update_location_ui()

    def _on_gps_poll(self):
        mode = self.mode.currentText()
        if mode in ("Phone GPS", "live_gps", "phone_gps"):
            self._update_location_ui()

    def _update_location_ui(self):
        mode = self.mode.currentText()
        if mode in ("Phone GPS", "live_gps", "phone_gps"):
            state = self.gps_service.get_state()
            if state.latitude is not None and state.longitude is not None:
                self.latitude.setText(f"{state.latitude:.6f}")
                self.longitude.setText(f"{state.longitude:.6f}")
            if state.status == "CONNECTED":
                acc = f" | Acc: {state.accuracy:.1f}m" if state.accuracy is not None else ""
                self.location_note.setText(f"Location source: Phone GPS (CONNECTED{acc})")
            elif state.status == "STALE":
                self.location_note.setText(
                    f"Location source: Phone GPS (STALE - last fix: {state.latitude:.6f}, {state.longitude:.6f})"
                )
            else:
                self.location_note.setText(f"Location source: Phone GPS ({state.status})")
        elif mode in ("Metadata", "metadata"):
            name = Path(self.metadata_file).name if self.metadata_file else "none"
            self.location_note.setText(f"Location source: metadata ({name})")
        else:
            self.location_note.setText("Location source: manual")

    def run_analysis(self):
        if not self.selected_file:
            return QMessageBox.warning(self, "Image required", "Select a sonar image first.")
        try:
            mode = self.mode.currentText()
            if mode in ("Metadata", "metadata"):
                if not self.metadata_file:
                    return QMessageBox.warning(
                        self, "Metadata required", "Load a JSON or CSV metadata file first."
                    )
                location = MetadataLocationProvider(self.metadata_file).get_location()
            elif mode in ("Phone GPS", "live_gps", "phone_gps"):
                location = GPSLocationProvider(self.gps_service).get_location()
            else:
                location = ManualLocationProvider(
                    float(self.latitude.text()), float(self.longitude.text())
                ).get_location()
            
            metadata = Metadata(
                survey_id="SURVEY_SAMPLE",
                latitude=location.latitude,
                longitude=location.longitude,
                source=location.source,
            )
            
            with SessionLocal() as db:
                self.result = analyze(
                    Path(self.selected_file).read_bytes(),
                    Path(self.selected_file).name,
                    metadata,
                    AnomalyRepository(db),
                    demo=False,
                )
            
            self.show_result()
            self.load_history()
        except (OSError, ValueError, RuntimeError) as exc:
            QMessageBox.critical(self, "Analysis failed", str(exc))

    def show_result(self):
        image = self.result["image"]
        self.original.show_file(image["original_path"])
        self.processed.show_file(image["processed_path"])
        self.annotated.show_file(image["annotated_path"])
        self.tabs.setCurrentIndex(2)
        
        label = (
            "DEMONSTRATION DATA / SIMULATED LOCATION"
            if self.result["mode"] == "demo"
            else "AI ANALYSIS"
        )
        self.summary.setText(
            f"{label}\nProcessing: {self.result['processing_time_ms']} ms | "
            f"Prototype Anomaly Score shown as Final Score"
        )
        
        self.table.setRowCount(0)
        for detection in self.result["detections"]:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                detection["object_type"],
                f"{detection['model_confidence']:.1%}",
                f"{detection['final_confidence']:.1%}",
                detection["priority"],
                f"{detection['latitude']:.5f}",
                f"{detection['longitude']:.5f}",
                detection["metadata_source"],
            ]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))

    def load_history(self):
        try:
            with SessionLocal() as db:
                items = AnomalyRepository(db).list()
            
            grouped = {}
            for item in items:
                grouped.setdefault(item.survey_id, []).append(item)
            
            self.history.setRowCount(0)
            for entries in grouped.values():
                row = self.history.rowCount()
                self.history.insertRow(row)
                first = entries[0]
                
                values = [
                    first.created_at.isoformat(timespec="seconds"),
                    first.image_name,
                    str(len(entries)),
                    first.metadata_source,
                    f"{first.latitude:.5f}",
                    f"{first.longitude:.5f}",
                    first.metadata_source,
                ]
                
                for column, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setData(Qt.ItemDataRole.UserRole, first.survey_id)
                    self.history.setItem(row, column, item)
        except Exception:
            pass

    def on_history_cell_clicked(self, row: int, column: int):
        self.reload_history(row, column)

    def reload_history(self, row: int, _column: int):
        item = self.history.item(row, 0)
        if not item:
            return
        survey_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            with SessionLocal() as db:
                items = AnomalyRepository(db).list(survey_id)
            if not items:
                return
            
            image_path = next(
                (path for path in (Path(__file__).parent / "backend" / "data" / "uploads").glob(f"{survey_id}_*")),
                None,
            )
            if not image_path:
                return self.statusBar().showMessage("Stored image artifact is unavailable.")
            
            annotated = Path(__file__).parent / "backend" / "data" / "processed" / f"{survey_id}.png"
            processed = Path(__file__).parent / "backend" / "data" / "processed" / f"{survey_id}_processed.png"
            
            self.result = {
                "survey_id": survey_id,
                "mode": "demo" if items[0].metadata_source == "simulated" else "ai",
                "processing_time_ms": 0,
                "image": {
                    "original_path": str(image_path),
                    "processed_path": str(processed),
                    "annotated_path": str(annotated),
                },
                "detections": [
                    {
                        "object_type": det.object_type,
                        "model_confidence": det.model_confidence,
                        "final_confidence": det.final_confidence,
                        "priority": det.priority,
                        "latitude": det.latitude,
                        "longitude": det.longitude,
                        "metadata_source": det.metadata_source,
                    }
                    for det in items
                ],
            }
            self.show_result()
            self.statusBar().showMessage(f"Reloaded analysis {survey_id}")
        except Exception:
            pass

    def delete_selected_history(self):
        selected_rows = self.history.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No selection", "Select at least one history record to delete.")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm deletion",
            f"Delete {len(selected_rows)} selected history record(s)? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        
        try:
            survey_ids = []
            for row_index in selected_rows:
                row = row_index.row()
                survey_id = self.history.item(row, 0).data(Qt.ItemDataRole.UserRole)
                survey_ids.append(survey_id)
            
            with SessionLocal() as db:
                repo = AnomalyRepository(db)
                for survey_id in survey_ids:
                    repo.delete_by_survey(survey_id)
            
            self.load_history()
            self.statusBar().showMessage(f"Deleted {len(survey_ids)} history record(s).")
        except Exception as exc:
            QMessageBox.critical(self, "Deletion failed", str(exc))

    def clear_all_history(self):
        reply = QMessageBox.question(
            self,
            "Confirm clear all",
            "Clear all analysis history? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        
        try:
            with SessionLocal() as db:
                db.query(Anomaly).delete()
                db.commit()
            
            self.load_history()
            self.statusBar().showMessage("Analysis history cleared.")
        except Exception as exc:
            QMessageBox.critical(self, "Clear failed", str(exc))

    def export(self, kind: str):
        if not self.result:
            return QMessageBox.information(self, "No analysis", "Run an analysis before exporting.")
        suffix = ".json" if kind == "json" else ".csv"
        path, _ = QFileDialog.getSaveFileName(
            self, f"Export {kind.upper()}", "marine_debris_report" + suffix, f"{kind.upper()} (*{suffix})"
        )
        if not path:
            return
        try:
            with SessionLocal() as db:
                items = AnomalyRepository(db).list(self.result["survey_id"])
            payload = json.dumps(json_report(items), indent=2) if kind == "json" else csv_report(items)
            Path(path).write_text(payload, encoding="utf-8")
            self.statusBar().showMessage(f"Exported {path}")
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Export failed", str(exc))

    def save_layout_state(self):
        try:
            self.settings.setValue(self.SETTINGS_SPLITTER_H, self.h_splitter.saveState())
            self.settings.setValue(self.SETTINGS_SPLITTER_V, self.v_splitter.saveState())
            self.settings.sync()
        except Exception:
            pass

    def load_layout_state(self):
        try:
            h_state = self.settings.value(self.SETTINGS_SPLITTER_H)
            v_state = self.settings.value(self.SETTINGS_SPLITTER_V)
            
            restored_h = False
            if h_state:
                restored_h = self.h_splitter.restoreState(h_state)
            if not restored_h:
                # Proportions: ~24% (~355px) | ~36% (~533px) | ~40% (~592px) of 1480 width
                self.h_splitter.setSizes([355, 533, 592])
                
            restored_v = False
            if v_state:
                restored_v = self.v_splitter.restoreState(v_state)
            if not restored_v:
                # Top workspace 70% (~630px) / History 30% (~270px) of 900 height
                self.v_splitter.setSizes([630, 270])
        except Exception:
            self.h_splitter.setSizes([355, 533, 592])
            self.v_splitter.setSizes([630, 270])


def main():
    app = QApplication(sys.argv)
    window = MarineDebrisWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
