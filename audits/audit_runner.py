from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional

import pandas as pd

from audits.audit_engine import AuditEngine


StageCallback = Callable[[int, str], None]
AuditExecutor = Callable[[AuditEngine], dict]


@dataclass
class AuditResult:
    success: bool
    audit_type: str
    report_filename: str = ""
    summary_metrics: Optional[dict] = None
    four_way_comparisons: Optional[list] = None
    comparison_html: str = ""
    error_message: str = ""


class AuditRunner:
    """Central execution engine for desktop audit workflows."""

    REQUIRED_SOURCES = ("trackvia", "directus")

    def __init__(
        self,
        source_file_paths: Dict[str, str],
        audit_type: str,
        stage_callback: Optional[StageCallback] = None,
        audit_executors: Optional[Dict[str, AuditExecutor]] = None,
    ):
        self.source_file_paths = dict(source_file_paths)
        self.audit_type = audit_type
        self._stage_callback = stage_callback
        self._audit_executors = dict(audit_executors or {})

        self._dataframes: Dict[str, Optional[pd.DataFrame]] = {
            "german": None,
            "trackvia": None,
            "directus": None,
            "us_catalog": None,
        }
        self._engine: Optional[AuditEngine] = None
        self._engine_payload: dict = {}

    def register_audit_executor(self, audit_type: str, executor: AuditExecutor) -> None:
        self._audit_executors[audit_type] = executor

    def run(self) -> AuditResult:
        try:
            self._stage(1, "Validate input files")
            self._validate_input_files()

            self._stage(2, "Load source files")
            self._load_source_files()

            self._stage(3, "Normalize data")
            self._normalize_data()

            self._stage(4, "Execute selected audit")
            self._execute_selected_audit()

            self._stage(5, "Build findings")
            findings = self._build_findings()

            self._stage(6, "Generate reports")
            report_filename = self._generate_reports()

            self._stage(7, "Complete")
            return AuditResult(
                success=True,
                audit_type=self.audit_type,
                report_filename=report_filename,
                summary_metrics=findings.get("summary_metrics", {}),
                four_way_comparisons=findings.get("four_way_comparisons", []),
                comparison_html=findings.get("comparison_html", ""),
            )
        except Exception as exc:
            return AuditResult(
                success=False,
                audit_type=self.audit_type,
                error_message=str(exc),
                summary_metrics={},
                four_way_comparisons=[],
                comparison_html="",
            )

    def _stage(self, stage_number: int, stage_name: str) -> None:
        percent = round((stage_number / 7) * 100)
        if self._stage_callback is not None:
            self._stage_callback(percent, stage_name)

    def _validate_input_files(self) -> None:
        missing_required = [
            key
            for key in self.REQUIRED_SOURCES
            if not self.source_file_paths.get(key)
        ]
        if missing_required:
            friendly_names = ", ".join(name.replace("_", " ") for name in missing_required)
            raise ValueError(f"Missing required source files: {friendly_names}")

        for key, path_value in self.source_file_paths.items():
            if not path_value:
                continue
            path = Path(path_value)
            if not path.exists() or not path.is_file():
                raise ValueError(f"Source file not found: {path}")

    def _load_source_files(self) -> None:
        for key in self._dataframes.keys():
            path_value = self.source_file_paths.get(key, "")
            if not path_value:
                self._dataframes[key] = None
                continue

            file_path = Path(path_value)
            suffix = file_path.suffix.lower()

            if suffix == ".csv":
                dataframe = self._read_csv(file_path)
            elif suffix in {".xlsx", ".xls"}:
                dataframe = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file type: {suffix}")

            dataframe.attrs["source_filename"] = file_path.name
            self._dataframes[key] = dataframe

    def _normalize_data(self) -> None:
        self._engine = AuditEngine(
            trackvia_df=self._dataframes.get("trackvia"),
            directus_df=self._dataframes.get("directus"),
            german_df=self._dataframes.get("german"),
            us_catalog_df=self._dataframes.get("us_catalog"),
            audit_type=self.audit_type,
        )

    def _execute_selected_audit(self) -> None:
        if self._engine is None:
            raise RuntimeError("Audit engine was not initialized")

        executor = self._audit_executors.get(self.audit_type) or self._audit_executors.get("*")
        if executor is None:
            self._engine_payload = self._engine.run()
            return

        payload = executor(self._engine)
        if payload is None:
            payload = {}
        self._engine_payload = dict(payload)

    def _build_findings(self) -> dict:
        return {
            "summary_metrics": self._engine_payload.get("summary_metrics", {}),
            "four_way_comparisons": self._engine_payload.get("four_way_comparisons", []),
            "comparison_html": self._engine_payload.get("comparison_html", ""),
        }

    def _generate_reports(self) -> str:
        return str(self._engine_payload.get("report_filename", ""))

    @staticmethod
    def _read_csv(file_path: Path) -> pd.DataFrame:
        encodings = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
        last_error: Optional[Exception] = None
        for encoding in encodings:
            try:
                return pd.read_csv(file_path, encoding=encoding)
            except UnicodeDecodeError as exc:
                last_error = exc
                continue

        if last_error is not None:
            raise last_error

        return pd.read_csv(file_path)
