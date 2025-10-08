import xml.etree.ElementTree as ET
from typing import Any

from service.lksg_core.persistence_service import persistence_service
from service.lksg_core.tools.general_tools import FixXMLTool


# The only function that contains unique logic, not just forwarding
def process_and_fix_xml(
    input_data: str, lite_llm_model: Any, cache_file: str | None = None
) -> str:
    # Extract XML content if wrapped in code blocks
    if "```xml" in input_data and "```" in input_data:
        start_index = input_data.find("```xml") + len("```xml")
        end_index = input_data.find("```", start_index)
        if end_index != -1:
            input_data_xml = input_data[start_index:end_index].strip()
        else:
            input_data_xml = input_data.replace("```xml", "").strip()
    else:
        input_data_xml = (
            input_data.replace("```xml", "").replace("```", "").replace("`", "")
        )

    # Process the structured_company_data_xml to fix XML parsing issues
    input_data_xml = input_data_xml.strip()
    if not input_data_xml.startswith("<?xml"):
        # Remove any content before the XML declaration or add one if missing
        xml_start_index = input_data_xml.find("<?xml")
        if xml_start_index > 0:
            input_data_xml = input_data_xml[xml_start_index:]
        elif input_data_xml.startswith("<"):
            # Add XML declaration if it's missing but content starts with an XML tag
            input_data_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + input_data_xml

    input_data_xml = input_data_xml.replace("&", "&amp;")

    try:
        xml_root = ET.fromstring(input_data_xml)
        print("XML parsing successful")
    except Exception as e:
        print(f"Error parsing XML: {e}. Fixing it via LLM.")
        print("Wrong XML:")
        print(input_data_xml)
        fix_xml_tool = FixXMLTool(lite_llm_model)
        input_data_xml = fix_xml_tool.forward(input_data_xml)
        input_data_xml = input_data_xml.split("```xml")[1].split("```")[0].strip()
        if cache_file:
            persistence_service.save_to_cache(cache_file, input_data_xml)
        print("Fixed XML:")

        try:
            xml_root = ET.fromstring(input_data_xml)  # noqa: F841
            print("XML structure fixed successfully")
        except Exception as e:
            print(f"Failed to parse XML even after fixing: {e}")

    return input_data_xml
