# Service

## Install uv

```shell
pipx install uv
```

## Set Python Version
See [pyproject.toml](pyproject.toml) for the Python version. You can use pyenv to set the local Python version. More info: [https://github.com/pyenv/pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation)

## Install Dependencies

```shell
uv sync --dev
```

## Data Preparation

We use Pharia Data to store the raw Excel files for the application.

### Upload Excel files to Pharia Data

1. Place your Excel files (`brutto_file.xlsx`, `concrete_file.xlsx`, `resource_risks.xlsx`) in the `service/data` directory. Get the files from [here](https://alephalphahd.sharepoint.com/:f:/r/sites/Market/Shared%20Documents/Aleph%20Alpha%20Market/05%20Team%20Customer/20%20Retail/01.%20Schwarz%20Group/03.%20Projects%20%26%20CS%20Initiatives/3.47%20Compliance/01.%20Supplier%20Risk%20Analysis/data?csf=1&web=1&e=uAfdk0).
2. Upload them to Pharia Data
   ```shell
   uv run src/service/upload_raw_data.py
   ```

### Download Excel files from Pharia Data and run the preprocessing

```shell
uv run src/service/download_and_preprocess_data.py
```


## Run linter and type checker
```shell
./lint.sh
```

## Run tests
```shell
uv run pytest tests
```

## Start the Service Locally

Ensure the environment variables listed in the [.env](.env) file are set.
Note: The environment variables must be prefixed with `SERVICE_` to ensure only those required by the service get injected into the container on deployment.

```shell
uv run dev
```

## Debugging agent runs


To see traces in Studio set the following environment variables in your `.env` file:
```
SERVICE_AGENT_TELEMETRY=pharia_studio
SERVICE_STUDIO_URL=https://pharia-studio.customer.pharia.com/
SERVICE_STUDIO_PROJECT_NAME=supplier-briefing
```

### OTEL/Phoenix Alternative

Smolagents comes with [telemetry functionality](https://huggingface.co/docs/smolagents/en/tutorials/inspect_runs). In order to save and inspect the traces, run
```shell
uv run python -m phoenix.server.main serve
```
and set the environment variable 
```
SERVICE_AGENT_TELEMETRY=phoenix
```
