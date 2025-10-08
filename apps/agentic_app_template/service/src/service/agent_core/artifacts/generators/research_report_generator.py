import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional
from xml.etree.ElementTree import Element

from jinja2 import Environment, FileSystemLoader, select_autoescape

from service.agent_core.persistence_service import persistence_service


def parse_agentic_report_xml(xml_string: str) -> Dict[str, Any]:
    """
    Parse the AgenticReport XML string into a nested dictionary structure.
    """
    root = ET.fromstring(xml_string)

    def get_text(element: Optional[Element], tag: str) -> str:
        """Get text from an XML tag, return an empty string if not found."""
        if element is None:
            return ""  # Avoids calling .find() on NoneType
        child = element.find(tag)
        return child.text.strip() if child is not None and child.text else ""

    # Parse Summary section
    summary_el = root.find("Summary")
    summary_data = {"Text": get_text(summary_el, "Text")}

    # Parse KeyInsights section
    key_insights_el = root.find("KeyInsights")
    key_insights = []

    if key_insights_el is not None:
        for insight_el in key_insights_el.findall("Insight"):
            category = insight_el.get("category", "")
            text = insight_el.text.strip() if insight_el.text else ""
            key_insights.append({"category": category, "text": text})

    # Parse DetailedFindings section
    detailed_findings_el = root.find("DetailedFindings")
    sections = []

    if detailed_findings_el is not None:
        for section_el in detailed_findings_el.findall("Section"):
            title = section_el.get("title", "")
            paragraphs = []

            for para_el in section_el.findall("Paragraph"):
                paragraph_text = para_el.text.strip() if para_el.text else ""
                paragraphs.append(paragraph_text)

            sections.append({"title": title, "Paragraph": paragraphs})

    # Parse ResearchQuality section
    research_quality_el = root.find("ResearchQuality")
    research_quality = {
        "ConfidenceScore": float(
            get_text(research_quality_el, "ConfidenceScore") or 0.0
        ),
        "Reasoning": get_text(research_quality_el, "Reasoning"),
    }

    # Build the complete result dictionary
    result = {
        "Summary": summary_data,
        "KeyInsights": {"Insight": key_insights},
        "DetailedFindings": {"Section": sections},
        "ResearchQuality": research_quality,
    }

    return result


def generate_agentic_report_artifact(xml_input: str, work_log_id: str) -> str:
    """
    Parses the XML report data, renders it as HTML, and saves it to a file.

    Args:
        xml_input: XML string containing the report data
        work_log_id: ID to use for the saved file name

    Returns:
        str: The absolute path to the saved HTML file
    """
    # 1. Parse the XML into a dictionary
    report_dict = parse_agentic_report_xml(xml_input)

    # 2. Load Jinja2 template
    template_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "templates")
    )
    # initialize with autoescape to avoid XSS vulnarbiltiy
    env = Environment(
        loader=FileSystemLoader(template_dir), autoescape=select_autoescape()
    )
    template = env.get_template("final_report.html")

    # 3. Render template with parsed data
    html_output = template.render(report=report_dict)

    # 4. Save the report with a descriptive filename
    return persistence_service.save_html_report(
        html_output, work_log_id + "_agentic_report"
    )
