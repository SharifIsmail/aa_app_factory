# Supplier Briefing Evaluation System


## Creating the Evaluation Dataset

```bash
uv run generate_golden_dataset
```

- We derive our evaluation samples from [Lidl's Word file](https://aleph-alpha.atlassian.net/wiki/spaces/Customer/pages/1656881735/Example+Requests+Responses) containing example requests and answers
- To create the samples we write scripts in `golden_dataset_creation/` to create `golden_dataset.json`
- Each file contains one or multiple function, where each function creates a sample. The files then export a function that will call all the sample functions in the file.
- `main.py` calls all the exported functions to create the full `golden_dataset.json`.
- Each sample includes:
  - Question
  - Unique ID format: `<file_name>__X_X_<question_id>`
  - Expected dataframe outputs
  - Textual answer (or None to skip text evaluation)


## Running the Benchmark

```bash
# Convert and upload to PhariaStudio (defaults to golden dataset if no args)
uv run create_dataset

# Option A: Run benchmark using dataset ID
uv run run_benchmark <dataset_id>

# Option B: If you registered with label 'golden', retrieve ID then run
uv run run_benchmark  # defaults to using the 'golden' dataset from the registry
```

- **conversion**: Convert `golden_dataset.json` and upload using `dataset_creator`
- **run**: Execute the benchmark using `run_benchmark`
- **view**: See results in the Evaluate tab of PhariaStudio


