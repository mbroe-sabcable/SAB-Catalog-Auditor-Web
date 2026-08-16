import os
from pathlib import Path


def get_report_directory():
    if os.name == "nt":
        report_directory = Path.home() / "Documents" / "SAB Catalog Auditor" / "Reports"
    else:
        report_directory = Path(__file__).resolve().parent / "output"

    report_directory.mkdir(parents=True, exist_ok=True)
    return report_directory
