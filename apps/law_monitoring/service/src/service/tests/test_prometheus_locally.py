#!/usr/bin/env python3
"""
Simple script to test and display law monitoring metrics in a readable format.
Use it to test the prometheus metrics endpoint locally. We can remove it later if unused.
Usage: uv run test_prometheus_locally.py [host:port]
"""

import sys
from typing import Dict, List

import requests


def fetch_metrics(url: str) -> Dict[str, List[str]]:
    """Fetch and parse metrics from the endpoint."""
    try:
        response = requests.get(f"{url}/metrics", timeout=10)
        response.raise_for_status()

        metrics: Dict[str, List[str]] = {
            "reconciliation": [],
            "worker": [],
            "discovery": [],
            "summary": [],
            "laws": [],
            "step_timing": [],
            "llm": [],
            "web_scraping": [],
            "general": [],
        }

        for line in response.text.split("\n"):
            line = line.strip()
            if line.startswith("#") or not line:
                continue

            if "acts_reconciliation_" in line:
                metrics["reconciliation"].append(line)
            elif "law_monitoring_worker_" in line:
                metrics["worker"].append(line)
            elif "law_monitoring_discovery_" in line:
                metrics["discovery"].append(line)
            elif "law_monitoring_summary_" in line:
                metrics["summary"].append(line)
            elif "law_monitoring_laws_" in line:
                metrics["laws"].append(line)
            elif "law_monitoring_step_duration_" in line:
                metrics["step_timing"].append(line)
            elif "law_monitoring_llm_call_" in line:
                metrics["llm"].append(line)
            elif "law_monitoring_web_scraping_" in line:
                metrics["web_scraping"].append(line)
            else:
                # Catch any other metrics (like usecase_ metrics)
                metrics["general"].append(line)

        return metrics
    except Exception as e:
        print(f"Error fetching metrics: {e}")
        return {}


def display_metrics(metrics: Dict[str, List[str]]) -> None:
    """Display metrics in a readable format."""

    print("🔄 RECONCILIATION METRICS")
    print("=" * 50)
    for metric in metrics.get("reconciliation", []):
        parts = metric.split()
        value = parts[-1]
        if "missing_current" in metric:
            print(f"  Acts missing during reconciliation: {value}")

    print("\n🔧 WORKER METRICS")
    print("=" * 50)
    for metric in metrics.get("worker", []):
        if "active_runs" in metric:
            parts = metric.split()
            value = parts[-1]
            if 'worker_type="' in metric:
                worker_type = metric.split('worker_type="')[1].split('"')[0]
                print(f"  Active {worker_type} workers: {value}")
        elif "runs_total" in metric and "_created" not in metric:
            parts = metric.split()
            value = parts[-1]
            if 'status="' in metric and 'worker_type="' in metric:
                status = metric.split('status="')[1].split('"')[0]
                worker_type = metric.split('worker_type="')[1].split('"')[0]
                print(f"  {worker_type.title()} runs ({status}): {value}")
        elif "executions_total" in metric and "_created" not in metric:
            parts = metric.split()
            value = parts[-1]
            if 'worker_type="' in metric:
                worker_type = metric.split('worker_type="')[1].split('"')[0]
                work_started = (
                    metric.split('work_started="')[1].split('"')[0]
                    if 'work_started="' in metric
                    else "unknown"
                )
                exit_reason = (
                    metric.split('exit_reason="')[1].split('"')[0]
                    if 'exit_reason="' in metric
                    else "unknown"
                )
                print(
                    f"  {worker_type.title()} executions (started: {work_started}, exit: {exit_reason}): {value}"
                )
        elif "last_run_timestamp" in metric and "_created" not in metric:
            parts = metric.split()
            value = parts[-1]
            if value != "0" and 'worker_type="' in metric:
                worker_type = metric.split('worker_type="')[1].split('"')[0]
                status = (
                    metric.split('status="')[1].split('"')[0]
                    if 'status="' in metric
                    else "unknown"
                )
                import datetime

                timestamp = datetime.datetime.fromtimestamp(float(value)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                print(f"  {worker_type.title()} last run ({status}): {timestamp}")

    print("\n📊 DISCOVERY METRICS")
    print("=" * 50)
    for metric in metrics.get("discovery", []):
        if "_created" not in metric:
            parts = metric.split()
            value = parts[-1]
            if "found_total" in metric:
                print(f"  Laws found: {value}")
            elif "saved_total" in metric:
                print(f"  Laws saved: {value}")
            elif "skipped_total" in metric:
                print(f"  Laws skipped: {value}")
            elif "failed_total" in metric:
                print(f"  Laws failed: {value}")

    print("\n🏭 SUMMARY PROCESSING METRICS")
    print("=" * 50)
    for metric in metrics.get("summary", []):
        if "_created" not in metric:
            parts = metric.split()
            value = parts[-1]
            if "status=" in metric:
                status = metric.split('status="')[1].split('"')[0]
                print(f"  Processed ({status}): {value}")

    print("\n📋 LAW STATUS METRICS")
    print("=" * 50)
    for metric in metrics.get("laws", []):
        if "_created" not in metric:
            parts = metric.split()
            value = parts[-1]
            if "by_status" in metric and "status=" in metric:
                status = metric.split('status="')[1].split('"')[0]
                print(f"  Laws in {status} status: {value}")
            elif "failure_count" in metric and "failure_count=" in metric:
                failure_count = metric.split('failure_count="')[1].split('"')[0]
                print(f"  Laws with {failure_count} failures: {value}")

    print("\n⏱️ STEP TIMING METRICS")
    print("=" * 50)
    step_metrics = {}
    for metric in metrics.get("step_timing", []):
        if (
            "_created" not in metric
            and "_bucket" not in metric
            and "_sum" not in metric
        ):
            parts = metric.split()
            value = parts[-1]
            if "step_name=" in metric:
                step_name = metric.split('step_name="')[1].split('"')[0]
                status = (
                    metric.split('status="')[1].split('"')[0]
                    if 'status="' in metric
                    else "all"
                )
                key = f"{step_name} ({status})"
                step_metrics[key] = value

    for step, count in step_metrics.items():
        print(f"  Step {step}: {count} calls")

    print("\n🤖 LLM CALL METRICS")
    print("=" * 50)
    llm_metrics = {}
    for metric in metrics.get("llm", []):
        if (
            "_created" not in metric
            and "_bucket" not in metric
            and "_sum" not in metric
        ):
            parts = metric.split()
            value = parts[-1]
            if "purpose=" in metric:
                purpose = metric.split('purpose="')[1].split('"')[0]
                llm_metrics[purpose] = value

    for purpose, count in llm_metrics.items():
        print(f"  LLM calls for {purpose}: {count}")

    print("\n🌐 WEB SCRAPING METRICS")
    print("=" * 50)
    for metric in metrics.get("web_scraping", []):
        if (
            "_created" not in metric
            and "_bucket" not in metric
            and "_sum" not in metric
        ):
            parts = metric.split()
            value = parts[-1]
            if "success=" in metric:
                success = metric.split('success="')[1].split('"')[0]
                print(f"  Web scraping ({success}): {value} calls")

    # Show general metrics if any
    general_metrics = metrics.get("general", [])
    if general_metrics:
        print("\n📈 GENERAL METRICS")
        print("=" * 50)
        for metric in general_metrics:
            if "_created" not in metric:
                parts = metric.split()
                value = parts[-1]
                metric_name = parts[0] if parts else "unknown"
                print(f"  {metric_name}: {value}")


def main() -> None:
    host_port = sys.argv[1] if len(sys.argv) > 1 else "localhost:8080"
    url = f"http://{host_port}"

    print(f"Fetching metrics from {url}/metrics...")
    print()

    metrics = fetch_metrics(url)
    if metrics:
        display_metrics(metrics)
        print("\n✅ Metrics endpoint is working correctly!")
        print(f"\nTo view all metrics: curl {url}/metrics")
        print(f"To test in Prometheus: add '{host_port}' as a target")
    else:
        print("❌ Failed to fetch metrics")
        sys.exit(1)


if __name__ == "__main__":
    main()
