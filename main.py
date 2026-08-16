from io import BytesIO
from html import escape
from pathlib import Path
import sys
from typing import Optional

import pandas as pd
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from audits.audit_engine import AuditEngine
from audits.shared.validators import validate_trackvia_columns

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="SAB Catalog Auditor")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")

UPLOAD_FIELDS = [
    ("trackvia_csv", "TrackVia CSV"),
    ("directus_csv", "Directus CSV"),
    ("german_engineering_csv", "German Engineering CSV"),
    ("us_catalog_csv", "US Catalog CSV"),
    ("rubicon_excel", "Rubicon ERP"),
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
    file_extension = Path(filename).suffix.lower()
    encoding = _detect_encoding(contents)

    if file_extension in {".xlsx", ".xls"}:
        return pd.read_excel(BytesIO(contents))

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


def _summarize_upload(contents: bytes, filename: str):
    file_extension = Path(filename).suffix.lower()

    if file_extension in {".xlsx", ".xls"}:
        dataframe = pd.read_excel(BytesIO(contents))
        return "excel", int(dataframe.shape[0]), int(dataframe.shape[1]), list(dataframe.columns)

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


def _render_page(request, results, selected_audit_type, comparison_html="", report_filename="", source_status=None, audit_summary=None):
    if source_status is None:
        source_status = {
            "german_engineering": False,
            "trackvia": False,
            "directus": False,
            "us_catalog": False,
        }

    html = templates.get_template("index.html").render(
        title="SAB Catalog Auditor",
        results=results,
        selected_audit_type=selected_audit_type,
        report_filename=report_filename,
        source_status=source_status,
        audit_summary=audit_summary,
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
    rubicon_excel: Optional[UploadFile] = File(None),
):
    results = []
    uploaded_files = {}
    for field_name, label in UPLOAD_FIELDS:
        upload_file = locals()[field_name]
        if upload_file is not None and getattr(upload_file, "filename", None):
            contents = await upload_file.read()
            uploaded_files[field_name] = (contents, upload_file.filename)
            encoding, row_count, column_count, column_names = _summarize_upload(contents, upload_file.filename)
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
    audit_summary = None
    source_status = {
        "german_engineering": "german_engineering_csv" in uploaded_files,
        "trackvia": "trackvia_csv" in uploaded_files,
        "directus": "directus_csv" in uploaded_files,
        "us_catalog": "us_catalog_csv" in uploaded_files,
    }
    if "trackvia_csv" in uploaded_files and "directus_csv" in uploaded_files:
        trackvia_contents, trackvia_filename = uploaded_files["trackvia_csv"]
        directus_contents, directus_filename = uploaded_files["directus_csv"]
        trackvia_df = _load_dataframe(trackvia_contents, trackvia_filename)
        try:
            validate_trackvia_columns(trackvia_df)
        except ValueError as error:
            comparison_html = (
                '<div class="alert alert-danger mt-4" role="alert">'
                f"{escape(str(error))}"
                "</div>"
            )
            return _render_page(request, results, audit_type, comparison_html, "", source_status, None)

        directus_df = _load_dataframe(directus_contents, directus_filename)
        trackvia_df.attrs["source_filename"] = trackvia_filename
        directus_df.attrs["source_filename"] = directus_filename
        german_df = None
        us_catalog_df = None
        rubicon_df = None

        if "german_engineering_csv" in uploaded_files:
            german_contents, german_filename = uploaded_files["german_engineering_csv"]
            german_df = _load_dataframe(german_contents, german_filename)
            german_df.attrs["source_filename"] = german_filename

        if "us_catalog_csv" in uploaded_files:
            us_catalog_contents, us_catalog_filename = uploaded_files["us_catalog_csv"]
            us_catalog_df = _load_dataframe(us_catalog_contents, us_catalog_filename)
            us_catalog_df.attrs["source_filename"] = us_catalog_filename

        if "rubicon_excel" in uploaded_files:
            rubicon_contents, rubicon_filename = uploaded_files["rubicon_excel"]
            rubicon_df = _load_dataframe(rubicon_contents, rubicon_filename)
            rubicon_df.attrs["source_filename"] = rubicon_filename

        engine = AuditEngine(
            trackvia_df=trackvia_df,
            directus_df=directus_df,
            german_df=german_df,
            us_catalog_df=us_catalog_df,
            rubicon_df=rubicon_df,
            audit_type=audit_type,
        )
        audit_result = engine.run()
        comparison_html = audit_result["comparison_html"]
        report_filename = audit_result["report_filename"]
        summary_metrics = audit_result.get("summary_metrics", {})

        audit_summary = {
            "products_compared": f"{int(summary_metrics.get('products_compared', 0)):,}",
            "missing_products": f"{int(summary_metrics.get('missing_products', 0)):,}",
            "specification_mismatches": f"{int(summary_metrics.get('specification_mismatches', 0)):,}",
            "corrections_generated": f"{int(summary_metrics.get('corrections_generated', 0)):,}",
            "rubicon_weight_matches": f"{int(summary_metrics.get('rubicon_weight_matches', 0)):,}",
            "rubicon_weight_mismatches": f"{int(summary_metrics.get('rubicon_weight_mismatches', 0)):,}",
            "rubicon_not_found": f"{int(summary_metrics.get('rubicon_not_found', 0)):,}",
            "report_relative_path": f"reports/output/{report_filename}" if report_filename else "",
        }

        if report_filename:
            comparison_html += (
                '<div class="mt-4">'
                f'<a class="btn btn-success" href="/download-report/{report_filename}">Download Report</a>'
                '</div>'
            )

    return _render_page(request, results, audit_type, comparison_html, report_filename, source_status, audit_summary)


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


@app.get("/reports-output", response_class=HTMLResponse)
async def reports_output_browser():
    output_dir = Path("reports/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(
        [path for path in output_dir.iterdir() if path.is_file()],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not files:
        body = (
            "<h1>Reports Output</h1>"
            "<p>No reports found in reports/output.</p>"
            "<p><a href='/'>Back to Auditor</a></p>"
        )
        return HTMLResponse(content=body)

    rows = []
    for file_path in files:
        filename = escape(file_path.name)
        rows.append(
            "<tr>"
            f"<td>{filename}</td>"
            f"<td><a href='/download-report/{filename}'>Open</a></td>"
            "</tr>"
        )

    body = (
        "<h1>Reports Output</h1>"
        "<table border='1' cellpadding='8' cellspacing='0'>"
        "<thead><tr><th>Filename</th><th>Action</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
        "<p><a href='/'>Back to Auditor</a></p>"
    )
    return HTMLResponse(content=body)