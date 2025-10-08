# Multi-Source Ingestion Plan

## Goals
- Add new legal data providers without refactoring downstream processing.
- Preserve the existing `LegalAct` contract so reporting, classification, and UI continue to function unchanged.

## Strategy

1. **Encapsulate Providers**
   - Define a lightweight `LegalActProvider` protocol that exposes `get_legal_acts(start_date, end_date, limit) -> Iterable[LegalAct]`.
   - Implement adapters for each new source (REST API client, CSV/Excel loader, custom crawler, etc.) that normalize their output into `LegalAct` instances or compatible dictionaries.

2. **Extend Discovery Worker**
   - Update `DiscoveryWorker` to accept a list of providers (in addition to the existing EUR-Lex service).
   - After fetching from EUR-Lex, iterate through each provider and extend the result list with their `LegalAct`s.
   - Continue to persist acts using `legalact_to_law`, preserving hashing based on `expression_url`.
   - Drive provider enablement via configuration/ENV so deployments can toggle sources without code edits.

3. **Handle Full Text Fetching**
   - Prefer sources that expose an HTML page and set `expression_url` to that page so `SummaryWorker` can reuse `VisitWebpageUserAgentTool`.
   - If a source cannot provide fetchable HTML, allow providers to optionally supply `law_text`; short-circuit the fetch in `SummaryWorker` when pre-fetched text exists, storing it directly with `mark_processed`.
   - Require providers to supply a stable `expression_url` (or surrogate) so IDs and reconciliation remain deterministic.

4. **Reuse Downstream Pipeline**
   - Leave `LawReportService`, relevancy classification, reporting, and UI untouched; they operate on stored laws and the generated full text.
   - Ensure metadata fields (`title`, dates, Eurovoc labels, `pdf_url`) are filled to keep reports and user actions consistent.

5. **Configuration & Monitoring**
   - Document provider-specific settings (API keys, base URLs, file paths) and surface them in existing settings modules.
   - Add logging/metrics tags per provider so reconciliation and monitoring dashboards can differentiate sources.

## Optional Enhancements
- Introduce validation tests that instantiate each provider and confirm it yields well-formed `LegalAct`s.
- Add a dry-run CLI to import sample data from new providers without writing to the database.

