# Intelligence Layer Law Relevancy Evaluation

This module provides automated evaluation of law relevancy classification using the Intelligence Layer SDK and Studio integration. It evaluates how well the system can determine which teams within a company are relevant for specific laws.

## Overview

The evaluation system:
- Uses Intelligence Layer's Task framework for standardized evaluation
- Calculates precision, recall, and F1 scores for each team
- Supports both overall and team-specific metrics
- Integrates with Intelligence Layer Studio for automated benchmarking
- Uses consolidated dataset management through `LawRelevancyDatasetCreator`

## Key Features

### Metrics
- **Precision**: How many of the predicted relevant teams were actually relevant
- **Recall**: How many of the actually relevant teams were predicted as relevant
- **F1 Score**: Harmonic mean of precision and recall
- **Overall Metrics**: Aggregated across all teams
- **Team-Specific Metrics**: Individual performance for each team

## Architecture

### Core Components

1. **`LawRelevancyDatasetCreator`**: Dataset management for Intelligence Layer
   - `_load_labeled_samples()`: Loads samples from JSON files
   - `create_dataset()`: Creates Intelligence Layer datasets

2. **`LawRelevancyTask`**: Intelligence Layer task implementation
   - Uses the same `LawReportService` as production
   - Returns `List[TeamRelevancy]` for team-level evaluation
   - Generates unique IDs for work log management

3. **`LawRelevancyEvaluationLogic`**: Individual example evaluation
   - Compares predicted vs ground truth team relevancy
   - Calculates team-level metrics

4. **`LawRelevancyAggregationLogic`**: Results aggregation
   - Combines individual results into overall metrics
   - Generates confusion matrices and performance statistics

5. **`run_studio_benchmark()`**: Studio integration
   - Creates and executes benchmarks in Intelligence Layer Studio
   - Handles authentication and project management

## Usage

### Prerequisites

1. **Set up environment variables**:
SERVICE_AUTHENTICATION_TOKEN="your_authentication_token_here"

2. **Ensure labeled dataset exists**:
   ```
   labeled_eval_dataset/
   ├── sample_1.json
   ├── sample_2.json
   └── ...
   ```

### Dataset Creation

Create Intelligence Layer datasets (local and Studio):

```bash
# Create datasets
python law_relevancy_dataset_creator.py
```

This will:
- Create a local dataset in `evaluation_data/`
- Create a Studio dataset (if `SERVICE_AUTHENTICATION_TOKEN` is set in .env)
- Display the dataset ID for use in benchmarks

### Running Benchmarks

Execute benchmarks in Intelligence Layer Studio:

```bash
# Basic benchmark
python run_law_relevancy_benchmark.py <dataset_id>

# With custom benchmark name
python run_law_relevancy_benchmark.py <dataset_id> --benchmark-name "My Custom Benchmark"
```

### Example Workflow

```bash
# 1. Create datasets
python law_relevancy_dataset_creator.py
# Output: Created Studio dataset with ID: abc123-def456-ghi789

# 2. Run benchmark
python run_law_relevancy_benchmark.py abc123-def456-ghi789 --benchmark-name "Law Relevancy Test"
# Output: Successfully completed law relevancy benchmark with run ID: xyz789-abc123-def456
```

## Configuration

Configuration is managed in `eval_config.py`:

```python
# Dataset configuration
DATASET_NAME = "law_relevancy_dataset"

# Studio configuration
STUDIO_PROJECT = "law-monitoring-evaluation"


# Paths
LABELED_DATASET_DIR = BASE_DIR / "evaluation" / "labeled_eval_dataset"
EVALUATION_DATA_DIR = BASE_DIR / "evaluation" / "intelligence_layer_eval" / "evaluation_data"
```

## Dataset Format

Each sample in the labeled dataset should be a JSON file with:

```json
{
  "law_text": "Full text of the law...",
  "metadata": {
    "title": "Commission Implementing Regulation (EU) 2025/96...",
    "expression_url": "http://publications.europa.eu/resource/cellar/...",
    "pdf_url": "http://publications.europa.eu/resource/cellar/...",
    "publication_date": "2025-01-22T00:00:00",
    "document_date": "2025-01-21T00:00:00",
    "effect_date": "2025-02-11T00:00:00",
    "eurovoc_labels": ["grape", "market approval", "pesticide"]
  },
  "collection_info": {
    "collected_at": "2025-06-30T12:06:09.517597",
    "source_date": "2025-01-22T00:00:00",
    "act_id": "0dcc962e-d866-11ef-be2a-01aa75ed71a1"
  },
  "ground_truth": {
    "is_relevant": false,
    "original_title": "Commission Implementing Regulation (EU) 2025/96...",
    "reason": "Not in relevant titles list"
  }
}
```

**Note**: The current system uses overall relevancy (true/false) rather than team-specific ground truth. The `LawRelevancyTask` will evaluate relevancy for all teams based on the law content, but the ground truth only indicates whether the law is relevant overall.

## Integration with Law Monitoring System

This evaluation system integrates with the main law monitoring system:

- Uses the same `LawReportService` for consistency
- Leverages the same `TeamRelevancy` model
- Maintains compatibility with the production classification logic
- Provides insights for system improvement

## Troubleshooting

### Common Issues

1. **SERVICE_AUTHENTICATION_TOKEN not set**: Ensure `SERVICE_AUTHENTICATION_TOKEN="your_token"` is added to your `.env` file
2. **Dataset not found**: Verify the labeled dataset directory exists
3. **Import errors**: Ensure the service path is correctly set in the scripts
4. **Benchmark name conflicts**: Use unique benchmark names or let the system generate them

### Debug Mode

Enable debug logging by modifying the logging level in the scripts:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

1. **Detailed Team-Level Ground Truth**: Support for granular team-specific relevancy labels
2. **Confidence Scoring**: Evaluate prediction confidence levels
3. **Cross-Validation**: Support for k-fold cross-validation
4. **A/B Testing**: Compare different classification approaches
5. **Real-time Evaluation**: Continuous evaluation during production use

## Contributing

When adding new evaluation features:

1. Update the `LawRelevancyTask` if needed
2. Modify the evaluation logic in `evaluate_law_relevancy()`
3. Update the dataset loading methods in `LawRelevancyDatasetCreator` if format changes
4. Add new configuration options to `eval_config.py`
5. Update this README with new features 