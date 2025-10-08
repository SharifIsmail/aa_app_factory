import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape

from service.lksg_core.persistence_service import persistence_service


def parse_risk_data_xml(xml_string: str) -> Dict[str, Any]:
    """
    Parse the XML string into a nested dictionary structure with grouped incidents.
    """
    root = ET.fromstring(xml_string)

    # Initialize the result dictionary
    result: Dict[str, Any] = {
        "Incident": [],
        "GroupedIncidents": {
            "ByCategory": {},
            "BySeverity": {"High": [], "Medium": [], "Low": []},
        },
    }

    # Parse each incident
    for incident_el in root.findall("Incident"):
        incident: Dict[str, str] = {
            "Description": incident_el.findtext("Description", ""),
            "Date": incident_el.findtext("Date", ""),
            "Location": incident_el.findtext("Location", ""),
            "SourceURL": incident_el.findtext("SourceURL", ""),
            "RiskCategory": incident_el.findtext("RiskCategory", ""),
            "Severity": incident_el.findtext("Severity", ""),
            "Impact": incident_el.findtext("Impact", ""),
        }
        result["Incident"].append(incident)

        # Group by category - split categories by comma and handle each one
        categories: List[str] = [
            cat.strip() for cat in incident["RiskCategory"].split(",") if cat.strip()
        ]
        for category in categories:
            if category not in result["GroupedIncidents"]["ByCategory"]:
                result["GroupedIncidents"]["ByCategory"][category] = []
            result["GroupedIncidents"]["ByCategory"][category].append(incident)

        # Group by severity
        severity = incident["Severity"]
        if severity in result["GroupedIncidents"]["BySeverity"]:
            result["GroupedIncidents"]["BySeverity"][severity].append(incident)

    return result


def render_risk_report(xml_string: str) -> str:
    """
    Parse XML data and render it using Jinja2 template.
    """
    risk_data_dict = parse_risk_data_xml(xml_string)

    templates_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../templates")
    )
    # initialized with autoescape to avoid XSS vulnarability
    env = Environment(
        loader=FileSystemLoader(templates_dir), autoescape=select_autoescape()
    )
    template = env.get_template("risk_data_template.html")

    return template.render(risk_data=risk_data_dict)


def generate_risk_data_artifact(report_data: Dict[str, Any], work_log_id: str) -> str:
    """
    Generates and saves the company data artifact.

    Returns:
        str: The absolute path to the saved file
    """

    incident_data = report_data["risk_incidents"]

    # Create XML structure for risk incidents
    root = ET.Element("RiskIncidents")

    for incident_str in incident_data:
        incident_el = ET.SubElement(root, "Incident")

        # Parse the string to extract key-value pairs
        incident_dict: Dict[str, str] = {}
        for line in incident_str.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                incident_dict[key.strip()] = value.strip()

        ET.SubElement(incident_el, "Description").text = incident_dict.get(
            "Description", ""
        )
        ET.SubElement(incident_el, "Date").text = incident_dict.get("Date", "")
        ET.SubElement(incident_el, "Location").text = incident_dict.get("Location", "")
        ET.SubElement(incident_el, "SourceURL").text = incident_dict.get(
            "Source URL", ""
        )
        ET.SubElement(incident_el, "RiskCategory").text = incident_dict.get(
            "Risk Category", ""
        )
        ET.SubElement(incident_el, "Severity").text = incident_dict.get("Severity", "")
        ET.SubElement(incident_el, "Impact").text = incident_dict.get("Impact", "")

    # Convert to XML string
    xml_string = ET.tostring(root, encoding="unicode")

    # Parse XML to render the HTML
    html_output = render_risk_report(xml_string)

    # Save HTML report
    return persistence_service.save_html_report(
        html_output, f"{work_log_id}_risks_report"
    )


if __name__ == "__main__":
    pass
