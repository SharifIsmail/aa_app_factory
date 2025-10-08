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

## Run linter and type checker
```shell
./lint.sh
```

## Start the Service Locally

Ensure the environment variables listed in the [.env](.env) file are set.
Note: The environment variables must be prefixed with `SERVICE_` to ensure only those required by the service get injected into the container on deployment.

```shell
uv run dev
```



## Supplier Analysis API Endpoints Documentation

### Health Check
Endpoint: GET /health
Description: Checks the health status of the service
Response: Returns a HealthResponse with status "ok"
Authentication: Not required

### Company Data Search
Endpoint: POST /company-data-search
Description: Initiates a company data search process
Authentication: Required
Request Body:
company_name (required): Name of the company to search
country_id (required): Country identifier
research_type (optional): Type of research (defaults to "comprehensive")
Response: Returns execution ID and status

### Company Data Search Status
Endpoint: GET /company-data-search-status/{uuid}
Description: Checks the status of a company data search
Authentication: Required
Path Parameters:
uuid: The execution ID of the search
Response: Returns search status, tasks, tool logs, and extracted data

### Stop Company Data Search
Endpoint: DELETE /company-data-search/{uuid}
Description: Stops an ongoing company data search
Authentication: Required
Path Parameters:
uuid: The execution ID of the search
Response: Returns status and UUID

### Get Company Report
Endpoint: GET /company-data-search/{uuid}/report/{report_type}
Description: Retrieves a company report
Authentication: Required
Path Parameters:
uuid: The execution ID of the search
report_type: Type of report ("data" or "risks")
Query Parameters:
download (optional): Boolean to trigger file download
Response: Returns HTML report or file download

### Get Companies List
Endpoint: GET /companies
Description: Retrieves a list of all previously processed companies
Authentication: Required
Response: Returns list of companies with their UUIDs, names, and report availability

### Company Risks Research
Endpoint: POST /company-risks-research
Description: Initiates company risks research
Authentication: Required
Request Body:
company_name (required): Name of the company to research
research_type (optional): Type of research (defaults to "comprehensive")
Response: Returns execution ID and status

### Company Risks Research Status
Endpoint: GET /company-risks-research-status/{uuid}
Description: Checks the status of a company risks research
Authentication: Required
Path Parameters:
uuid: The execution ID of the research
Response: Returns research status, tasks, tool logs, and extracted data

### Stop Company Risks Research
Endpoint: DELETE /company-risks-research/{uuid}
Description: Stops an ongoing company risks research
Authentication: Required
Path Parameters:
uuid: The execution ID of the research
Response: Returns status and UUID

### Get Risk Report
Endpoint: GET /company-risks-research/{uuid}/report
Description: Retrieves a risk report
Authentication: Required
Path Parameters:
uuid: The execution ID of the research
Query Parameters:
download (optional): Boolean to trigger file download
Response: Returns HTML report or file download

### Metrics
Endpoint: GET /metrics
Description: Exposes Prometheus metrics for monitoring
Authentication: Not required
Response: Returns Prometheus metrics data
Additional Notes:
All endpoints that require authentication use the access_permission dependency
The service runs on port 8080 by default
CORS is enabled if configured in settings
The service requires several environment variables:
SERVICE_AUTHENTICATION_TOKEN
SERVICE_INFERENCE_API_URL
SERPER_API_KEY
ABSTRACT_API_KEY