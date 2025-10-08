To bolt on more sources without disturbing the current stack, treat everything upstream of `LegalAct` as pluggable and leave the downstream pipeline alone.

**Keep The Ingestion Contract**
- The rest of the system only understands `LegalAct` metadata (title, expression_url, Eurovoc, dates, `pdf_url`). Whatever you ingest—API, CSV, your own crawler—normalize it into that Pydantic model (`apps/law_monitoring/service/src/service/models.py:83`). You can emit it as actual `LegalAct` instances, or simply return dicts that Pydantic can coerce.
- Maintain a stable `expression_url`: the discovery worker hashes it to create `law_id`, and the summary worker later dereferences it to fetch full text. If your source doesn’t expose a resolvable HTML page, provide an internal URL that your own fetcher can serve, or plan to store the text immediately (see below).

**Add Providers Instead Of Rewriting Discovery**
- Create a thin “provider” interface that mirrors `eur_lex_service.get_legal_acts_by_date_range(start, end, limit)` but can be backed by anything (REST, file dump, etc.). Keep it in a new module so existing code stays untouched.
- In `DiscoveryWorker._do_work` (`apps/law_monitoring/service/src/service/law_core/background_work/discovery_worker.py:44`), after the Eur-Lex query, iterate over an injected list of provider functions and call `legalact_to_law` on whatever comes back.
- Gate providers via config/env so you can enable/disable without code edits; pass them into the worker at construction (constructor already pulls settings, so adding one optional dependency is a tiny change).

**Supplying The Full Text**
- If your new source gives an HTML page, set `expression_url` to that page—`SummaryWorker` will use the existing `VisitWebpageUserAgentTool` to extract it.
- If you can’t expose HTML, provide the text yourself: extend `LegalAct` with an optional `raw_text` (or use a side-channel) and short-circuit `SummaryWorker` to skip fetching when that field is present, storing it directly via `laws_dao.mark_processed`. That’s one guarded branch instead of a rewrite.
- PDF-only feeds aren’t supported today; you’d need your provider to convert PDFs to text before handing them to the pipeline.

**Let The Rest Of The Pipeline Run Unchanged**
- Once your provider saves rows through `legalact_to_law`, the summary worker, `LawReportService`, LLM extractions, and reporting all work as they do now, because they read from the database and only rely on the `LegalAct` schema and the stored full text.
- Background metrics, reconciliation, and UI dashboards stay in sync automatically since they go through the same tables.

**Practical Steps**
1. Define a `LegalActProvider` protocol returning `Iterable[LegalAct]`.
2. Implement adapters for each new source (API client, file reader, etc.).
3. Modify `DiscoveryWorker` to accept a list of providers and call them after Eur-Lex.
4. Ensure each `LegalAct` has a reachable `expression_url` or provide pre-fetched `law_text`.
5. Configure providers via settings so they can be toggled per environment.

