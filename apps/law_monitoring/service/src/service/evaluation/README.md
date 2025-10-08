# Law Monitoring Evaluation Pipeline

This directory contains evaluation pipelines for the law monitoring system, organized into logical components for easy navigation and maintenance.

## 📁 Directory Structure

```
evaluation/
├── README.md                    # This file
├── data_collection/             # Data collection from EUR-Lex
│   └── eval_dataset_collector.py
├── ground_truth_labeling/       # Ground truth labeling tools
│   ├── add_ground_truth_labels.py
│   └── extract_titles_to_text.py
├── evaluation/                  # Manual evaluation scripts
│   └── eval_with_ground_truth.py
├── intelligence_layer_eval/     # Intelligence Layer SDK evaluation
│   ├── README.md               # Intelligence Layer evaluation documentation
│   ├── eval_config.py          # Configuration settings
│   ├── law_relevancy_task.py   # Main evaluation task
│   ├── law_relevancy_eval_logic.py # Evaluation logic
│   ├── law_relevancy_dataset_creator.py # Dataset creation
│   ├── studio_benchmark_runner.py # Studio integration
│   └── run_law_relevancy_benchmark.py # Main execution script
├── config/                      # Configuration files
│   └── all_titles.txt
├── results/                     # Evaluation results
│   └── evaluation_results.json
└── labeled_eval_dataset/        # Labeled evaluation datasets
```

## 🚀 Evaluation Options

This evaluation system provides two complementary evaluation approaches:

### 1. Manual Evaluation Pipeline
A traditional evaluation pipeline for manual assessment and analysis.

### 2. Intelligence Layer SDK Evaluation
A modern evaluation framework using the Intelligence Layer SDK for automated benchmarking and Studio integration.

## 📋 Manual Pipeline

### Step 1: Data Collection
```bash
uv run data_collection/eval_dataset_collector.py \
    --output-dir eval_dataset \
    --dates 2025-01-22 2025-01-27 2025-02-14 2025-03-10 2025-03-31 2025-05-07 2025-05-28 2025-06-10

```
The dates used above are all the dates where relevant laws for our client were published (8 dates total: 514 laws collected, 513 successful fetches, 99.8% success rate).
It was a voluntary decision to restrict to those dates instead of covering a continuous period as the dataset is already quite unbalanced (very few laws are relevant).

**Example Collection Results:**
- **Input**: 8 specific dates with known relevant law publications
- **Output**: 484 evaluation samples processed (after filtering out summary files)
- **Ground Truth**: 9 relevant matches found (1.9% relevance ratio)
- **Dataset Balance**: 9 positive samples, 475 negative samples

### Step 2: Ground Truth Labeling
Extract all titles for manual editing:
```bash
uv run ground_truth_labeling/extract_titles_to_text.py --dataset-dir eval_dataset --output-file config/all_titles.txt
```

Edit `all_titles.txt` to uncomment relevant titles (remove `#` prefix from relevant titles), then:
```bash
uv run ground_truth_labeling/add_ground_truth_labels.py \
    --relevant-titles-file config/all_titles.txt \
    --dataset-dir eval_dataset \
    --output-dir labeled_eval_dataset
```

### (Optional) Convert human annotations export (CSV) → all_titles.txt for feedback loop
Once users annotate relevance in the application UI, one can export an "All evaluated" CSV (Category ∈ {RELEVANT, NOT_RELEVANT}) and convert that CSV into the `all_titles.txt` format used by the manual pipeline. This enables a continuous feedback loop without retyping.

```bash
# Example: convert evaluated CSV to all_titles.txt
uv run python service/src/service/evaluation/csv_to_titles.py \
  --csv service/src/service/evaluation/config/evaluated_legal_acts_2025-09-03.csv \
  --out service/src/service/evaluation/config/all_titles.txt
```

Behavior:
- Appends to `all_titles.txt` if it exists, otherwise creates it
- De-duplicates titles already present (commented or not)
- Groups entries by "Publication Date" into dated sections
- Writes titles uncommented if `Category=RELEVANT`, commented with `#` otherwise

Use case:
- Incorporate human-labeled relevance into the manual labeling workflow, then proceed with `add_ground_truth_labels.py` as usual.

### Step 3: Run Evaluation
```bash
uv run evaluation/eval_with_ground_truth.py \
    --dataset-dir labeled_eval_dataset \
    --output-file results/evaluation_results.json
```

## 🧠 Intelligence Layer SDK Evaluation

For automated benchmarking and Studio integration, use the Intelligence Layer SDK evaluation system:

### Prerequisites

1. **Set up environment variables**:
   ```
   SERVICE_AUTHENTICATION_TOKEN="your_authentication_token_here"
   ```


### Quick Start
```bash
# 1. Create dataset from labeled evaluation data
uv run intelligence_layer_eval/law_relevancy_dataset_creator.py
# This will create both local and Studio datasets and display the dataset ID

# 2. Run Studio benchmark (replace with actual dataset ID from step 1)
uv run intelligence_layer_eval/run_law_relevancy_benchmark.py <dataset_id> --benchmark-name "Law Relevancy Test"
```

### Complete Workflow Example
```bash
# 1. Create datasets
uv run intelligence_layer_eval/law_relevancy_dataset_creator.py
# Output: Created Studio dataset with ID: abc123-def456

# 2. Run benchmark with the returned dataset ID
uv run intelligence_layer_eval/run_law_relevancy_benchmark.py abc123-def456 --benchmark-name "Law Relevancy Test"
# Output: Successfully completed law relevancy benchmark with run ID: xyz789-abc123-def456
```

For detailed documentation, see [Intelligence Layer Evaluation README](intelligence_layer_eval/README.md).

## 📋 Component Details

### Data Collection (`data_collection/`)
- **Purpose**: Collect law data from EUR-Lex for specific dates
- **Main Script**: `eval_dataset_collector.py`
- **Output**: Raw law data in JSON format with metadata

### Ground Truth Labeling (`ground_truth_labeling/`)
- **Purpose**: Add ground truth labels to collected data
- **Scripts**:
  - `add_ground_truth_labels.py`: Main labeling script
  - `extract_titles_to_text.py`: Extract titles for manual editing (all commented out by default)
- **Input**: Text file with relevant titles (uncommented lines, one per line)
- **Output**: Labeled datasets with ground truth information

### Manual Evaluation (`evaluation/`)
- **Purpose**: Evaluate system performance against ground truth
- **Main Script**: `eval_with_ground_truth.py`
- **Metrics**: Precision, recall, F1-score, accuracy, confidence analysis
- **Output**: Comprehensive evaluation results with detailed metrics

### Intelligence Layer Evaluation (`intelligence_layer_eval/`)
- **Purpose**: Automated benchmarking with Studio integration
- **Components**:
  - `LawRelevancyTask`: Main evaluation task implementation
  - `LawRelevancyEvaluationLogic`: Individual example evaluation logic
  - `LawRelevancyAggregationLogic`: Results aggregation and metrics calculation
  - `LawRelevancyDatasetCreator`: Dataset creation for Intelligence Layer
  - `run_studio_benchmark()`: Studio benchmark execution function
- **Features**: Automated dataset creation, Studio integration, comprehensive metrics
- **Workflow**: Create datasets → Run benchmarks → View results in Studio

### Configuration (`config/`)
- **Purpose**: Configuration files and templates
- **Files**:
  - `all_titles.txt`: All law titles extracted from dataset

### Results (`results/`)
- **Purpose**: Store evaluation results and outputs
- **Files**: JSON files with evaluation metrics and detailed results

## 🔧 Configuration

### Environment Variables
Ensure `SERVICE_AUTHENTICATION_TOKEN="your_token"` is added to your `.env` file.

### Company Configuration
The evaluation uses your company configuration for context-aware assessment. The configuration is stored in two ways:

1. **File Storage**: `/tmp/law_monitoring_data_storage/config/company.json` (FilesystemStorageBackend)
2. **API Access**: Available via FastAPI endpoint (when service is running)

To check your current company configuration:
```bash
# If the service is running (default port 8000)
curl -X GET "http://localhost:8000/company-config"

# Or check the file directly
cat /tmp/law_monitoring_data_storage/config/company.json
```

**Note**: The evaluation script automatically retrieves the company configuration from the LawReportService, so you don't need to manually check it unless troubleshooting.

## 📊 Evaluation Metrics

Both evaluation approaches provide comprehensive evaluation metrics:

### Basic Metrics
- **Accuracy**: Overall correct predictions
- **Precision**: True positives / (True positives + False positives)
- **Recall**: True positives / (True positives + False negatives)
- **F1-Score**: Harmonic mean of precision and recall

### Advanced Metrics
- **Confidence Analysis**: Average, min, max confidence scores
- **Team Relevancy Statistics**: Per-team assessment analysis
- **Relevance Distribution**: Ground truth vs predicted distribution

### Confusion Matrix
```
                Predicted
Actual    Relevant  Not Relevant
Relevant     TP         FN
Not Rel.     FP         TN
```

## 📈 Results Analysis

### Manual Evaluation Results
```bash
# View summary metrics
cat evaluation/results/evaluation_results.json | jq '.metrics'

# View confusion matrix
cat evaluation/results/evaluation_results.json | jq '.confusion_matrix'

# View individual sample results
cat evaluation/results/evaluation_results.json | jq '.evaluation_results[0]'
```

### Intelligence Layer Results
Results are available in Pharia Studio. After running a benchmark:

1. **Studio**: View detailed results, metrics, and individual example evaluations
2. **Local Files**: Check `intelligence_layer_eval/evaluation_data/` for local dataset files
3. **Run IDs**: Use the returned run ID to access specific benchmark results in Studio

### Key Insights
- **Performance**: Overall system accuracy and reliability
- **Team Analysis**: How well the system identifies relevant laws for each team
- **Confidence**: Reliability of the system's predictions
- **Error Analysis**: Understanding false positives and false negatives

## 🛠️ Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   # Ensure service path is in Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/service/src"
   ```

2. **Missing Dependencies**:
   ```bash
   cd service
   uv sync
   ```

3. **Company Configuration Missing**:
   ```bash
   # Check if company config exists
   curl -X GET "http://localhost:8000/company-config"
   ```

4. **Intelligence Layer Issues**:
   ```bash
   # Check Intelligence Layer installation
   pip install pharia-inference-sdk pharia-studio-sdk
   
   # Verify Studio token
   echo $SERVICE_AUTHENTICATION_TOKEN
   
   # Check dataset creation
   uv run law_relevancy_dataset_creator.py
   ```

## 📝 Example Workflows

### Complete Manual Pipeline
```bash
# Complete manual pipeline example
cd evaluation

# 1. Collect data for all relevant dates
uv run data_collection/eval_dataset_collector.py \
    --output-dir eval_dataset \
    --dates 2025-01-22 2025-01-27 2025-02-14 2025-03-10 2025-03-31 2025-05-07 2025-05-28 2025-06-10

# 2. Extract titles for manual review
uv run ground_truth_labeling/extract_titles_to_text.py --dataset-dir eval_dataset --output-file config/all_titles.txt

# 3. Manually edit all_titles.txt to mark relevant titles (remove # prefix from relevant ones)
# Then run labeling
uv run ground_truth_labeling/add_ground_truth_labels.py \
    --relevant-titles-file config/all_titles.txt \
    --dataset-dir eval_dataset \
    --output-dir labeled_eval_dataset

# 4. Run evaluation
uv run evaluation/eval_with_ground_truth.py \
    --dataset-dir labeled_eval_dataset \
    --output-file results/evaluation_results.json

# 5. View results
cat results/evaluation_results.json | jq '.metrics'
```

### Intelligence Layer Pipeline
```bash
# Intelligence Layer evaluation example
cd evaluation/intelligence_layer_eval

# 1. Create dataset from existing labeled data
uv run law_relevancy_dataset_creator.py
# Note the dataset ID from the output (e.g., abc123-def456-ghi789)

# 2. Run Studio benchmark with the dataset ID
uv run run_law_relevancy_benchmark.py abc123-def456 --benchmark-name "Law Relevancy Test"

# 3. View results in Studio using the returned run ID
# Or check local files
ls evaluation_data/
```

## 🔮 Future Enhancements

1. **Additional Metrics**: ROUGE, BLEU, or custom metrics for summarization quality
2. **Human Evaluation**: Integration with human annotation workflows
3. **Cross-validation**: K-fold cross-validation for model evaluation
4. **Comparative Analysis**: Compare different model configurations
5. **Visualization**: Add charts and graphs for evaluation results
6. **Automated Reporting**: Generate evaluation reports automatically
7. **Studio Integration**: Enhanced Studio dashboard and reporting
8. **Continuous Evaluation**: Automated evaluation pipelines

## 📚 Related Documentation

- [Main README](../../../README.md): Overview of the law monitoring system
- [Intelligence Layer Evaluation README](intelligence_layer_eval/README.md): Detailed Intelligence Layer SDK documentation
- [Service Documentation](../service/README.md): Backend service documentation

## 🤝 Contributing

To extend the evaluation pipeline:

1. **New Metrics**: Add new evaluation metrics to evaluation scripts
2. **New Data Sources**: Extend `eval_dataset_collector.py` for new data sources
3. **New Labeling Methods**: Add new labeling scripts to `ground_truth_labeling/`
4. **Intelligence Layer Extensions**: Add new tasks or evaluation logic to `intelligence_layer_eval/`
5. **New Scripts**: Add utility scripts to `scripts/`

Follow the existing patterns and ensure compatibility with the current pipeline structure. 