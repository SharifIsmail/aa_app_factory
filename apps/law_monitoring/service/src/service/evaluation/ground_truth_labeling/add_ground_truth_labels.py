#!/usr/bin/env python3
"""
Script to add ground truth labels to collected evaluation data.

This script reads a text file containing relevant law titles and matches them
with the collected evaluation dataset to add ground truth labels.
"""

import argparse
import json
import sys
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from loguru import logger


def load_relevant_titles(file_path: str) -> Set[str]:
    """
    Load relevant law titles from text file.

    Args:
        file_path: Path to the text file containing relevant titles

    Returns:
        Set of relevant law titles (normalized for matching)
    """
    relevant_titles = set()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines and comment lines (lines starting with #)
                if not line or line.startswith("#"):
                    continue

                # Remove inline comments (everything after the first #)
                if "#" in line:
                    line = line.split("#")[0].strip()

                # Skip empty lines after removing comments
                if not line:
                    continue

                # Remove extra whitespace and convert to lowercase
                normalized = " ".join(line.split()).lower()
                relevant_titles.add(normalized)

        logger.info(f"Loaded {len(relevant_titles)} relevant titles from text file")
        return relevant_titles

    except Exception as e:
        logger.error(f"Error loading text file: {e}")
        raise


def normalize_title(title: str) -> str:
    """
    Normalize a title for matching.

    Args:
        title: Original title

    Returns:
        Normalized title
    """
    return " ".join(title.strip().split()).lower()


def calculate_similarity(title1: str, title2: str) -> float:
    """
    Calculate similarity between two titles using SequenceMatcher.

    Args:
        title1: First title
        title2: Second title

    Returns:
        Similarity score (0.0 to 1.0)
    """
    return SequenceMatcher(None, title1, title2).ratio()


def find_best_match(
    target_title: str, relevant_titles: Set[str], similarity_threshold: float = 0.8
) -> Optional[str]:
    """
    Find the best matching relevant title for a target title.

    Args:
        target_title: Title to match
        relevant_titles: Set of relevant titles
        similarity_threshold: Minimum similarity score to consider a match

    Returns:
        Best matching title if above threshold, None otherwise
    """
    normalized_target = normalize_title(target_title)
    best_match = None
    best_score = 0.0

    for relevant_title in relevant_titles:
        score = calculate_similarity(normalized_target, relevant_title)
        if score > best_score:
            best_score = score
            best_match = relevant_title

    if best_score >= similarity_threshold:
        logger.debug(
            f"Match found: '{target_title}' -> '{best_match}' (score: {best_score:.3f})"
        )
        return best_match
    else:
        logger.debug(f"No match for: '{target_title}' (best score: {best_score:.3f})")
        return None


def load_eval_samples(dataset_dir: str) -> List[Tuple[str, Dict]]:
    """
    Load all evaluation samples from the dataset directory.

    Args:
        dataset_dir: Directory containing evaluation samples

    Returns:
        List of (sample_id, sample_data) tuples
    """
    samples = []
    dataset_path = Path(dataset_dir)

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    # Find all JSON files (excluding collection_summary.json)
    json_files = [
        f for f in dataset_path.glob("*.json") if f.name != "collection_summary.json"
    ]

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                sample_data = json.load(f)

            # Extract sample ID from filename
            sample_id = json_file.stem
            samples.append((sample_id, sample_data))

        except Exception as e:
            logger.warning(f"Error loading {json_file}: {e}")
            continue

    logger.info(f"Loaded {len(samples)} evaluation samples")
    return samples


def add_ground_truth_labels(
    samples: List[Tuple[str, Dict]],
    relevant_titles: Set[str],
    similarity_threshold: float = 0.8,
) -> List[Tuple[str, Dict]]:
    """
    Add ground truth labels to evaluation samples.

    Args:
        samples: List of (sample_id, sample_data) tuples
        relevant_titles: Set of relevant law titles
        similarity_threshold: Minimum similarity score for matching

    Returns:
        List of (sample_id, sample_data) tuples with ground truth labels added
    """
    labeled_samples = []
    matches_found = 0

    for sample_id, sample_data in samples:
        # Create a copy to avoid modifying the original
        labeled_sample = sample_data.copy()

        # Extract title from metadata
        title = sample_data.get("metadata", {}).get("title", "")

        if not title:
            logger.warning(f"No title found for sample {sample_id}")
            labeled_sample["ground_truth"] = {
                "is_relevant": False,
                "reason": "No title available",
            }
        else:
            # Try to find a match
            matched_title = find_best_match(
                title, relevant_titles, similarity_threshold
            )

            if matched_title:
                labeled_sample["ground_truth"] = {
                    "is_relevant": True,
                    "matched_title": matched_title,
                    "original_title": title,
                    "reason": "Matched with relevant titles list",
                }
                matches_found += 1
            else:
                labeled_sample["ground_truth"] = {
                    "is_relevant": False,
                    "original_title": title,
                    "reason": "Not in relevant titles list",
                }

        labeled_samples.append((sample_id, labeled_sample))

    logger.info(
        f"Labeled {len(labeled_samples)} samples, found {matches_found} relevant matches"
    )
    return labeled_samples


def save_labeled_dataset(
    labeled_samples: List[Tuple[str, Dict]], output_dir: str
) -> None:
    """
    Save the labeled dataset to the output directory.

    Args:
        labeled_samples: List of (sample_id, sample_data) tuples with labels
        output_dir: Output directory for labeled dataset
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save individual samples
    for sample_id, sample_data in labeled_samples:
        output_file = output_path / f"{sample_id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(sample_data, f, indent=2, ensure_ascii=False)

    # Create summary statistics
    relevant_count = sum(
        1
        for _, data in labeled_samples
        if data.get("ground_truth", {}).get("is_relevant", False)
    )
    total_count = len(labeled_samples)

    summary = {
        "total_samples": total_count,
        "relevant_samples": relevant_count,
        "irrelevant_samples": total_count - relevant_count,
        "relevance_ratio": relevant_count / total_count if total_count > 0 else 0,
        "labeling_info": {
            "method": "Title matching with text file",
            "similarity_threshold": 0.8,
            "created_at": datetime.now().isoformat(),
        },
    }

    summary_file = output_path / "labeling_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved labeled dataset to {output_dir}")
    logger.info(f"Summary: {relevant_count}/{total_count} samples labeled as relevant")


def main() -> None:
    """Main function to run the ground truth labeling process."""
    parser = argparse.ArgumentParser(
        description="Add ground truth labels to evaluation dataset"
    )
    parser.add_argument(
        "--relevant-titles-file",
        required=True,
        help="Path to text file containing relevant law titles (one per line)",
    )
    parser.add_argument(
        "--dataset-dir",
        required=True,
        help="Directory containing collected evaluation samples",
    )
    parser.add_argument(
        "--output-dir", required=True, help="Output directory for labeled dataset"
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.8,
        help="Minimum similarity score for title matching (default: 0.8)",
    )

    args = parser.parse_args()

    try:
        # Load relevant titles from text file
        logger.info(
            f"Loading relevant titles from text file: {args.relevant_titles_file}"
        )
        relevant_titles = load_relevant_titles(args.relevant_titles_file)

        # Load evaluation samples
        logger.info(f"Loading evaluation samples from {args.dataset_dir}")
        samples = load_eval_samples(args.dataset_dir)

        # Add ground truth labels
        logger.info("Adding ground truth labels...")
        labeled_samples = add_ground_truth_labels(
            samples, relevant_titles, args.similarity_threshold
        )

        # Save labeled dataset
        logger.info(f"Saving labeled dataset to {args.output_dir}")
        save_labeled_dataset(labeled_samples, args.output_dir)

        logger.info("Ground truth labeling completed successfully!")

    except Exception as e:
        logger.error(f"Error during ground truth labeling: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
