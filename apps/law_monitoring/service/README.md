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

## Run tests

```shell
uv run pytest -s tests
```

## Start the Service Locally

Ensure the environment variables listed in the [.env.sample](.env.sample) file are set.
Note: The environment variables must be prefixed with `SERVICE_` to ensure only those required by the service get injected into the container on deployment.

```shell
uv run dev
```

## PostgreSQL Setup

Start PostgreSQL with Docker Compose:
   ```shell
   docker-compose up -d postgres
   ```

## Testing the API

Once the service is running locally (on port 8080), you can test the endpoints using curl or any HTTP client.

### Health Check

Test that the service is running:

```shell
curl -X GET "http://localhost:8080/health"
```

**Expected Response:**
```json
{
  "status": "ok"
}
```

## Legal Acts Search

Search for legal acts published within a specific date range:

```shell
curl -X GET "http://localhost:8080/legal-acts/search?start_date=2025-05-28&end_date=2025-05-28&limit=3" -H "Content-Type: application/json"
```

**Parameters:**
- `start_date`: Start date for the search (YYYY-MM-DD format)
- `end_date`: End date for the search (YYYY-MM-DD format)
- `limit`: Maximum number of results per day (optional, defaults to 1000, range 1-10000)

**Expected Response:**
```json
{
  "legal_acts": [
    {
      "date": "2025-05-28T00:00:00",
      "expression_url": "http://publications.europa.eu/resource/oj/C_202503125",
      "title": "Non-opposition to a notified concentration (Case M.11760 – DAIMLER TRUCK / VOLVO / JV)",
      "pdf_url": "http://publications.europa.eu/resource/cellar/0c469e40-3b5c-11f0-8a44-01aa75ed71a1.0006.01/DOC_1"
    },
    {
      "date": "2025-05-28T00:00:00",
      "expression_url": "http://publications.europa.eu/resource/oj/L_202501107",
      "title": "Council Decision (CFSP) 2025/1107 of 27 May 2025 amending and updating Decision (CFSP) 2018/340 establishing the list of projects to be developed under PESCO",
      "pdf_url": "http://publications.europa.eu/resource/cellar/0e422022-3b5c-11f0-8a44-01aa75ed71a1.0006.01/DOC_1"
    },
    {
      "date": "2025-05-28T00:00:00",
      "expression_url": "http://publications.europa.eu/resource/oj/C_202503132",
      "title": "Notice for the attention of persons and entities subject to the restrictive measures provided for in Council Decision 2013/255/CFSP, as amended by Council Decision (CFSP) 2025/1096 and as implemented by Council implementing Decision (CFSP) 2025/1095 and in Council Regulation (EU) No 36/2012 as amended by Council Regulation (EU) 2025/1098, and implemented by Council implementing Regulation (EU) 2025/1094 concerning restrictive measures in view of the situation in Syria",
      "pdf_url": "http://publications.europa.eu/resource/cellar/0d120491-3b5c-11f0-8a44-01aa75ed71a1.0006.01/DOC_1"
    },
  ],
  "total_count": 3,
  "start_date": "2025-05-28T00:00:00",
  "end_date": "2025-05-28T00:00:00"
}
```

**Response Fields:**
- `legal_acts`: Array of legal act objects
- `total_count`: Total number of legal acts found
- `start_date`: Start date of the search range
- `end_date`: End date of the search range

Each legal act object contains:
- `date`: Publication date
- `expression_url`: EUR-Lex reference URL
- `title`: Title of the legal act
- `pdf_url`: Direct link to the PDF document

### Alternative POST Endpoint

You can also use the POST version of the search endpoint:

```shell
curl -X POST "http://localhost:8080/legal-acts/search" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2023-12-01T00:00:00",
    "end_date": "2023-12-01T00:00:00",
    "limit": 5
  }'
```

This endpoint accepts the same parameters in the request body and returns the same response format.

## Database Integration

We use a PostgreSQL database for persisting law data. In deployment, we access the PhariaAssistant database.
Before you can deploy the application to a PhariaAI instance, the `pharia-assistant-postgresql-secret` needs to be
injected to the usecase. For documentation on how this works, we refer to the [PhariaOS docs](https://docs.aleph-alpha.com/products/pharia-ai/pharia-os/application-management/how-to-inject-secrets-to-applications/).

For the `c-prod` cluster, the configuration for the Assistant postgres secret is available in
[this file](https://gitlab.aleph-alpha.de/product-infra-platform-customer/c-prod-deployment/-/blob/main/applications/multicluster-config/values.yaml?ref_type=heads).

During deployment, the secret is then injected via the `secretEnvVars` field in the `config`.


## Default Company Configuration

The `default_company_config.py` file provides company description and team configurations to ensure system functionality when no custom configuration is available.

> **Important:** When modifying this file, cached versions in the PostgreSQL database must be updated/deleted for changes to take effect.

## Database Migrations (Alembic)

This project uses **Alembic** for database schema migrations. Migrations are automatically applied on app startup.

### Creating New Migrations
After changing or adding data models:

```bash
alembic revision --autogenerate -m "Describe your change"
# Review & edit the generated script
alembic upgrade head  # or restart the app
```

### Manual Migration Commands
Apply all pending migrations:
```bash
alembic upgrade head
```

Rollback to previous revision:
```bash
alembic downgrade -1
```

> **Note:** Always review auto-generated migration scripts before committing, as Alembic may not detect all changes correctly.