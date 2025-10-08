from pathlib import Path

# Base directories
IL_EVAL_DIR = Path(__file__).parent
EVAL_DIR = IL_EVAL_DIR.parent
SERVICE_DIR = EVAL_DIR.parent
DATA_DIR = EVAL_DIR / "data"

# Paths
CORE_DATA_DIR = DATA_DIR / "core"
EVALUATION_DATA_DIR = DATA_DIR / "intelligence_layer_eval"

# JSON dataset files
GOLDEN_DATASET_PATH = CORE_DATA_DIR / "golden_dataset.json"
