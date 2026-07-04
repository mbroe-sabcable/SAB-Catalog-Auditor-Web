from io import BytesIO
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from audits.audit_engine import AuditEngine

app = FastAPI(title="SAB Catalog Auditor")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

UPLOAD_FIELDS = [
    ("trackvia_csv", "TrackVia CSV"),
    ("directus_csv", "Directus CSV"),
    ("german_engineering_csv", "German Engineering CSV"),
    ("us_catalog_csv", "US Catalog CSV"),
]

try:
    from importers.csv_loader import CSVLoader
except ImportError:
    CSVLoader = None


def _detect_encoding(contents: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            contents.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return "unknown"


def _load_dataframe(contents: bytes, filename: str):
    encoding = _detect_encoding(contents)

    if CSVLoader is not None:
        try:
            loader = CSVLoader()
            candidates = [contents, BytesIO(contents), filename]
            for candidate in candidates:
                for attr_name in ("load", "load_csv", "read", "read_csv"):
                    method = getattr(loader, attr_name, None)
                    if callable(method):
                        try:
                            payload = method(candidate)
                            return pd.DataFrame(payload)
                        except TypeError:
                            continue
                try:
                    payload = loader(candidate)
                    return pd.DataFrame(payload)
                except TypeError:
                    continue
        except Exception:
            pass

    return pd.read_csv(BytesIO(contents), encoding=encoding)


def _format_column_names(columns):
    if not columns:
        return "-"

    names = [str(name) for name in columns]
    if len(names) > 5:
        return ", ".join(names[:5]) + " ..."
    return ", ".join(names)


def _summarize_csv(contents: bytes, filename: str):
    encoding = _detect_encoding(contents)

    if CSVLoader is not None:
        try:
            loader = CSVLoader()
            candidates = [contents, BytesIO(contents), filename]
            for candidate in candidates:
                for attr_name in ("load", "load_csv", "read", "read_csv"):
                    method = getattr(loader, attr_name, None)
                    if callable(method):
                        try:
                            payload = method(candidate)
                            if hasattr(payload, "shape"):
                                return encoding, int(payload.shape[0]), int(payload.shape[1]), list(payload.columns)
                            if isinstance(payload, list):
                                row_count = len(payload)
                                column_count = len(payload[0]) if payload else 0
                                if payload and isinstance(payload[0], dict):
                                    column_names = list(payload[0].keys())
                                else:
                                    column_names = [f"column_{index}" for index in range(column_count)]
                                return encoding, row_count, column_count, column_names
                            dataframe = pd.DataFrame(payload)
                            return encoding, int(dataframe.shape[0]), int(dataframe.shape[1]), list(dataframe.columns)
                        except TypeError:
                            continue
                try:
                    payload = loader(candidate)
                    if hasattr(payload, "shape"):
                        return encoding, int(payload.shape[0]), int(payload.shape[1]), list(payload.columns)
                    if isinstance(payload, list):
                        row_count = len(payload)
                        column_count = len(payload[0]) if payload else 0
                        if payload and isinstance(payload[0], dict):
                            column_names = list(payload[0].keys())
                        else:
                            column_names = [f"column_{index}" for index in range(column_count)]
                        return encoding, row_count, column_count, column_names
                    dataframe = pd.DataFrame(payload)
                    return encoding, int(dataframe.shape[0]), int(dataframe.shape[1]), list(dataframe.columns)
                except TypeError:
                    continue
        except Exception:
            pass

    dataframe = pd.read_csv(BytesIO(contents), encoding=encoding)
    return encoding, int(dataframe.shape[0]), int(dataframe.shape[1]), list(dataframe.columns)


def _render_page(request, results, selected_audit_type, comparison_html="", report_filename=""):
    html = templates.get_template("index.html").render(
        title="SAB Catalog Auditor",
        results=results,
        selected_audit_type=selected_audit_type,
        report_filename=report_filename,
    )

    if comparison_html:
        html = html.replace("</body>", f"{comparison_html}</body>", 1)

    return HTMLResponse(content=html)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return _render_page(request, [], "", "")


@app.post("/audit", response_class=HTMLResponse)
async def audit(
    request: Request,
    audit_type: str = Form("Full Product Family Audit"),
    trackvia_csv: Optional[UploadFile] = File(None),
    directus_csv: Optional[UploadFile] = File(None),
    german_engineering_csv: Optional[UploadFile] = File(None),
    us_catalog_csv: Optional[UploadFile] = File(None),
):
    results = []
    uploaded_files = {}
    for field_name, label in UPLOAD_FIELDS:
        upload_file = locals()[field_name]
        if upload_file is not None and getattr(upload_file, "filename", None):
            contents = await upload_file.read()
            uploaded_files[field_name] = (contents, upload_file.filename)
            encoding, row_count, column_count, column_names = _summarize_csv(contents, upload_file.filename)
            results.append(
                {
                    "label": label,
                    "filename": upload_file.filename,
                    "encoding": encoding,
                    "row_count": row_count,
                    "column_count": column_count,
                    "column_names": _format_column_names(column_names),
                }
            )

    comparison_html = ""
    report_filename = ""
    if "trackvia_csv" in uploaded_files and "directus_csv" in uploaded_files:
        trackvia_contents, trackvia_filename = uploaded_files["trackvia_csv"]
        directus_contents, directus_filename = uploaded_files["directus_csv"]
        trackvia_df = _load_dataframe(trackvia_contents, trackvia_filename)
        directus_df = _load_dataframe(directus_contents, directus_filename)

        engine = AuditEngine(trackvia_df=trackvia_df, directus_df=directus_df, audit_type=audit_type)
        audit_result = engine.run()
        comparison_html = audit_result["comparison_html"]
        report_filename = audit_result["report_filename"]

        if report_filename:
            comparison_html += (
                '<div class="mt-4">'
                f'<a class="btn btn-success" href="/download-report/{report_filename}">Download Report</a>'
                '</div>'
            )

    return _render_page(request, results, audit_type, comparison_html, report_filename)


@app.get("/download-report/{filename}")
async def download_report(filename: str):
    report_path = Path("reports/output") / filename
    if not report_path.exists():
        return HTMLResponse("Report not found", status_code=404)

    return FileResponse(
        report_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
    )