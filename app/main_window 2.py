from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QUrl
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QWidget


class MainWindow(QMainWindow):
    """Desktop shell for SAB Catalog Auditor menu actions."""

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

        self.setWindowTitle("SAB Catalog Auditor")
        self.resize(1100, 760)
        self.setCentralWidget(QWidget(self))

        self.create_menu_bar()

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
        generate_corrections_action = self._action("Generate Corrections", lambda: self._set_audit_type("Generate Correction Report"))

        # These route to placeholders until audit-type switching is implemented.
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
        QMessageBox.information(self, "New Audit", "New Audit action is not yet connected.")

    def _handle_run_audit(self) -> None:
        if self._run_audit_handler is not None:
            self._run_audit_handler()
            return
        QMessageBox.information(self, "Run Audit", "Run Audit action is not yet connected.")

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
        QMessageBox.information(
            self,
            "Audit Type",
            f"Audit type selection is not connected yet.\nRequested: {audit_type}",
        )
