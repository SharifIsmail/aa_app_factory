#!/usr/bin/env python3
"""
Evaluation Dataset Collector for Law Monitoring

This script collects law data from EUR-Lex for specific dates to create an evaluation dataset
for summarization and relevancy classification tasks.

Usage:
    uv run eval_dataset_collector.py --output-dir ./eval_dataset --dates 2025-01-22,2025-01-27,2025-02-14,2025-02-22,2025-03-10,2025-05-07,2025-05-28,2025-06-10
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from service.law_core.eur_lex_service import EurLexService
from service.law_core.models import TaskStatus, WorkLog
from service.law_core.tools.visit_webpage_tool import VisitWebpageUserAgentTool
from service.models import LegalAct


class EvalDatasetCollector:
    """Collects evaluation dataset from EUR-Lex for specified dates."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize services
        self.eur_lex_service = EurLexService.get_instance()

        # Create a mock work log for the webpage tool
        self.mock_work_log = WorkLog(
            id="eval_dataset_collector", status=TaskStatus.IN_PROGRESS, tasks=[]
        )

    def fetch_laws_for_date(self, date: datetime) -> List[LegalAct]:
        """Fetch all legal acts for a specific date."""
        logger.info(f"Fetching laws for date: {date.date()}")

        try:
            response = self.eur_lex_service.get_legal_acts_by_date_range(
                start_date=date, end_date=date, limit=1000
            )

            logger.info(
                f"Found {len(response.legal_acts)} legal acts for {date.date()}"
            )
            return response.legal_acts

        except Exception as e:
            logger.error(f"Error fetching laws for {date.date()}: {e}")
            return []

    def fetch_law_text(self, legal_act: LegalAct) -> Optional[str]:
        """Fetch the law text content from the expression URL."""
        logger.info(f"Fetching law text for: {legal_act.title[:100]}...")

        try:
            # Create webpage tool
            webpage_tool = VisitWebpageUserAgentTool(
                data_storage=None,  # No storage needed for evaluation
                execution_id=f"eval_{legal_act.expression_url.split('/')[-1]}",
                work_log=self.mock_work_log,
                repo_key="eval_dataset",
            )

            # Fetch the law text
            law_text = webpage_tool.forward(legal_act.expression_url)

            # Check if the fetch was successful
            if law_text.startswith("Error:"):
                logger.error(f"Failed to fetch law text: {law_text}")
                return None

            logger.info(f"Successfully fetched law text ({len(law_text)} characters)")
            return law_text

        except Exception as e:
            logger.error(f"Error fetching law text for {legal_act.expression_url}: {e}")
            return None

    def create_metadata(self, legal_act: LegalAct) -> Dict:
        """Create metadata dictionary for the legal act."""
        return {
            "title": legal_act.title,
            "expression_url": legal_act.expression_url,
            "pdf_url": legal_act.pdf_url,
            "publication_date": legal_act.publication_date.isoformat()
            if legal_act.publication_date
            else None,
            "document_date": legal_act.document_date.isoformat()
            if legal_act.document_date
            else None,
            "effect_date": legal_act.effect_date.isoformat()
            if legal_act.effect_date
            else None,
            "end_validity_date": legal_act.end_validity_date.isoformat()
            if legal_act.end_validity_date
            else None,
            "notification_date": legal_act.notification_date.isoformat()
            if legal_act.notification_date
            else None,
            "eurovoc_labels": legal_act.eurovoc_labels or [],
        }

    def save_eval_sample(
        self, legal_act: LegalAct, law_text: str, date: datetime
    ) -> None:
        """Save a single evaluation sample to JSON file."""
        # Create a unique filename based on the legal act
        act_id = legal_act.expression_url.split("/")[-1]
        filename = f"{date.strftime('%Y-%m-%d')}_{act_id}.json"
        filepath = self.output_dir / filename

        # Create the evaluation sample
        eval_sample = {
            "law_text": law_text,
            "metadata": self.create_metadata(legal_act),
            "collection_info": {
                "collected_at": datetime.now().isoformat(),
                "source_date": date.isoformat(),
                "act_id": act_id,
            },
        }

        # Save to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(eval_sample, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved evaluation sample: {filename}")

    def collect_dataset(self, dates: List[datetime]) -> None:
        """Collect the complete evaluation dataset for all specified dates."""
        logger.info(f"Starting evaluation dataset collection for {len(dates)} dates")

        total_laws = 0
        successful_fetches = 0

        for date in dates:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"Processing date: {date.date()}")
            logger.info(f"{'=' * 60}")

            # Fetch laws for this date
            legal_acts = self.fetch_laws_for_date(date)
            total_laws += len(legal_acts)

            if not legal_acts:
                logger.warning(f"No legal acts found for {date.date()}")
                continue

            # Process each legal act
            for i, legal_act in enumerate(legal_acts, 1):
                logger.info(
                    f"\nProcessing law {i}/{len(legal_acts)}: {legal_act.title[:80]}..."
                )

                # Fetch law text
                law_text = self.fetch_law_text(legal_act)

                if law_text:
                    # Save the evaluation sample
                    self.save_eval_sample(legal_act, law_text, date)
                    successful_fetches += 1
                else:
                    logger.warning(
                        f"Failed to fetch law text for: {legal_act.title[:80]}..."
                    )

        # Create summary
        logger.info(f"\n{'=' * 60}")
        logger.info("COLLECTION SUMMARY")
        logger.info(f"{'=' * 60}")
        logger.info(f"Total legal acts found: {total_laws}")
        logger.info(f"Successful text fetches: {successful_fetches}")
        logger.info(f"Failed fetches: {total_laws - successful_fetches}")
        logger.info(
            f"Success rate: {(successful_fetches / total_laws * 100):.1f}%"
            if total_laws > 0
            else "N/A"
        )
        logger.info(f"Output directory: {self.output_dir.absolute()}")

        # Create a summary file
        summary = {
            "collection_summary": {
                "total_laws": total_laws,
                "successful_fetches": successful_fetches,
                "failed_fetches": total_laws - successful_fetches,
                "success_rate": (successful_fetches / total_laws * 100)
                if total_laws > 0
                else 0,
                "dates_processed": [d.isoformat() for d in dates],
                "collected_at": datetime.now().isoformat(),
            }
        }

        summary_file = self.output_dir / "collection_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"Collection summary saved to: {summary_file}")


def parse_dates(date_strings: List[str]) -> List[datetime]:
    """Parse date strings into datetime objects."""
    dates = []
    for date_str in date_strings:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            dates.append(date)
        except ValueError as e:
            logger.error(f"Invalid date format '{date_str}': {e}")
            sys.exit(1)
    return dates


def main() -> None:
    """Main function to run the evaluation dataset collector."""
    parser = argparse.ArgumentParser(
        description="Collect evaluation dataset from EUR-Lex for law monitoring"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./eval_dataset"),
        help="Output directory for the evaluation dataset (default: ./eval_dataset)",
    )
    parser.add_argument(
        "--dates", nargs="+", required=True, help="List of dates in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        level=args.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # Parse dates
    dates = parse_dates(args.dates)
    logger.info(
        f"Processing {len(dates)} dates: {[d.strftime('%Y-%m-%d') for d in dates]}"
    )

    # Create collector and run
    collector = EvalDatasetCollector(args.output_dir)
    collector.collect_dataset(dates)

    logger.info("Evaluation dataset collection completed!")


if __name__ == "__main__":
    main()
