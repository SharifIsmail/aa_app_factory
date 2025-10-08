#!/usr/bin/env python3
"""
Simple script to extract law titles from dataset and save as text file.

This script extracts all law titles from your collected dataset and saves them
as a simple text file, one title per line, for easy manual editing.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

from loguru import logger


def extract_titles_from_dataset(dataset_dir: str) -> List[Dict]:
    """
    Extract all law titles from the dataset directory.

    Args:
        dataset_dir: Directory containing evaluation samples

    Returns:
        List of dictionaries with sample_id, title, and metadata
    """
    titles = []
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

            title = sample_data.get("metadata", {}).get("title", "")
            if title:
                titles.append(
                    {
                        "sample_id": json_file.stem,
                        "title": title,
                        "publication_date": sample_data.get("metadata", {}).get(
                            "publication_date", ""
                        ),
                        "eurovoc_labels": sample_data.get("metadata", {}).get(
                            "eurovoc_labels", []
                        ),
                    }
                )

        except Exception as e:
            logger.warning(f"Error loading {json_file}: {e}")
            continue

    logger.info(f"Extracted {len(titles)} titles from dataset")
    return titles


def save_titles_as_text(
    titles: List[Dict], output_file: str, include_metadata: bool = False
) -> None:
    """
    Save titles to a text file, one per line.

    Args:
        titles: List of title dictionaries
        output_file: Output text file path
        include_metadata: Whether to include sample_id and date as comments
    """
    with open(output_file, "w", encoding="utf-8") as f:
        # Write header
        f.write("# Law Titles for Manual Review\n")
        f.write("# ===========================\n")
        f.write("#\n")
        f.write("# Instructions:\n")
        f.write("# 1. All titles are commented out by default (prefixed with #)\n")
        f.write(
            "# 2. Remove the # prefix from titles that are relevant to your use case\n"
        )
        f.write("# 3. Keep irrelevant titles commented out (with # prefix)\n")
        f.write("# 4. You can add notes after the title using #\n")
        f.write("# 5. Save the file and use it with add_ground_truth_labels.py\n")
        f.write("#\n")

        # Group by publication date
        date_groups: Dict[str, List[Dict]] = {}
        for title_info in titles:
            date = title_info.get("publication_date", "Unknown")
            if date not in date_groups:
                date_groups[date] = []
            date_groups[date].append(title_info)

        # Write titles grouped by date
        for date, date_titles in sorted(date_groups.items()):
            f.write(f"\n# {date} ({len(date_titles)} titles)\n")
            f.write("#" + "=" * (len(date) + 20) + "\n")

            for title_info in date_titles:
                if include_metadata:
                    f.write(f"# Sample ID: {title_info['sample_id']}\n")
                    f.write(f"# EuroVoc: {', '.join(title_info['eurovoc_labels'])}\n")

                # Comment out all titles by default
                f.write(f"# {title_info['title']}\n")
                f.write("\n")

    logger.info(f"Saved {len(titles)} titles to: {output_file}")
    logger.info(
        "Edit this file to uncomment relevant titles, then use it with add_ground_truth_labels.py"
    )


def print_title_summary(titles: List[Dict]) -> None:
    """
    Print a summary of all titles in the dataset.

    Args:
        titles: List of title dictionaries
    """
    logger.info(f"\n{'=' * 80}")
    logger.info("DATASET TITLE SUMMARY")
    logger.info(f"{'=' * 80}")
    logger.info(f"Total titles: {len(titles)}")

    # Group by publication date
    date_groups: Dict[str, List[Dict]] = {}
    for title_info in titles:
        date = title_info.get("publication_date", "Unknown")
        if date not in date_groups:
            date_groups[date] = []
        date_groups[date].append(title_info)

    logger.info("\nTitles by publication date:")
    for date, date_titles in sorted(date_groups.items()):
        logger.info(f"  {date}: {len(date_titles)} titles")

    # Show some example titles
    logger.info("\nExample titles:")
    for i, title_info in enumerate(titles[:5], 1):
        title = title_info["title"]
        if len(title) > 100:
            title = title[:97] + "..."
        logger.info(f"  {i}. {title}")

    if len(titles) > 5:
        logger.info(f"  ... and {len(titles) - 5} more titles")

    logger.info(f"{'=' * 80}")


def main() -> None:
    """Main function to extract titles and save as text file."""
    parser = argparse.ArgumentParser(
        description="Extract law titles from dataset and save as text file"
    )
    parser.add_argument(
        "--dataset-dir", required=True, help="Directory containing evaluation samples"
    )
    parser.add_argument("--output-file", required=True, help="Output text file path")
    parser.add_argument(
        "--include-metadata",
        action="store_true",
        help="Include sample ID and EuroVoc labels as comments",
    )
    parser.add_argument(
        "--show-summary",
        action="store_true",
        help="Show summary of all titles in the dataset",
    )

    args = parser.parse_args()

    try:
        # Extract titles from dataset
        logger.info(f"Extracting titles from {args.dataset_dir}")
        titles = extract_titles_from_dataset(args.dataset_dir)

        if args.show_summary:
            print_title_summary(titles)

        # Save as text file
        logger.info(f"Saving titles to text file: {args.output_file}")
        save_titles_as_text(titles, args.output_file, args.include_metadata)

        logger.info("Title extraction completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Edit the text file to uncomment relevant titles")
        logger.info("2. Use add_ground_truth_labels.py with the edited file")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
