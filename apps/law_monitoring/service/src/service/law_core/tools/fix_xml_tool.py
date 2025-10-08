import traceback

from smolagents import Tool

from service.law_core.models import ToolLog, WorkLog
from service.law_core.tools.llm_completion_tool import LLMCompletionTool
from service.law_core.tools.xml_fix_prompts import FIX_XML_PROMPT


class FixXMLTool(Tool):
    name = "fix_xml"
    description = "Takes as input a potentially malformed XML string and returns a corrected XML string."
    inputs = {"xml_string": {"type": "string", "description": "The XML string to fix."}}
    output_type = "string"

    def __init__(
        self, llm_completion_tool: LLMCompletionTool, work_log: WorkLog = None
    ):
        self.llm_completion_tool = llm_completion_tool
        self.work_log = work_log
        self.is_initialized = True

    def forward(self, xml_string: str) -> str:
        tool_log = None
        if self.work_log:
            tool_log = ToolLog(
                tool_name=self.name,
                params={
                    "xml_string": xml_string[:100] + "..."
                    if len(xml_string) > 100
                    else xml_string
                },
            )
            self.work_log.tool_logs.append(tool_log)

        try:
            prompt = FIX_XML_PROMPT.format(xml_string=xml_string)
            result = self.llm_completion_tool.forward(prompt, "fix_xml")
            if tool_log:
                tool_log.result = result
            return result
        except Exception as e:
            traceback.print_exc()
            error_msg = f"Error: {str(e)}"
            if tool_log:
                tool_log.result = error_msg
            return error_msg
