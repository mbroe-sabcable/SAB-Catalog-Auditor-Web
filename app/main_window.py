from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QObject, QThread, Qt, QUrl, Signal
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from audits.audit_runner import AuditResult, AuditRunner


AUDIT_TYPE_OPTIONS = (
    "Full Product Family Audit",
    "TrackVia vs Directus Audit",
    "Directus QA Audit",
    "Catalog Verification Audit",
    "Product Existence Audit",
)

SOURCE_FIELDS = (
    ("trackvia", "TrackVia"),
    ("directus", "Directus"),
    ("german", "German Engineering"),
    ("us_catalog", "US Catalog"),
)


class AuditWorker(QObject):
    progress_changed = Signal(int, str)
    finished = Signal(object)

    def __init__(self, source_file_paths: dict[str, str], audit_type: str):
        super().__init__()
        self._source_file_paths = dict(source_file_paths)
        self._audit_type = audit_type

    def run(self) -> None:
        runner = AuditRunner(
            source_file_paths=self._source_file_paths,
            audit_type=self._audit_type,
            stage_callback=self._emit_stage,
        )
        result = runner.run()
        self.finished.emit(result)

    def _emit_stage(self, percent: int, stage_name: str) -> None:
        self.progress_changed.emit(percent, stage_name)


class MainWindow(QMainWindow):
    """Desktop shell for SAB Catalog Auditor workflows."""

    def __init__(
        self,
        run_audit_handler: Optional[Callable[[], None]] = None,
        new_audit_handler: Optional[Callable[[], None]] = None,
        settings_handler: Optional[Callable[[], None]] = None,
        view_log_handler: Optional[Callable[[], None]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self._run_audit_handler = run_audit_handler
        self._new_audit_handler = new_audit_handler
        self._settings_handler = settings_handler
        self._view_log_handler = view_log_handler

        self._last_report_path: Optional[Path] = None
        self._worker_thread: Optional[QThread] = None
        self._worker: Optional[AuditWorker] = None

        self._audit_type_combo: Optional[QComboBox] = None
        self._file_inputs: dict[str, QLineEdit] = {}
        self._source_status_labels: dict[str, QLabel] = {}
        self._run_button: Optional[QPushButton] = None
        self._progress_bar: Optional[QProgressBar] = None
        self._progress_label: Optional[QLabel] = None
        self._status_label: Optional[QLabel] = None
        self._log_panel: Optional[QPlainTextEdit] = None

        self.setWindowTitle("SAB Catalog Auditor")
        self.resize(1100, 760)
        self.setCentralWidget(self._build_central_widget())

        self.create_menu_bar()
        self._sync_source_status()
        self._append_log("System initialized.")
        self._append_log("Ready.")

    def set_last_report_path(self, report_path: str) -> None:
        if report_path:
            self._last_report_path = Path(report_path)

    def create_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        file_menu.addAction(self._action("New Audit", self._handle_new_audit))
        file_menu.addAction(self._action("Open Report...", self._handle_open_report))
        file_menu.addAction(self._action("Open Reports Folder", self._handle_open_reports_folder))
        file_menu.addSeparator()
        file_menu.addAction(self._action("Exit", self.close))

        audit_menu = menu_bar.addMenu("Audit")
        run_audit_action = self._action("Run Audit", self._handle_run_audit)
        audit_menu.addAction(run_audit_action)
        audit_menu.addSeparator()

        full_product_action = self._action("Full Product Family Audit", lambda: self._set_audit_type("Full Product Family Audit"))
        trackvia_directus_action = self._action("TrackVia vs Directus", lambda: self._set_audit_type("TrackVia vs Directus Audit"))
        directus_qa_action = self._action("Directus QA", lambda: self._set_audit_type("Directus QA Audit"))
        catalog_verification_action = self._action("Catalog Verification", lambda: self._set_audit_type("Catalog Verification Audit"))
        product_existence_action = self._action("Product Existence", lambda: self._set_audit_type("Product Existence Audit"))
        generate_corrections_action = self._action("Generate Corrections", lambda: self._set_audit_type("Full Product Family Audit"))

        for action in (
            full_product_action,
            trackvia_directus_action,
            directus_qa_action,
            catalog_verification_action,
            product_existence_action,
            generate_corrections_action,
        ):
            audit_menu.addAction(action)

        tools_menu = menu_bar.addMenu("Tools")
        settings_action = self._action("Settings", self._handle_settings)
        tools_menu.addAction(settings_action)

        view_log_action = self._action("View Log", self._handle_view_log)
        tools_menu.addAction(view_log_action)

        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction(self._action("About SAB Catalog Auditor", self._show_about))

    def _action(self, text: str, handler: Callable[[], None]) -> QAction:
        action = QAction(text, self)
        action.triggered.connect(handler)
        return action

    def _handle_new_audit(self) -> None:
        if self._new_audit_handler is not None:
            self._new_audit_handler()
            return
        self._reset_form()

    def _handle_run_audit(self) -> None:
        if self._run_audit_handler is not None:
            self._run_audit_handler()
            return
        self._start_audit()

    def _handle_open_report(self) -> None:
        report_path = self._last_report_path
        if report_path is None or not report_path.exists():
            selected_path, _ = QFileDialog.getOpenFileName(
                self,
                "Open Report",
                str((Path("reports") / "output").resolve()),
                "Excel Reports (*.xlsx)",
            )
            if not selected_path:
                return
            report_path = Path(selected_path)

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(report_path.resolve())))

    def _handle_open_reports_folder(self) -> None:
        reports_dir = (Path("reports") / "output").resolve()
        reports_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(reports_dir)))

    def _handle_settings(self) -> None:
        if self._settings_handler is not None:
            self._settings_handler()
            return
        QMessageBox.information(self, "Settings", "Settings are not implemented yet.")

    def _handle_view_log(self) -> None:
        if self._view_log_handler is not None:
            self._view_log_handler()
            return

        log_path = (Path("reports") / "debug.txt").resolve()
        if log_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(log_path)))
            return

        QMessageBox.information(self, "View Log", "No log file found yet.")

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About SAB Catalog Auditor",
            "SAB Catalog Auditor\nVersion 1.0",
        )

    def _set_audit_type(self, audit_type: str) -> None:
        if self._audit_type_combo is None:
            return

        index = self._audit_type_combo.findText(audit_type)
        if index >= 0:
            self._audit_type_combo.setCurrentIndex(index)
            self._append_log(f"Selected audit type: {audit_type}")

    def _build_central_widget(self) -> QWidget:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header = QLabel("SAB North America Catalog Auditor")
        header.setStyleSheet("font-size: 24px; font-weight: 600;")
        layout.addWidget(header)

        subheader = QLabel("Select an audit, choose source files, and run the existing audit pipeline.")
        subheader.setStyleSheet("color: #555;")
        layout.addWidget(subheader)

        top_grid = QGridLayout()
        top_grid.setHorizontalSpacing(16)
        top_grid.setVerticalSpacing(16)
        layout.addLayout(top_grid)

        top_grid.addWidget(self._build_audit_group(), 0, 0)
        top_grid.addWidget(self._build_status_group(), 0, 1)
        top_grid.setColumnStretch(0, 3)
        top_grid.setColumnStretch(1, 2)

        layout.addWidget(self._build_files_group())
        layout.addWidget(self._build_execution_group())
        layout.addWidget(self._build_log_group(), 1)

        return container

    def _build_audit_group(self) -> QGroupBox:
        group = QGroupBox("Audit Setup", self)
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignLeft)

        self._audit_type_combo = QComboBox(group)
        self._audit_type_combo.addItems(AUDIT_TYPE_OPTIONS)
        self._audit_type_combo.currentTextChanged.connect(self._handle_audit_type_changed)
        form.addRow("Audit Type", self._audit_type_combo)

        guidance = QLabel(
            "TrackVia and Directus are required by the current runner. German Engineering and US Catalog are optional inputs that enrich the report when provided."
        )
        guidance.setWordWrap(True)
        guidance.setStyleSheet("color: #555;")
        form.addRow("", guidance)
        return group

    def _build_status_group(self) -> QGroupBox:
        group = QGroupBox("Status", self)
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        self._status_label = QLabel("Ready", group)
        self._status_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(self._status_label)

        for key, label in SOURCE_FIELDS:
            status_label = QLabel(group)
            self._source_status_labels[key] = status_label
            layout.addWidget(status_label)

        layout.addStretch(1)
        return group

    def _build_files_group(self) -> QGroupBox:
        group = QGroupBox("Input Files", self)
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        for row, (key, label) in enumerate(SOURCE_FIELDS):
            grid.addWidget(QLabel(label, group), row, 0)

            line_edit = QLineEdit(group)
            line_edit.setPlaceholderText(f"Select {label} CSV or Excel file")
            line_edit.textChanged.connect(self._sync_source_status)
            self._file_inputs[key] = line_edit
            grid.addWidget(line_edit, row, 1)

            browse_button = QPushButton("Browse...", group)
            browse_button.clicked.connect(lambda _checked=False, source_key=key, source_label=label: self._browse_for_file(source_key, source_label))
            grid.addWidget(browse_button, row, 2)

        grid.setColumnStretch(1, 1)
        return group

    def _build_execution_group(self) -> QGroupBox:
        group = QGroupBox("Execution", self)
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        button_row = QHBoxLayout()
        self._run_button = QPushButton("Run Audit", group)
        self._run_button.setMinimumHeight(40)
        self._run_button.clicked.connect(self._start_audit)
        button_row.addWidget(self._run_button)

        clear_button = QPushButton("New Audit", group)
        clear_button.setMinimumHeight(40)
        clear_button.clicked.connect(self._reset_form)
        button_row.addWidget(clear_button)
        button_row.addStretch(1)
        layout.addLayout(button_row)

        self._progress_bar = QProgressBar(group)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)

        self._progress_label = QLabel("Progress: 0%", group)
        layout.addWidget(self._progress_label)
        return group

    def _build_log_group(self) -> QGroupBox:
        group = QGroupBox("Status / Log", self)
        layout = QVBoxLayout(group)

        self._log_panel = QPlainTextEdit(group)
        self._log_panel.setReadOnly(True)
        self._log_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self._log_panel)
        return group

    def _handle_audit_type_changed(self, audit_type: str) -> None:
        if self._status_label is not None and not self._is_audit_running():
            self._status_label.setText(f"Ready: {audit_type}")

    def _browse_for_file(self, source_key: str, source_label: str) -> None:
        start_dir = str(Path.cwd())
        selected_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select {source_label} File",
            start_dir,
            "Data Files (*.csv *.xlsx *.xls)",
        )
        if not selected_path:
            return

        self._file_inputs[source_key].setText(selected_path)
        self._append_log(f"Selected {source_label}: {Path(selected_path).name}")

    def _collect_source_paths(self) -> dict[str, str]:
        return {
            key: self._file_inputs[key].text().strip()
            for key, _label in SOURCE_FIELDS
        }

    def _reset_form(self) -> None:
        if self._is_audit_running():
            QMessageBox.information(self, "Audit Running", "Wait for the current audit to finish before starting a new one.")
            return

        for line_edit in self._file_inputs.values():
            line_edit.clear()

        if self._audit_type_combo is not None:
            self._audit_type_combo.setCurrentIndex(0)

        self._last_report_path = None
        self._set_progress(0, "Ready")
        if self._status_label is not None:
            self._status_label.setText("Ready")
        if self._log_panel is not None:
            self._log_panel.clear()
            self._append_log("System initialized.")
            self._append_log("Ready.")
        self._sync_source_status()

    def _start_audit(self) -> None:
        if self._is_audit_running():
            QMessageBox.information(self, "Audit Running", "An audit is already in progress.")
            return

        source_paths = self._collect_source_paths()
        audit_type = self._selected_audit_type()

        self._append_log(f"Starting audit: {audit_type}")
        self._append_log("Dispatching to audits.audit_runner.AuditRunner.")
        self._set_running_state(True)
        self._set_progress(0, "Starting")
        if self._status_label is not None:
            self._status_label.setText(f"Running: {audit_type}")

        self._worker_thread = QThread(self)
        self._worker = AuditWorker(source_paths, audit_type)
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.progress_changed.connect(self._handle_stage_progress)
        self._worker.finished.connect(self._handle_audit_finished)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)
        self._worker_thread.finished.connect(self._clear_worker_references)
        self._worker_thread.start()

    def _handle_stage_progress(self, percent: int, stage_name: str) -> None:
        self._set_progress(percent, stage_name)
        self._append_log(f"{percent}% - {stage_name}")

    def _handle_audit_finished(self, result: object) -> None:
        self._set_running_state(False)

        if not isinstance(result, AuditResult):
            self._append_log("Audit finished with an unexpected result payload.")
            if self._status_label is not None:
                self._status_label.setText("Audit failed")
            QMessageBox.critical(self, "Audit Failed", "The audit returned an unexpected result.")
            return

        if result.success:
            self._set_progress(100, "Complete")
            if self._status_label is not None:
                self._status_label.setText(f"Completed: {result.audit_type}")
            self._append_log("Audit complete.")

            if result.summary_metrics:
                metrics_text = ", ".join(
                    f"{label.replace('_', ' ')}={value}"
                    for label, value in result.summary_metrics.items()
                )
                self._append_log(f"Summary metrics: {metrics_text}")

            if result.report_filename:
                report_path = (Path("reports") / "output" / result.report_filename).resolve()
                self.set_last_report_path(str(report_path))
                self._append_log(f"Report saved: {report_path}")

            QMessageBox.information(
                self,
                "Audit Complete",
                self._build_success_message(result),
            )
            return

        self._set_progress(0, "Failed")
        if self._status_label is not None:
            self._status_label.setText(f"Failed: {result.audit_type}")
        self._append_log(f"Audit failed: {result.error_message}")
        QMessageBox.critical(
            self,
            "Audit Failed",
            result.error_message or "The audit runner did not provide an error message.",
        )

    def _build_success_message(self, result: AuditResult) -> str:
        lines = [f"{result.audit_type} finished successfully."]
        if result.report_filename:
            lines.append(f"Report: {result.report_filename}")
        if result.summary_metrics:
            for key, value in result.summary_metrics.items():
                lines.append(f"{key.replace('_', ' ').title()}: {value}")
        return "\n".join(lines)

    def _clear_worker_references(self) -> None:
        self._worker = None
        self._worker_thread = None

    def _is_audit_running(self) -> bool:
        return self._worker_thread is not None and self._worker_thread.isRunning()

    def _selected_audit_type(self) -> str:
        if self._audit_type_combo is None:
            return AUDIT_TYPE_OPTIONS[0]
        return self._audit_type_combo.currentText()

    def _set_running_state(self, is_running: bool) -> None:
        if self._run_button is not None:
            self._run_button.setEnabled(not is_running)
        if self._audit_type_combo is not None:
            self._audit_type_combo.setEnabled(not is_running)

        for line_edit in self._file_inputs.values():
            line_edit.setEnabled(not is_running)

    def _set_progress(self, percent: int, stage_name: str) -> None:
        if self._progress_bar is not None:
            self._progress_bar.setValue(percent)
        if self._progress_label is not None:
            self._progress_label.setText(f"Progress: {percent}% - {stage_name}")

    def _sync_source_status(self) -> None:
        for key, label in SOURCE_FIELDS:
            status_label = self._source_status_labels.get(key)
            if status_label is None:
                continue

            file_path = self._file_inputs.get(key)
            is_loaded = bool(file_path and file_path.text().strip())
            state_text = "Loaded" if is_loaded else "Missing"
            marker = "OK" if is_loaded else "Missing"
            status_label.setText(f"{label}: {marker} - {state_text}")

    def _append_log(self, message: str) -> None:
        if self._log_panel is None:
            return
        self._log_panel.appendPlainText(message)
