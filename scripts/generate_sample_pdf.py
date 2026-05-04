"""
Generate ``templates/pdf/example_report.out.pdf`` from ``example_report.sample.json``.

Requires WeasyPrint system libraries (see Dockerfile) and ``pip install -r requirements.txt``.

Run from repo root::

    python -m scripts.generate_sample_pdf
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.pdf.service import PdfTemplateService  # noqa: E402


def main() -> None:
    sample_path = ROOT / "templates" / "pdf" / "example_report.sample.json"
    data = json.loads(sample_path.read_text(encoding="utf-8"))
    svc = PdfTemplateService()
    pdf_bytes = svc.generate_pdf("example_report.html", data)
    out = ROOT / "templates" / "pdf" / "example_report.out.pdf"
    out.write_bytes(pdf_bytes)
    print(f"Wrote {out} ({len(pdf_bytes)} bytes)")


if __name__ == "__main__":
    main()
