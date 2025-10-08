# Law Monitoring System - Prometheus & Grafana Setup

This document explains how to set up comprehensive monitoring for the law monitoring background workers using Prometheus and Grafana.

## Overview

The system now exposes detailed metrics about:
- **Worker Performance**: Run counts, durations, active runs, execution attempts
- **Discovery Metrics**: Laws found, saved, skipped, failed during discovery
- **Processing Metrics**: Summary worker success/failure rates
- **Law Status Tracking**: Current counts by processing status (raw, processing, processed, failed)
- **Failure Analysis**: Laws grouped by failure count

## Available Metrics

### Worker Metrics
- `law_monitoring_worker_runs_total` - Total worker runs by type and status
- `law_monitoring_worker_run_duration_seconds` - Worker run duration histogram
- `law_monitoring_worker_active_runs` - Currently active workers
- `law_monitoring_worker_last_run_timestamp_seconds` - Last run timestamp by worker and status
- `law_monitoring_worker_executions_total` - Worker execution attempts (including blocked runs)

### Law Processing Metrics
- `law_monitoring_laws_by_status` - Current law counts by status (raw, processing, processed, failed)
- `law_monitoring_laws_processing_duration_seconds` - Time spent processing individual laws
- `law_monitoring_laws_failure_count` - Laws grouped by failure count

### Discovery Worker Metrics
- `law_monitoring_discovery_laws_found_total` - Total laws found during discovery
- `law_monitoring_discovery_laws_saved_total` - Total laws successfully saved
- `law_monitoring_discovery_laws_skipped_total` - Total laws skipped (already exist)
- `law_monitoring_discovery_laws_failed_total` - Total laws failed to save

### Summary Worker Metrics
- `law_monitoring_summary_laws_processed_total` - Laws processed by summary worker with status labels:
  - `status="success"` - Successfully processed
  - `status="failed_retry"` - Failed but will retry
  - `status="failed_permanent"` - Failed permanently (moved to failed folder)

## Setup Instructions

### 1. Metrics are Already Enabled
The metrics endpoint is automatically available at `/metrics` when the service starts. No additional configuration needed.

### 2. Configure Prometheus

Add this job to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'law-monitoring'
    static_configs:
      - targets: ['localhost:8000']  # Adjust host:port as needed
    scrape_interval: 30s
    metrics_path: '/metrics'
```

### 3. Import Grafana Dashboard

1. Copy the contents of `grafana-dashboard-example.json`
2. In Grafana: Dashboards → Import → Paste JSON
3. Configure your Prometheus data source

The dashboard includes:
- Worker run status overview
- Active worker monitoring
- Law processing status pie chart
- Worker performance timeseries
- Discovery and summary worker metrics
- Failure analysis

### 4. Set Up Alerts

1. Copy the contents of `grafana-alerts-example.yaml`
2. In Grafana: Alerting → Alert Rules → Import
3. Configure notification channels (email, Slack, etc.)

## Key Alerts Configured

### Critical Alerts
- **WorkerHighFailureRate**: Worker failing >10% of runs
- **PermanentFailures**: >5 laws permanently failed in 1 hour
- **MetricsEndpointDown**: Service is not responding

### Warning Alerts
- **WorkerStuckProcessing**: Worker running >2 hours without completion
- **NoDiscoveryRuns**: Discovery worker hasn't run in >70 minutes
- **ProcessingBacklog**: >100 unprocessed laws waiting
- **HighFailureCountLaws**: >10 laws have failed 2+ times
- **DiscoveryFindingNoLaws**: No new laws discovered for 2+ hours
- **SlowLawProcessing**: 95th percentile processing time >30 minutes

## Useful Queries

### Worker Health
```promql
# Active workers by type
law_monitoring_worker_active_runs

# Worker success rate (last hour)
rate(law_monitoring_worker_runs_total{status="COMPLETED"}[1h]) / 
rate(law_monitoring_worker_runs_total[1h])

# Time since last successful run
time() - law_monitoring_worker_last_run_timestamp_seconds{status="COMPLETED"}
```

### Processing Pipeline Health
```promql
# Current processing queue size
law_monitoring_laws_by_status{status="raw"}

# Processing throughput (laws/hour)
rate(law_monitoring_summary_laws_processed_total{status="success"}[1h]) * 3600

# Discovery vs Processing rate comparison
rate(law_monitoring_discovery_laws_saved_total[1h]) / rate(law_monitoring_summary_laws_processed_total{status="success"}[1h])
```

### Failure Analysis
```promql
# Laws that have failed multiple times
sum by (failure_count) (law_monitoring_laws_failure_count)

# Failure rate by worker type
rate(law_monitoring_worker_runs_total{status="FAILED"}[1h])
```

## Troubleshooting

### High Failure Rates
1. Check logs for specific error messages
2. Look at `law_monitoring_laws_failure_count` to see which laws are failing repeatedly
3. Monitor `law_monitoring_summary_laws_processed_total{status="failed_permanent"}` for laws moved to failed folder

### Processing Backlog
1. Check if summary workers are running: `law_monitoring_worker_active_runs{worker_type="summary"}`
2. Monitor processing duration: `law_monitoring_laws_processing_duration_seconds`
3. Scale workers if needed or investigate performance issues

### Discovery Issues
1. Monitor EUR-Lex connectivity through discovery success rates
2. Check `law_monitoring_discovery_laws_failed_total` for save failures
3. Verify discovery worker scheduling with `law_monitoring_worker_last_run_timestamp_seconds{worker_type="discovery"}`

## File System Monitoring

The system tracks laws in three folders:
- `raw_law_data/` - Newly discovered laws (status: raw, processing)
- `processed_law_data/` - Successfully processed laws
- `failed_law_data/` - Laws that failed processing permanently

Current counts are reflected in the `law_monitoring_laws_by_status` metric, updated on each metrics scrape.