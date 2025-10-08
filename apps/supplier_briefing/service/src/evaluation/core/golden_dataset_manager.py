import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from loguru import logger

from evaluation.core.pandas_comparator import (
    PandasComparisonConfig,
    PandasComparisonMode,
)
from evaluation.intelligence_layer_eval.supplier_briefing_models import (
    QuestionDifficulty,
)
from service.core.utils.pandas_json_utils import (
    serialize_pandas_object_to_json,
)

# Define the path to the golden dataset relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GOLDEN_DATASET_PATH = os.path.join(
    SCRIPT_DIR, "..", "data", "core", "golden_dataset.json"
)


class GoldenDatasetManager:
    """
    Manages operations on the golden_dataset.json file.
    """

    def __init__(self, dataset_path: str = GOLDEN_DATASET_PATH):
        self.dataset_path = dataset_path

    def _read_dataset(self) -> Dict[str, Any]:
        """Reads the entire golden dataset from the JSON file."""
        if not os.path.exists(self.dataset_path):
            # Create a default structure if the file doesn't exist
            return {
                "generated_at": "",
                "total_questions": 0,
                "language": "en",
                "evaluation_entries": [],
            }
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_dataset(self, data: Dict[str, Any]) -> None:
        """Writes the updated dataset back to the JSON file."""
        with open(self.dataset_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _update_entry_data(
        self,
        entry: Dict[str, Any],
        research_question: str,
        ground_truth_text: str | None,
        pandas_objects_json: Optional[List[Dict[str, str]]],
        question_difficulty: QuestionDifficulty = QuestionDifficulty.HARD,
        pandas_comparison_config: Optional[PandasComparisonConfig] = None,
    ) -> None:
        """Helper to update an existing entry's data.

        Only updates fields that are explicitly provided (not None).
        """
        entry["research_question"] = research_question
        entry["ground_truth"]["text"] = ground_truth_text
        entry["question_difficulty"] = question_difficulty.value

        # Only update pandas_objects_json if explicitly provided
        if pandas_objects_json is not None:
            entry["ground_truth"]["pandas_objects_json"] = pandas_objects_json
        # Update comparison config if provided
        if pandas_comparison_config is not None:
            entry["pandas_comparison_config"] = pandas_comparison_config.model_dump()

    def _create_new_entry(
        self,
        question_id: str,
        research_question: str,
        ground_truth_text: str | None,
        pandas_objects_json: Optional[List[Dict[str, Any]]] = None,
        question_difficulty: QuestionDifficulty = QuestionDifficulty.HARD,
        pandas_comparison_config: PandasComparisonConfig | None = None,
    ) -> Dict[str, Any]:
        """Helper to create a new entry dictionary."""
        if pandas_comparison_config is None:
            pandas_comparison_config = PandasComparisonConfig(
                mode=PandasComparisonMode.EXACT_MATCH
            )

        return {
            "research_question": research_question,
            "question_difficulty": question_difficulty.value,
            "metadata": {
                "question_id": question_id,
            },
            "ground_truth": {
                "text": ground_truth_text,
                "pandas_objects_json": pandas_objects_json,
            },
            "pandas_comparison_config": pandas_comparison_config.model_dump(),
        }

    def add_entry(
        self,
        research_question: str,
        question_id: str,
        ground_truth_text: str | None,
        pandas_objects: List[pd.DataFrame | pd.Series] | None = None,
        question_difficulty: QuestionDifficulty = QuestionDifficulty.HARD,
        pandas_comparison_config: PandasComparisonConfig | None = None,
    ) -> None:
        """
        Adds or updates an entry in the golden dataset (upsert).
        If an entry with the given question_id exists, it will be updated.
        Otherwise, a new entry will be added.
        Args:
            research_question: The question asked to the agent.
            question_id: A unique identifier for the question.
            ground_truth_text: The expected textual answer from the agent (None to skip text evaluation).
            pandas_objects: A list of pandas DataFrames or Series objects.
            question_difficulty: Difficulty of the example.
        """
        pandas_objects_as_json: Optional[List[Dict[str, Any]]] = None
        if pandas_objects is not None:
            pandas_objects_as_json = []
            for pandas_object in pandas_objects:
                if isinstance(pandas_object, (pd.DataFrame, pd.Series)):
                    pandas_objects_as_json.append(
                        serialize_pandas_object_to_json(pandas_object)
                    )
                else:
                    raise TypeError(
                        f"Only pandas DataFrame and Series objects are supported. Got: {type(pandas_object)}"
                    )

        dataset = self._read_dataset()
        entries_map = {
            entry["metadata"]["question_id"]: entry
            for entry in dataset["evaluation_entries"]
        }

        existing_entry = entries_map.get(question_id)

        if existing_entry:
            logger.info(f"Updating existing entry with question_id '{question_id}'.")
            self._update_entry_data(
                entry=existing_entry,
                research_question=research_question,
                ground_truth_text=ground_truth_text,
                pandas_objects_json=pandas_objects_as_json,
                question_difficulty=question_difficulty,
                pandas_comparison_config=pandas_comparison_config,
            )
        else:
            logger.info(f"Adding new entry with question_id '{question_id}'.")
            new_entry = self._create_new_entry(
                question_id=question_id,
                research_question=research_question,
                ground_truth_text=ground_truth_text,
                pandas_objects_json=pandas_objects_as_json
                if pandas_objects_as_json is not None
                else [],
                question_difficulty=question_difficulty,
                pandas_comparison_config=pandas_comparison_config,
            )
            dataset["evaluation_entries"].append(new_entry)

        # Sort entries by question_id alphabetically
        dataset["evaluation_entries"].sort(key=lambda x: x["metadata"]["question_id"])

        dataset["total_questions"] = len(dataset["evaluation_entries"])
        dataset["generated_at"] = datetime.now().isoformat()

        self._write_dataset(dataset)
        logger.info(f"Successfully saved entry for question_id '{question_id}'.")

    def load_entry(self, question_id: str) -> Optional[Dict[str, Any]]:
        """
        Loads a specific entry from the golden dataset by its question_id.

        Args:
            question_id: The unique identifier of the question to load.

        Returns:
            A dictionary containing the entry's data ('research_question',
            'ground_truth_text', 'pandas_objects_json') or None if not found.
        """
        dataset = self._read_dataset()
        for entry in dataset["evaluation_entries"]:
            if entry["metadata"]["question_id"] == question_id:
                return {
                    "question_id": entry["metadata"]["question_id"],
                    "research_question": entry["research_question"],
                    "ground_truth_text": entry["ground_truth"]["text"],
                    "pandas_objects_json": entry["ground_truth"]["pandas_objects_json"],
                }

        logger.error(f"No entry found with question_id '{question_id}'.")
        return None

    def clear_dataset(self) -> None:
        """
        Clears all entries from the golden dataset, resetting it to its default structure.
        """
        empty_dataset = {
            "generated_at": datetime.now().isoformat(),
            "total_questions": 0,
            "language": "en",
            "evaluation_entries": [],
        }
        self._write_dataset(empty_dataset)
        logger.info("Golden dataset cleared and reset to default structure.")


def main() -> None:
    """
    Command-line interface to manage the golden dataset.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Manage entries in the golden dataset."
    )
    parser.add_argument(
        "--clear", action="store_true", help="Clear all entries from the dataset."
    )
    parser.add_argument("--question", help="The research question.")
    parser.add_argument("--id", help="A unique question ID.")
    parser.add_argument("--text", help="The ground truth text for the answer.")
    parser.add_argument(
        "--pandas_objects", help="A JSON string representing a list of pandas_objects."
    )
    parser.add_argument(
        "--question_difficulty",
        choices=[d.value for d in QuestionDifficulty],
        default=QuestionDifficulty.HARD.value,
        help="Difficulty of the question: Easy or Hard",
    )

    args = parser.parse_args()

    manager = GoldenDatasetManager()

    if args.clear:
        manager.clear_dataset()
        return

    pandas_objects_list = None
    if args.pandas_objects:
        try:
            pandas_objects_list = json.loads(args.pandas_objects)
        except json.JSONDecodeError:
            logger.error("--pandas_objects argument is not a valid JSON string.")
            return

    manager.add_entry(
        research_question=args.question,
        question_id=args.id,
        ground_truth_text=args.text,
        pandas_objects=pandas_objects_list,
        question_difficulty=QuestionDifficulty(args.question_difficulty),
    )


if __name__ == "__main__":
    main()
