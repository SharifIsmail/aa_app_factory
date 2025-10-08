import json
from typing import Any

from loguru import logger

from service.agent_core.artifacts.generators.research_report_generator import (
    generate_agentic_report_artifact,
)
from service.agent_core.models import WorkLog
from service.agent_core.persistence_service import persistence_service
from service.agent_core.research_agent.model_tools_manager import (
    REPO_GOOGLE_SEARCH,
    REPO_RESEARCH_RESULTS,
    REPO_VISIT_WEBPAGE,
)
from service.agent_core.research_agent.research_prompts import (
    EXTRACT_STRUCTURED_DATA_PROMPT,
)
from service.agent_core.tools.xml_report_generator_tool import GenerateXMLReportTool


class ResearchReportGenerator:
    """Handles the generation of research reports from collected data."""

    def __init__(self, work_log: WorkLog, xml_generator_tool: GenerateXMLReportTool):
        self.work_log = work_log
        self.xml_generator_tool = xml_generator_tool

    def _prepare_research_data(self, research_topic: str) -> dict[str, Any]:
        """Prepare research data for XML generation."""
        google_search_data = list(
            self.work_log.data_storage.retrieve_all_from_repo(
                REPO_GOOGLE_SEARCH
            ).values()
        )
        visit_webpage_data = list(
            self.work_log.data_storage.retrieve_all_from_repo(
                REPO_VISIT_WEBPAGE
            ).values()
        )
        research_results_data = list(
            self.work_log.data_storage.retrieve_all_from_repo(
                REPO_RESEARCH_RESULTS
            ).values()
        )

        return {
            "research_topic": research_topic,
            "google_search_data": google_search_data,
            "visit_webpage_data": visit_webpage_data,
            "research_results": research_results_data,
            "total_google_search_items": self.work_log.data_storage.repo_length(
                REPO_GOOGLE_SEARCH
            ),
            "total_visit_webpage_items": self.work_log.data_storage.repo_length(
                REPO_VISIT_WEBPAGE
            ),
            "total_research_results": self.work_log.data_storage.repo_length(
                REPO_RESEARCH_RESULTS
            ),
        }

    def _process_research_to_xml(
        self,
        research_topic: str,
        google_search_data: Any,
        visit_webpage_data: Any,
        research_results_data: Any,
    ) -> str:
        """Process research data to XML format."""
        logger.info("Generating XML from research data...")

        # Create the full prompt with the data
        full_prompt = EXTRACT_STRUCTURED_DATA_PROMPT.format(
            user_query=research_topic,
            research_results_computed_so_far=json.dumps(
                research_results_data, indent=2
            ),
            raw_data_based_on_google_search=json.dumps(google_search_data, indent=2),
            raw_data_based_on_webpages=json.dumps(visit_webpage_data, indent=2),
        )

        logger.info(
            "Using GenerateXMLReportTool to process data for topic: {}", research_topic
        )

        research_xml_str = self.xml_generator_tool.forward(full_prompt)
        logger.info("Successfully generated and extracted XML content")

        xml_path = persistence_service.save_xml(
            research_xml_str, f"{self.work_log.id}_research"
        )
        logger.info("XML file saved to: {}", xml_path)

        return research_xml_str

    def generate(self, research_topic: str) -> str:
        """Generate the final HTML report from research data.

        Args:
            research_topic: The topic being researched

        Returns:
            str: Path to the generated HTML report
        """
        logger.info("Starting final report generation process...")

        # Step 1: Prepare research data
        logger.info("Preparing research data...")
        research_data = self._prepare_research_data(research_topic)
        logger.info("Research data prepared successfully")

        # Step 2: Process research data to XML
        logger.info("Processing research data to XML...")
        research_xml = self._process_research_to_xml(
            research_topic,
            research_data["google_search_data"],
            research_data["visit_webpage_data"],
            research_data["research_results"],
        )
        logger.info("Research data processed to XML successfully")

        # Step 3: Generate HTML report
        logger.info("Generating final HTML report...")

        try:
            html_report_path = generate_agentic_report_artifact(
                research_xml, self.work_log.id
            )
            logger.info("HTML report generated and saved to: {}", html_report_path)

            # Store the absolute path to the report file in the WorkLog
            self.work_log.report_file_path = html_report_path

            # Log statistics
            logger.info(
                "Total Google Search items collected: {}",
                research_data["total_google_search_items"],
            )
            logger.info(
                "Total Visit Webpage items collected: {}",
                research_data["total_visit_webpage_items"],
            )
            logger.info(
                "Total Research Results: {}", research_data["total_research_results"]
            )

            return html_report_path
        except Exception as e:
            logger.error("Error generating HTML report: {}", str(e))
            raise
