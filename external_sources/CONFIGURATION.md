# BaFin Provider Deployment Notes

## Provider Import Path
- `external_sources.my_provider`

## Environment Variables
- `FIRECRAWL_API_KEY` (**required**): API key used to fetch HTML content through the Firecrawl gateway.
- `BAFIN_RSS_FEED_URLS` (**required**): Comma-separated list of BaFin RSS feed URLs to monitor (e.g. `https://www.bafin.de/SharedDocs/RSS_Feed/EN/Aufsicht/Banken/rss.xml`).
- `MY_PROVIDER_BASE_URL` (optional): Override the base URL used to generate `LegalAct.expression_url` values. Default `http://localhost:8000`.
- `MY_PROVIDER_CACHE_MAX_AGE_MINUTES` (optional): Cache TTL for downloaded data. Default `60`.
- `MY_PROVIDER_MAX_ITEMS` (optional): Maximum number of RSS items fetched per refresh. Default `25`.
- `MY_PROVIDER_FORCE_REFRESH` (optional): Set to `true` to force a refresh on every Python call (useful for debugging).

Ensure the same `MY_PROVIDER_BASE_URL` is used when running the FastAPI server so the provider module and HTTP responses stay aligned.

## Smoke Test Steps
1. Export `FIRECRAWL_API_KEY` and `BAFIN_RSS_FEED_URLS`.
2. Run the HTTP server: `uvicorn external_sources.http_server.app:app`.
3. Visit `http://localhost:8000/legal-acts?refresh=1` to trigger a fresh crawl and inspect the returned JSON.
4. Follow an `expression_url` from the JSON payload to confirm the HTML article contains the `data-law-monitoring="legal-act"` marker.

## Scheduling Guidance
- Cached responses refresh automatically once the TTL expires; align cron or worker schedules to avoid redundant crawls (e.g. every 30–60 minutes).
- Respect BaFin’s published guidance on RSS polling (avoid hitting the feeds more often than every 15 minutes).
