#!/usr/bin/env python3
"""
Dataset registry for tracking Studio dataset IDs.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from evaluation.intelligence_layer_eval.eval_config import EVALUATION_DATA_DIR


class DatasetRegistry:
    """Tracks Studio dataset IDs for different dataset labels."""

    def __init__(self, registry_path: Optional[Path] = None):
        if registry_path is None:
            registry_path = EVALUATION_DATA_DIR / "studio_dataset_registry.json"
        self.registry_path = registry_path
        self._load_registry()

    def _load_registry(self) -> None:
        """Load registry from file."""
        if self.registry_path.exists():
            with open(self.registry_path, "r") as f:
                self.registry = json.load(f)
        else:
            self.registry = {}

    def _save_registry(self) -> None:
        """Save registry to file."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w") as f:
            json.dump(self.registry, f, indent=2)

    def register_dataset(self, label: str, studio_id: str) -> None:
        """Register a dataset with its Studio ID."""
        self.registry[label] = studio_id
        self._save_registry()

    def get_studio_id(self, label: str) -> Optional[str]:
        """Get Studio dataset ID for a label."""
        dataset_id = self.registry.get(label)
        return dataset_id


def main() -> None:
    """CLI for querying the registry (Studio IDs only)."""
    parser = argparse.ArgumentParser(description="Query dataset registry")
    parser.add_argument("label", help="Dataset label (e.g., 'golden')")

    args = parser.parse_args()

    registry = DatasetRegistry()
    dataset_id = registry.get_studio_id(args.label)

    if dataset_id:
        print(dataset_id)
    else:
        print(f"No dataset found for label '{args.label}'", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
