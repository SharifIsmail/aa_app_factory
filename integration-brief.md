# What I provide

- A Python module (or client) whose entry point returns an iterable of `LegalAct` (e.g. `list[LegalAct]`) objects with all metadata filled (`title`, `expression_url`, `publication_date`, dates, Eurovoc labels if available, `pdf_url`, etc.). Hashable `expression_url` is mandatory.
- An HTTP-accessible endpoint per act—`expression_url` must resolve to a page containing the cleaned text the summary worker can scrape (HTML/Markdown, no authentication). If that’s impossible for any act, bundle the already-cleaned text alongside the record and document which acts require skipping the fetch.
- A short configuration note: how to import your provider, any required environment variables or credentials, and sample `expression_url`/`pdf_url` values so that you can enable it via settings.

Based on that, the provider should just plug into discovery and the rest of the pipeline runs unchanged.

## Questions
* For the classification to work well, does the HTML in `expression_url` need to contain something in particular?
* I think in this case the app would not differentiate the source of the legal act? Can you handle that downstream, for example using the URL scheme, or do you want me to provide something else?

# Proposal what you roughly need to do

1. Wire our provider into the discovery pipeline. Treat it like another `LegalAct` source alongside Eur-Lex, guardable via config.
2. Save those acts through the existing `legalact_to_law` path so they land in the same tables/queues.
3. Adjust the summary worker only if an act arrives with pre-supplied text (skip the web fetch in that case); otherwise it keeps scraping `expression_url` as today.
4. Add whatever config toggle or metrics tag you need so the new source can be enabled and monitored per environment.

