"""
Render HTML templates to PDF using Jinja2 + WeasyPrint.

Usage::

    svc = PdfTemplateService()
    pdf_bytes = svc.generate_pdf(
        "example_report.html",
        {"document": {...}},  # same shape as your JSON API payload
    )

Templates live under ``templates/pdf/`` (project root). Pass arbitrary JSON-like
dicts; expose fields to Jinja via top-level keys (e.g. ``document``, ``company``).
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.core.config import get_settings


def _project_root() -> Path:
    """backend/ root (parent of ``app/``)."""
    return Path(__file__).resolve().parent.parent.parent.parent


def _default_templates_dir() -> Path:
    return _project_root() / "templates" / "pdf"


class PdfTemplateService:
    """
    Load ``*.html`` Jinja2 templates and render PDF bytes.

    Not a FastAPI dependency by default — construct in a route or wrap in
    ``Depends`` if you need request-scoped configuration.
    """

    def __init__(self, templates_dir: Path | None = None) -> None:
        settings = get_settings()
        if templates_dir is not None:
            self._templates_dir = templates_dir.resolve()
        elif settings.pdf_templates_dir:
            self._templates_dir = Path(settings.pdf_templates_dir).resolve()
        else:
            self._templates_dir = _default_templates_dir()
        if not self._templates_dir.is_dir():
            raise FileNotFoundError(
                f"PDF templates directory does not exist: {self._templates_dir}"
            )
        self._env = Environment(
            loader=FileSystemLoader(str(self._templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    @property
    def templates_dir(self) -> Path:
        return self._templates_dir

    def render_html(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Render template to HTML string.

        ``context`` is passed to Jinja as keyword arguments: use keys like
        ``document``, ``data``, etc., and reference them in the template
        (e.g. ``{{ document.title }}``).
        """
        template = self._env.get_template(template_name)
        return template.render(**context)

    def generate_pdf(
        self,
        template_name: str,
        context: dict[str, Any],
        *,
        presentational_hints: bool = True,
    ) -> bytes:
        """
        Render template with ``context`` and return PDF bytes.

        ``context`` should match the JSON structure your API assembles
        (nested dicts/lists are fine).
        """
        html_string = self.render_html(template_name, context)
        base_url = self._templates_dir.as_uri()
        return HTML(
            string=html_string,
            base_url=base_url,
        ).write_pdf(
            presentational_hints=presentational_hints,
        )

    def list_templates(self) -> list[str]:
        """Return names of ``.html`` files in the templates directory."""
        return sorted(p.name for p in self._templates_dir.glob("*.html"))


@lru_cache
def get_pdf_template_service() -> PdfTemplateService:
    """Cached singleton (one templates dir per process)."""
    return PdfTemplateService()
