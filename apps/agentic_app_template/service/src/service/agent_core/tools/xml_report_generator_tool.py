import re
import xml.etree.ElementTree as ET

from loguru import logger
from smolagents import Tool

from service.agent_core.models import ToolLog, WorkLog
from service.agent_core.tools.fix_xml_tool import FixXMLTool
from service.agent_core.tools.llm_completion_tool import LLMCompletionTool


class GenerateXMLReportTool(Tool):
    name = "generate_xml_report"
    description = "Generates an XML report using a language model and extracts only the XML content from the response."
    inputs = {
        "full_prompt": {
            "type": "string",
            "description": "The complete prompt to send to the language model (system + data, single string).",
        }
    }
    output_type = "string"

    def __init__(
        self,
        llm_completion_tool: LLMCompletionTool,
        fix_xml_tool: FixXMLTool,
        work_log: WorkLog = None,
    ) -> None:
        self.llm_completion_tool = llm_completion_tool
        self.fix_xml_tool = fix_xml_tool
        self.work_log = work_log
        self.is_initialized = True

    def extract_xml(self, content: str) -> str:
        """
        Extract XML content from model output, handling various formats:
        1. XML enclosed in ```xml and ``` tags
        2. XML enclosed in just ``` tags
        3. Raw XML content

        Args:
            content: The text content that may contain XML

        Returns:
            Extracted XML content or the original content if no XML is found
        """
        # Try to extract XML from ```xml blocks
        if "```xml" in content and "```" in content:
            start_index = content.find("```xml") + len("```xml")
            end_index = content.find("```", start_index)
            if end_index != -1:
                return content[start_index:end_index].strip()

        # Try to extract from ``` blocks
        if "```" in content:
            # Find all code blocks
            code_blocks = re.findall(r"```(?:xml)?(.*?)```", content, re.DOTALL)
            if code_blocks:
                # Find the block that looks most like XML
                for block in code_blocks:
                    block = block.strip()
                    if block.startswith("<") and block.endswith(">"):
                        return block

        # If no code blocks, try to extract content between XML tags
        if "<" in content and ">" in content:
            # Find the first opening tag
            first_tag_start = content.find("<")
            # Find potential XML by looking for matching opening/closing tags
            if first_tag_start >= 0:
                xml_content = content[first_tag_start:]
                # Check if it has a matching closing tag
                opening_tag_match = re.search(r"<([a-zA-Z0-9_:]+)[^>]*>", xml_content)
                if opening_tag_match:
                    root_tag = opening_tag_match.group(1)
                    closing_tag = f"</{root_tag}>"
                    if closing_tag in xml_content:
                        closing_pos = xml_content.rfind(closing_tag) + len(closing_tag)
                        return xml_content[:closing_pos].strip()

        # If we couldn't extract XML, raise an exception
        logger.error("Failed to extract XML content from model output")
        logger.info(f"Model output: {content}")
        raise ValueError("No valid XML content found in model output")

    def parse_to_xml_document(self, input_data: str) -> str:
        # Extract XML content from the input
        input_data_xml = self.extract_xml(input_data)

        # Clean up the XML
        input_data_xml = input_data_xml.strip()
        if not input_data_xml.startswith("<?xml"):
            # Remove any content before the XML declaration or add one if missing
            xml_start_index = input_data_xml.find("<?xml")
            if xml_start_index > 0:
                input_data_xml = input_data_xml[xml_start_index:]
            elif input_data_xml.startswith("<"):
                # Add XML declaration if it's missing but content starts with an XML tag
                input_data_xml = (
                    '<?xml version="1.0" encoding="UTF-8"?>\n' + input_data_xml
                )

        input_data_xml = input_data_xml.replace("&", "&amp;")

        try:
            # Attempt to parse the XML to validate it
            ET.fromstring(input_data_xml)
            logger.info("XML parsing successful")
            return input_data_xml
        except Exception as e:
            logger.error(f"Error parsing XML: {e}. Fixing it via LLM.")
            logger.debug("Wrong XML:")
            logger.debug(input_data_xml)

            # Use the injected FixXMLTool to fix the XML
            fixed_xml = self.fix_xml_tool.forward(input_data_xml)

            # Extract the XML from the fixed content
            fixed_xml = self.extract_xml(fixed_xml)

            logger.info("Fixed XML generated")

            try:
                # Validate the fixed XML
                ET.fromstring(fixed_xml)
                logger.info("XML structure fixed successfully")
                return fixed_xml
            except Exception as e:
                logger.error(f"Failed to parse XML even after fixing: {e}")
                # Return the best version we have
                return fixed_xml

    def forward(self, full_prompt: str) -> str:
        tool_log = None
        if self.work_log:
            tool_log = ToolLog(
                tool_name=self.name, params={"prompt_length": len(full_prompt)}
            )
            self.work_log.tool_logs.append(tool_log)

        logger.info(f"Generating XML report from prompt ({len(full_prompt)} chars)")

        # Let exceptions propagate directly
        result = self.llm_completion_tool.forward(full_prompt, "generate_xml_report")
        xml_content = self.parse_to_xml_document(result)

        if tool_log:
            tool_log.result = f"Generated XML with {len(xml_content)} characters"

        return xml_content
