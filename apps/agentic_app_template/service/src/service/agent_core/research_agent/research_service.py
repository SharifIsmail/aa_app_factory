from loguru import logger

from service.agent_core.models import TaskStatus, WorkLog
from service.agent_core.research_agent.research_orchestrator import (
    ResearchAgentOrchestrator,
)
from service.agent_core.research_agent.research_report_generator import (
    ResearchReportGenerator,
)
from service.agent_core.research_agent.work_log_manager import (
    TaskKeys,
    create_work_log,
    update_task_status,
)
from service.settings import Settings


class ResearchService:
    """Main service facade for research operations."""

    @staticmethod
    def run_research(
        research_topic: str,
        execution_id: str,
        settings: Settings,
        research_type: str = None,
        work_log: WorkLog = None,
    ) -> str:
        """Run the complete research process.

        Args:
            research_topic: The topic to research
            execution_id: Unique identifier for this research execution
            settings: Application settings
            research_type: Type of research ('basic' or 'comprehensive')
            work_log: Optional existing WorkLog to use (if None, creates new one)

        Returns:
            str: Path to the generated HTML report
        """
        logger.info("Starting research service")
        logger.info(f"Research topic: {research_topic}")
        logger.info(f"Execution ID: {execution_id}")
        logger.info(f"Research type: {research_type}")

        # Create work log if not provided
        if work_log is None:
            if research_type is None:
                research_type = "comprehensive"
            work_log = create_work_log(research_type, execution_id)

        try:
            # Step 1: Run research orchestration
            logger.info("Initializing research orchestrator...")
            research_agent_orchestrator = ResearchAgentOrchestrator(
                work_log, settings, execution_id
            )

            logger.info("Running research orchestration...")
            research_agent_orchestrator.run(research_topic)

            # Check if cancelled during orchestration
            if (
                work_log.status == TaskStatus.FAILED
                or work_log.status == TaskStatus.CANCELLED
            ):
                logger.warning("Research was cancelled during orchestration")
                return ""

            # Step 2: Generate final report
            logger.info("Initializing report generator...")
            update_task_status(
                work_log, TaskKeys.GENERATE_RESEARCH_REPORT, TaskStatus.IN_PROGRESS
            )

            xml_generator_tool = research_agent_orchestrator.xml_generator_tool
            if xml_generator_tool is None:
                logger.error(
                    "XML generator tool not available - cannot generate report"
                )
                work_log.status = TaskStatus.FAILED
                update_task_status(
                    work_log, TaskKeys.GENERATE_RESEARCH_REPORT, TaskStatus.FAILED
                )
                return ""

            report_generator = ResearchReportGenerator(work_log, xml_generator_tool)

            logger.info("Generating final research report...")
            html_report_path = report_generator.generate(research_topic)

            update_task_status(
                work_log, TaskKeys.GENERATE_RESEARCH_REPORT, TaskStatus.COMPLETED
            )
            work_log.status = TaskStatus.COMPLETED

            logger.info("Research service completed successfully!")
            logger.info(f"Report saved to: {html_report_path}")

            return html_report_path

        except Exception as e:
            logger.error(f"Error in research service: {str(e)}")
            logger.exception("Research service error")
            work_log.status = TaskStatus.FAILED
            raise
