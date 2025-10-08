# Law Monitoring Metrics

This document provides comprehensive information about all metrics exposed by the Law Monitoring service, including PromQL queries for Grafana dashboards.

## Metrics Categories

### 1. User Activity Metrics
```promql
# Last seen timestamp per user
usecase_user_last_seen_timestamp_seconds

# HTTP requests per user and endpoint
usecase_user_endpoint_requests_total
```

### 2. Reconciliation Metrics
```promql
# Current number of acts missing during reconciliation
acts_reconciliation_missing_current
```

### 3. Background Worker Metrics

#### Worker Execution Tracking
```promql
# Total worker runs by type and status
law_monitoring_worker_runs_total

# Worker run duration
law_monitoring_worker_run_duration_seconds

# Currently active workers
law_monitoring_worker_active_runs

# Last run timestamp by worker type
law_monitoring_worker_last_run_timestamp_seconds

# Total execution attempts
law_monitoring_worker_executions_total
```

#### Worker Performance Queries
```promql
# Average worker run duration by type
rate(law_monitoring_worker_run_duration_seconds_sum[5m]) / rate(law_monitoring_worker_run_duration_seconds_count[5m])

# Worker success rate
rate(law_monitoring_worker_runs_total{status="success"}[5m]) / rate(law_monitoring_worker_runs_total[5m])

# Active workers by type
law_monitoring_worker_active_runs
```

### 4. Law Discovery Metrics
```promql
# Laws found during discovery
law_monitoring_discovery_laws_found_total

# Laws successfully saved
law_monitoring_discovery_laws_saved_total

# Laws skipped (already exist)
law_monitoring_discovery_laws_skipped_total

# Laws failed to save
law_monitoring_discovery_laws_failed_total
```

#### Discovery Performance Queries
```promql
# Discovery success rate
rate(law_monitoring_discovery_laws_saved_total[5m]) / rate(law_monitoring_discovery_laws_found_total[5m])

# Discovery failure rate
rate(law_monitoring_discovery_laws_failed_total[5m]) / rate(law_monitoring_discovery_laws_found_total[5m])

# Laws discovered per hour
rate(law_monitoring_discovery_laws_found_total[1h]) * 3600
```

### 5. Law Processing Status Metrics
```promql
# Number of laws by processing status
law_monitoring_laws_by_status

# Number of laws by failure count
law_monitoring_laws_failure_count

# Laws processed by summary worker
law_monitoring_summary_laws_processed_total

# End-to-end law processing duration
law_monitoring_laws_processing_duration_seconds
```

#### Law Status Queries
```promql
# Total laws in system
sum(law_monitoring_laws_by_status)

# Processing success rate
rate(law_monitoring_laws_processing_duration_seconds_count{status="success"}[5m]) / 
rate(law_monitoring_laws_processing_duration_seconds_count[5m])

# Laws processed per hour
rate(law_monitoring_laws_processing_duration_seconds_count{status="success"}[1h]) * 3600

# Average processing time per law
rate(law_monitoring_laws_processing_duration_seconds_sum[5m]) / 
rate(law_monitoring_laws_processing_duration_seconds_count[5m])
```

### 6. Step-Level Processing Metrics
```promql
# Individual processing step durations
law_monitoring_step_duration_seconds
```

#### Step Performance Queries
```promql
# Average time per step
rate(law_monitoring_step_duration_seconds_sum[5m]) / rate(law_monitoring_step_duration_seconds_count[5m])

# Slowest processing steps
topk(5, rate(law_monitoring_step_duration_seconds_sum[5m]) by (step_name))

# Step failure rate
rate(law_monitoring_step_duration_seconds_count{status="error"}[5m]) / 
rate(law_monitoring_step_duration_seconds_count[5m])

# Steps executed per minute
rate(law_monitoring_step_duration_seconds_count[1m]) * 60
```

### 7. LLM Performance Metrics
```promql
# LLM call durations by purpose
law_monitoring_llm_call_duration_seconds
```

#### LLM Performance Queries
```promql
# Average LLM response time by purpose
rate(law_monitoring_llm_call_duration_seconds_sum[5m]) / rate(law_monitoring_llm_call_duration_seconds_count[5m])

# LLM calls per minute
rate(law_monitoring_llm_call_duration_seconds_count[1m]) * 60

# Slowest LLM operations
topk(3, rate(law_monitoring_llm_call_duration_seconds_sum[5m]) by (purpose))

# LLM call distribution by purpose
sum(rate(law_monitoring_llm_call_duration_seconds_count[5m])) by (purpose)
```

### 8. Web Scraping Performance Metrics
```promql
# Web scraping durations by success status
law_monitoring_web_scraping_duration_seconds
```

#### Web Scraping Queries
```promql
# Web scraping success rate
rate(law_monitoring_web_scraping_duration_seconds_count{success="true"}[5m]) / 
rate(law_monitoring_web_scraping_duration_seconds_count[5m])

# Average scraping time
rate(law_monitoring_web_scraping_duration_seconds_sum[5m]) / 
rate(law_monitoring_web_scraping_duration_seconds_count[5m])

# Failed scraping attempts per hour
rate(law_monitoring_web_scraping_duration_seconds_count{success="false"}[1h]) * 3600
```

## Complete Metrics Reference

| Metric Name | Type | Purpose | Labels |
|-------------|------|---------|--------|
| `usecase_user_last_seen_timestamp_seconds` | Gauge | User activity tracking | `user_id` |
| `usecase_user_endpoint_requests_total` | Counter | HTTP requests per user | `user_id`, `endpoint` |
| `acts_reconciliation_missing_current` | Gauge | Missing acts during reconciliation | - |
| `law_monitoring_worker_runs_total` | Counter | Worker execution counts | `worker_type`, `status` |
| `law_monitoring_worker_run_duration_seconds` | Histogram | Worker execution time | `worker_type`, `status` |
| `law_monitoring_worker_active_runs` | Gauge | Currently active workers | `worker_type` |
| `law_monitoring_worker_last_run_timestamp_seconds` | Gauge | Last worker execution time | `worker_type`, `status` |
| `law_monitoring_worker_executions_total` | Counter | Worker execution attempts | `worker_type`, `work_started`, `exit_reason` |
| `law_monitoring_laws_by_status` | Gauge | Laws by processing status | `status` |
| `law_monitoring_laws_processing_duration_seconds` | Histogram | End-to-end law processing time | `status` |
| `law_monitoring_laws_failure_count` | Gauge | Laws by failure count | `failure_count` |
| `law_monitoring_discovery_laws_found_total` | Counter | Laws found during discovery | - |
| `law_monitoring_discovery_laws_saved_total` | Counter | Laws successfully saved | - |
| `law_monitoring_discovery_laws_skipped_total` | Counter | Laws skipped (duplicates) | - |
| `law_monitoring_discovery_laws_failed_total` | Counter | Laws failed to save | - |
| `law_monitoring_summary_laws_processed_total` | Counter | Laws processed by summary worker | `status` |
| `law_monitoring_step_duration_seconds` | Histogram | Individual processing steps | `step_name`, `status` |
| `law_monitoring_llm_call_duration_seconds` | Histogram | LLM call performance | `purpose` |
| `law_monitoring_web_scraping_duration_seconds` | Histogram | Web scraping performance | `success` |

## Processing Steps Tracked

The `law_monitoring_step_duration_seconds` metric tracks these processing steps:

- `FETCH_LAW` - Web scraping from EUR-Lex
- `EXTRACT_HEADER` - Document metadata extraction  
- `EXTRACT_SUBJECT_MATTER` - Subject matter analysis
- `EXTRACT_TIMELINE` - Timeline and dates extraction
- `EXTRACT_ROLES_RESPONSIBILITIES_PENALTIES` - Compliance requirements
- `GENERATE_REPORT` - Final HTML report generation

## Common Dashboard Queries

### System Health Overview
```promql
# Overall system activity
sum(rate(usecase_user_endpoint_requests_total[5m]))

# Worker health
sum(law_monitoring_worker_active_runs) by (worker_type)

# Processing pipeline status
sum(law_monitoring_laws_by_status) by (status)
```

### Performance Monitoring
```promql
# Processing throughput
rate(law_monitoring_laws_processing_duration_seconds_count{status="success"}[5m])

# Average processing time
rate(law_monitoring_laws_processing_duration_seconds_sum[5m]) / 
rate(law_monitoring_laws_processing_duration_seconds_count[5m])

# Error rates
rate(law_monitoring_laws_processing_duration_seconds_count{status="error"}[5m])
```

### Resource Utilization
```promql
# LLM usage intensity
rate(law_monitoring_llm_call_duration_seconds_count[5m])

# Web scraping load
rate(law_monitoring_web_scraping_duration_seconds_count[5m])

# Step execution frequency
rate(law_monitoring_step_duration_seconds_count[5m]) by (step_name)
```

## Alerting Examples

### Critical Alerts
```promql
# No laws processed in 1 hour
rate(law_monitoring_laws_processing_duration_seconds_count{status="success"}[1h]) == 0

# High failure rate (>20%)
rate(law_monitoring_laws_processing_duration_seconds_count{status="error"}[5m]) / 
rate(law_monitoring_laws_processing_duration_seconds_count[5m]) > 0.2

# Worker not running
law_monitoring_worker_active_runs == 0
```

### Warning Alerts
```promql
# Processing time too slow (>30 minutes average)
rate(law_monitoring_laws_processing_duration_seconds_sum[5m]) / 
rate(law_monitoring_laws_processing_duration_seconds_count[5m]) > 1800

# Web scraping failures increasing
rate(law_monitoring_web_scraping_duration_seconds_count{success="false"}[5m]) > 0.1
```