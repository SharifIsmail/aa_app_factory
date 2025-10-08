#!/usr/bin/env python3
"""
Enhanced evaluation script that works with ground truth labels.

This script evaluates the law monitoring system's relevancy classification
performance against ground truth labels.
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from loguru import logger

from service.law_core.law_report_service import LawReportService
from service.law_core.models import WorkLog
from service.law_core.summary.summary_work_log_manager import create_work_log
from service.models import RelevancyClassifierLegalActInput


def load_labeled_samples(dataset_dir: str) -> List[Tuple[str, Dict]]:
    """
    Load labeled evaluation samples from the dataset directory.

    Args:
        dataset_dir: Directory containing labeled evaluation samples

    Returns:
        List of (sample_id, sample_data) tuples
    """
    samples = []
    dataset_path = Path(dataset_dir)

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    # Find all JSON files (excluding summary files)
    json_files = [
        f
        for f in dataset_path.glob("*.json")
        if f.name not in ["collection_summary.json", "labeling_summary.json"]
    ]

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                sample_data = json.load(f)

            # Verify that the sample has ground truth labels
            if "ground_truth" not in sample_data:
                logger.warning(
                    f"Sample {json_file.stem} missing ground truth labels, skipping"
                )
                continue

            # Extract sample ID from filename
            sample_id = json_file.stem
            samples.append((sample_id, sample_data))

        except Exception as e:
            logger.warning(f"Error loading {json_file}: {e}")
            continue

    logger.info(f"Loaded {len(samples)} labeled evaluation samples")
    return samples


def create_mock_work_log() -> WorkLog:
    """Create a mock work log for evaluation purposes."""
    # Use the proper work log creation function that includes all required tasks
    return create_work_log("eval_work_log")


def evaluate_single_sample(
    sample_id: str, sample_data: Dict, law_report_service: LawReportService
) -> Dict:
    """
    Evaluate a single sample using the LawReportService.

    Args:
        sample_id: Sample identifier
        sample_data: Sample data with law text and metadata
        law_report_service: Initialized LawReportService

    Returns:
        Evaluation results dictionary
    """
    try:
        law_text = sample_data["law_text"]
        metadata = sample_data["metadata"]
        ground_truth = sample_data["ground_truth"]

        subject_matter = law_report_service.summarize_subject_matter(law_text)

        # Run relevancy classification directly with full law text
        logger.debug(f"Classifying relevancy for {sample_id}")
        team_relevancy_list = law_report_service.classify_relevancy(
            RelevancyClassifierLegalActInput(
                full_text=law_text,
                title=metadata["law_title"],
                summary=subject_matter.scope_subject_matter_summary,
                url=metadata["expression_url"],
            )
        )

        # Determine predicted relevancy (consider any team with is_relevant=True as relevant)
        predicted_relevant = any(team.is_relevant for team in team_relevancy_list)

        # Get ground truth relevancy
        ground_truth_relevant = ground_truth.get("is_relevant", False)

        # Calculate confidence score (ratio of teams that found it relevant)
        relevant_teams = [team for team in team_relevancy_list if team.is_relevant]
        confidence_score = (
            len(relevant_teams) / len(team_relevancy_list)
            if team_relevancy_list
            else 0.0
        )

        # Convert TeamRelevancy objects to dictionaries for JSON serialization
        team_relevancy_dicts = [
            {
                "team_name": team.team_name,
                "is_relevant": team.is_relevant,
                "reasoning": team.reasoning,
            }
            for team in team_relevancy_list
        ]

        return {
            "sample_id": sample_id,
            "success": True,
            "ground_truth": {
                "is_relevant": ground_truth_relevant,
                "title": ground_truth.get("original_title", ""),
                "reason": ground_truth.get("reason", ""),
            },
            "prediction": {
                "is_relevant": predicted_relevant,
                "confidence_score": confidence_score,
                "team_relevancy": team_relevancy_dicts,
                "relevant_teams_count": len(relevant_teams),
                "total_teams_count": len(team_relevancy_list),
            },
            "metadata": metadata,
        }

    except Exception as e:
        logger.error(f"Error evaluating sample {sample_id}: {e}")
        return {
            "sample_id": sample_id,
            "success": False,
            "error": str(e),
            "ground_truth": sample_data.get("ground_truth", {}),
            "prediction": None,
            "metadata": sample_data.get("metadata", {}),
        }


def calculate_metrics(evaluation_results: List[Dict]) -> Dict:
    """
    Calculate evaluation metrics from results.

    Args:
        evaluation_results: List of evaluation result dictionaries

    Returns:
        Dictionary containing calculated metrics
    """
    # Filter successful evaluations
    successful_results = [r for r in evaluation_results if r["success"]]

    if not successful_results:
        return {
            "total_samples": len(evaluation_results),
            "successful_evaluations": 0,
            "failed_evaluations": len(evaluation_results),
            "error": "No successful evaluations to calculate metrics",
        }

    # Calculate confusion matrix
    tp = fp = tn = fn = 0

    for result in successful_results:
        gt_relevant = result["ground_truth"]["is_relevant"]
        pred_relevant = result["prediction"]["is_relevant"]

        if gt_relevant and pred_relevant:
            tp += 1
        elif gt_relevant and not pred_relevant:
            fn += 1
        elif not gt_relevant and pred_relevant:
            fp += 1
        else:
            tn += 1

    # Calculate metrics
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_score = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0

    # Calculate confidence statistics
    confidence_scores = [
        r["prediction"]["confidence_score"]
        for r in successful_results
        if r["prediction"] and "confidence_score" in r["prediction"]
    ]

    avg_confidence = (
        sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
    )

    # Calculate team relevancy statistics
    team_relevancy_stats = {
        "avg_relevant_teams_per_law": 0.0,
        "avg_total_teams_per_law": 0.0,
        "most_relevant_teams": [],
    }

    if successful_results:
        avg_relevant = sum(
            r["prediction"]["relevant_teams_count"] for r in successful_results
        ) / len(successful_results)
        avg_total = sum(
            r["prediction"]["total_teams_count"] for r in successful_results
        ) / len(successful_results)
        team_relevancy_stats["avg_relevant_teams_per_law"] = avg_relevant
        team_relevancy_stats["avg_total_teams_per_law"] = avg_total

        # Count which teams found laws most relevant
        team_relevance_counts: defaultdict[str, int] = defaultdict(int)
        for result in successful_results:
            for team in result["prediction"]["team_relevancy"]:
                if team["is_relevant"]:
                    team_relevance_counts[team["team_name"]] += 1

        # Sort teams by relevance count
        most_relevant_teams = sorted(
            team_relevance_counts.items(), key=lambda x: x[1], reverse=True
        )
        team_relevancy_stats["most_relevant_teams"] = most_relevant_teams[:5]  # Top 5

    return {
        "total_samples": len(evaluation_results),
        "successful_evaluations": len(successful_results),
        "failed_evaluations": len(evaluation_results) - len(successful_results),
        "confusion_matrix": {
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
        },
        "metrics": {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "accuracy": accuracy,
        },
        "confidence_stats": {
            "average_confidence": avg_confidence,
            "min_confidence": min(confidence_scores) if confidence_scores else 0.0,
            "max_confidence": max(confidence_scores) if confidence_scores else 0.0,
        },
        "team_relevancy_stats": team_relevancy_stats,
        "relevance_distribution": {
            "ground_truth_relevant": tp + fn,
            "ground_truth_irrelevant": tn + fp,
            "predicted_relevant": tp + fp,
            "predicted_irrelevant": tn + fn,
        },
    }


def save_evaluation_results(
    evaluation_results: List[Dict],
    metrics: Dict,
    output_file: str,
    law_report_service: LawReportService,
) -> None:
    """
    Save evaluation results and metrics to file.

    Args:
        evaluation_results: List of evaluation result dictionaries
        metrics: Calculated metrics dictionary
        output_file: Output file path
        law_report_service: LawReportService instance to get company config from
    """
    # Get company configuration from the existing service
    try:
        company_config = law_report_service.relevancy_classifier.company_config
        company_info = {
            "company_description": company_config.company_description,
            "teams": [
                {
                    "team_name": team.name,
                    "team_description": team.description,
                    "department": team.department,
                    "daily_processes": team.daily_processes,
                    "relevant_laws_or_topics": team.relevant_laws_or_topics,
                }
                for team in company_config.teams
            ],
            "total_teams": len(company_config.teams),
        }
        logger.info(f"Retrieved company config with {len(company_config.teams)} teams")
    except Exception as e:
        logger.warning(f"Could not retrieve company configuration: {e}")
        company_info = {"error": f"Failed to retrieve company configuration: {str(e)}"}

    output_data = {
        "evaluation_results": evaluation_results,
        "metrics": metrics,
        "company_configuration": company_info,
        "evaluation_info": {
            "evaluated_at": datetime.now().isoformat(),
            "total_samples": len(evaluation_results),
        },
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Evaluation results saved to {output_file}")


def print_evaluation_summary(metrics: Dict, company_config: Dict = None) -> None:
    """
    Print a summary of evaluation metrics to console.

    Args:
        metrics: Calculated metrics dictionary
        company_config: Company configuration dictionary (optional)
    """
    logger.info("\n" + "=" * 60)
    logger.info("EVALUATION SUMMARY")
    logger.info("=" * 60)

    if company_config and "error" not in company_config:
        logger.info("Company Configuration:")
        logger.info(f"  Description: {company_config['company_description'][:100]}...")
        logger.info(f"  Total Teams: {company_config['total_teams']}")
        logger.info(
            f"  Teams: {', '.join([team['team_name'] for team in company_config['teams']])}"
        )
    elif company_config and "error" in company_config:
        logger.info(f"Company Configuration: {company_config['error']}")

    logger.info("\nDataset Statistics:")
    logger.info(f"Total samples: {metrics['total_samples']}")
    logger.info(f"Successful evaluations: {metrics['successful_evaluations']}")
    logger.info(f"Failed evaluations: {metrics['failed_evaluations']}")

    if "error" in metrics:
        logger.info(f"Error: {metrics['error']}")
        return

    logger.info("\nConfusion Matrix:")
    cm = metrics["confusion_matrix"]
    logger.info(f"  True Positives: {cm['true_positives']}")
    logger.info(f"  False Positives: {cm['false_positives']}")
    logger.info(f"  True Negatives: {cm['true_negatives']}")
    logger.info(f"  False Negatives: {cm['false_negatives']}")

    logger.info("\nPerformance Metrics:")
    perf = metrics["metrics"]
    logger.info(f"  Precision: {perf['precision']:.3f}")
    logger.info(f"  Recall: {perf['recall']:.3f}")
    logger.info(f"  F1-Score: {perf['f1_score']:.3f}")
    logger.info(f"  Accuracy: {perf['accuracy']:.3f}")

    logger.info("\nConfidence Statistics:")
    conf = metrics["confidence_stats"]
    logger.info(f"  Average Confidence: {conf['average_confidence']:.3f}")
    logger.info(f"  Min Confidence: {conf['min_confidence']:.3f}")
    logger.info(f"  Max Confidence: {conf['max_confidence']:.3f}")

    logger.info("\nTeam Relevancy Statistics:")
    team_stats = metrics["team_relevancy_stats"]
    logger.info(
        f"  Average Relevant Teams per Law: {team_stats['avg_relevant_teams_per_law']:.2f}"
    )
    logger.info(
        f"  Average Total Teams per Law: {team_stats['avg_total_teams_per_law']:.2f}"
    )

    if team_stats["most_relevant_teams"]:
        logger.info("  Most Relevant Teams:")
        for team_name, count in team_stats["most_relevant_teams"]:
            logger.info(f"    {team_name}: {count} relevant laws")

    logger.info("\nRelevance Distribution:")
    dist = metrics["relevance_distribution"]
    logger.info(f"  Ground Truth Relevant: {dist['ground_truth_relevant']}")
    logger.info(f"  Ground Truth Irrelevant: {dist['ground_truth_irrelevant']}")
    logger.info(f"  Predicted Relevant: {dist['predicted_relevant']}")
    logger.info(f"  Predicted Irrelevant: {dist['predicted_irrelevant']}")

    logger.info("=" * 60)


def main() -> None:
    """Main function to run the evaluation with ground truth."""
    parser = argparse.ArgumentParser(
        description="Evaluate law monitoring system with ground truth labels"
    )
    parser.add_argument(
        "--dataset-dir",
        required=True,
        help="Directory containing labeled evaluation samples",
    )
    parser.add_argument(
        "--output-file", required=True, help="Output file for evaluation results"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        help="Maximum number of samples to evaluate (for testing)",
    )
    parser.add_argument("--sample-id", help="Evaluate only a specific sample ID")

    args = parser.parse_args()

    try:
        # Load labeled samples
        logger.info(f"Loading labeled samples from {args.dataset_dir}")
        samples = load_labeled_samples(args.dataset_dir)

        # Filter samples if specified
        if args.sample_id:
            samples = [(sid, data) for sid, data in samples if sid == args.sample_id]
            if not samples:
                logger.error(f"Sample ID {args.sample_id} not found")
                sys.exit(1)
            logger.info(f"Evaluating single sample: {args.sample_id}")

        if args.max_samples:
            samples = samples[: args.max_samples]
            logger.info(f"Limited to {len(samples)} samples for evaluation")

        # Initialize LawReportService
        logger.info("Initializing LawReportService")
        work_log = create_mock_work_log()
        law_report_service = LawReportService(act_id="eval_123", work_log=work_log)

        # Evaluate samples
        logger.info(f"Starting evaluation of {len(samples)} samples...")
        evaluation_results = []

        for i, (sample_id, sample_data) in enumerate(samples, 1):
            logger.info(f"Evaluating sample {i}/{len(samples)}: {sample_id}")
            result = evaluate_single_sample(sample_id, sample_data, law_report_service)
            evaluation_results.append(result)

        # Calculate metrics
        logger.info("Calculating evaluation metrics...")
        metrics = calculate_metrics(evaluation_results)

        # Save results
        logger.info(f"Saving evaluation results to {args.output_file}")
        save_evaluation_results(
            evaluation_results, metrics, args.output_file, law_report_service
        )

        # Print summary
        print_evaluation_summary(metrics)

        logger.info("Evaluation completed successfully!")

    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
