# External Legal Act Provider Specification

This document defines the contract for supplying additional legal sources to the Law Monitoring application. It covers both the Python integration point and the HTTP surface that serves the full-text content.

## 1. Python Module Interface

Provide a Python module (for example `external_sources/my_provider.py`) that exposes the following items:

### 1.1 Public API

```python
from datetime import datetime
from typing import Iterable

from service.models import LegalAct

SOURCE_ID: str

def fetch_legal_acts(
    start_date: datetime,
    end_date: datetime,
    limit: int = 1000,
) -> Iterable[LegalAct]:
    ...
```

- `SOURCE_ID`: short identifier for logging/metrics (e.g. `"my_provider"`).
- `fetch_legal_acts`:
  - Returns an iterable (e.g. `list[LegalAct]`) of `LegalAct` objects populated with the mandatory metadata (`title`, `expression_url`, dates, Eurovoc labels when available, `pdf_url`, etc.).
  - Must accept `limit` but may ignore it if not applicable.
  - Must raise a descriptive exception (not return partial items) on failure.
  - Must ensure every `LegalAct.expression_url` is unique and deterministic so hashing remains stable.

### 1.2 Behavioural Notes

- The module **must not** mutate global state in the service.
- Network access, authentication, and throttling are handled inside the module.
- The iterable must be finite; avoid lazy generators that rely on open network cursors after the call returns.

## 2. HTTP Content Endpoint

Each `LegalAct.expression_url` returned by `fetch_legal_acts` must resolve to an HTTP GET endpoint that provides the full text of the act.

### 2.1 Requirements

- Responds with HTTP status code `200`.
- `Content-Type` header includes `text/html`.
- The body contains a single `<article data-law-monitoring="legal-act">` element whose textual content is the canonical law text.
- Optional metadata attributes:
  - `data-expression-url="<same value as LegalAct.expression_url>"`.
  - `data-source-id="<SOURCE_ID>"`.
- No authentication challenge or client-side rendering (content must be present in the initial response).

### 2.2 Minimal HTML Example

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Regulation (EU) 2025/123</title>
  </head>
  <body>
    <article
      data-law-monitoring="legal-act"
      data-expression-url="https://provider.example/acts/2025-123"
      data-source-id="my_provider"
    >
      <h1>Regulation (EU) 2025/123</h1>
      <section>
        The European Parliament and the Council of the European Union, Having regard to the Treaty...
      </section>
    </article>
  </body>
</html>
```

### 2.3 Optional PDF Link

- The `LegalAct.pdf_url` must point to a stable, downloadable PDF (if available).
- If the original source lacks a PDF, set `pdf_url` to an empty string.

## 3. Configuration Hand-off

Provide the following deployment artefacts alongside your module:

1. Import path to the provider module (e.g. `"external_sources.my_provider"`).
2. Environment variables or secrets required by the module, with descriptions.
3. Sample `expression_url` and `pdf_url` values for smoke testing.
4. Expected rate limits or scheduling constraints (if any).

## 4. Error Reporting Expectations

- Log or raise errors with enough context to identify the failing upstream endpoint.
- Include `SOURCE_ID` in exceptions/log messages to simplify troubleshooting.

