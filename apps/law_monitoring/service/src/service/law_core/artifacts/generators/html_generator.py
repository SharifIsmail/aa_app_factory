"""
HTML generator for law summary reports.
"""

import os
import re
from dataclasses import asdict

from jinja2 import Environment, FileSystemLoader, select_autoescape

from service.law_core.models import LawSummaryData

from .base_generator import BaseReportGenerator


class HTMLReportGenerator(BaseReportGenerator):
    """
    HTML report generator for law summary reports.

    Uses Jinja2 templating engine to generate professional HTML reports
    with proper styling and structured content for law analysis data.
    """

    def __init__(self) -> None:
        """Initialize the HTML generator."""
        super().__init__()

    def render(self, data: LawSummaryData) -> str:
        """
        Render law summary data as HTML using the template.

        Args:
            data: Structured law summary analysis data

        Returns:
            str: Rendered HTML content
        """
        # Convert structured data to dictionary for template processing
        data_dict = asdict(data)

        # Transform raw text fields that might contain =...= markers
        for key in ["header_raw", "roles_raw"]:
            if key in data_dict and data_dict[key]:
                data_dict[key] = self._transform_markers_to_bold(data_dict[key])

        # Transform timeline content specifically
        if "timeline" in data_dict and data_dict["timeline"].get("timeline_content"):
            data_dict["timeline"]["timeline_content"] = self._transform_markers_to_bold(
                data_dict["timeline"]["timeline_content"]
            )

        # Load and render template, use select_autoescape() to avoid possible XSS attacks
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        env = Environment(
            loader=FileSystemLoader(template_dir), autoescape=select_autoescape()
        )

        # Add custom filters
        env.filters["slugify"] = self._slugify

        template = env.get_template("law_summary_template.html")
        return template.render(data=data_dict)

    def _slugify(self, text: str) -> str:
        """
        Convert a string to a URL-friendly slug.
        Remove non-word characters, replace spaces with hyphens, and convert to lowercase.

        Args:
            text: Input text to convert to slug

        Returns:
            str: URL-friendly slug
        """
        # Remove non-word characters and replace spaces with hyphens
        text = re.sub(r"[^\w\s-]", "", text).strip().lower()
        text = re.sub(r"[\s-]+", "-", text)
        return text

    def _transform_markers_to_bold(self, text: str) -> str:
        """
        Transform =...= markers to <b>...</b> tags in text.

        Args:
            text: Input text containing =...= markers

        Returns:
            str: Text with markers replaced by <b>...</b> tags
        """
        if not text:
            return text

        # Replace =...= markers with <b>...</b> tags
        return re.sub(r"=([^=]+)=", r"<b>\1</b>", text)
